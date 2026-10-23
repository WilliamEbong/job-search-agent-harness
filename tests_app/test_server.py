"""The app's server, data readers and task queue, without spending a subscription:
a stand-in script plays the engine CLI."""

import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from app import data, engines, server, tasks

FAKE_ENGINE = r'''
import json, sys
prompt = sys.stdin.read()
print(json.dumps({"type": "system", "subtype": "init", "session_id": "s-1"}))
if "PING" in prompt:
    print(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": "python harness/today.py"}},
        {"type": "text", "text": "Which city do you live in?"}]}}))
    print(json.dumps({"type": "result", "result": "Which city do you live in?", "is_error": False}))
else:
    print(json.dumps({"type": "result", "result": "Thanks, saved: " + prompt.strip(), "is_error": False}))
'''


def wait(task, seconds=20):
    end = time.time() + seconds
    while task.status in ("queued", "running") and time.time() < end:
        time.sleep(0.05)
    return task.status


class TempRoot(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / "documents" / "applications").mkdir(parents=True)

    def tearDown(self):
        self.dir.cleanup()


class Paths(TempRoot):
    def test_inside_confines_to_documents(self):
        (self.root / "documents" / "a.pdf").write_bytes(b"x")
        self.assertIsNotNone(data.inside(self.root, "documents/a.pdf"))
        for bad in ("documents/../preferences.yaml", "evidence/register.yaml", "", "/etc/passwd",
                    "documents/\x00a", "\\\\host\\share\\x.pdf", "C:/Windows/x.pdf"):
            self.assertIsNone(data.inside(self.root, bad), bad)

    def test_upload_names_are_cleaned_and_never_overwrite(self):
        first = data.save_upload(self.root, "../../My CV`$(x).pdf", b"1")
        second = data.save_upload(self.root, "My CV`$(x).pdf", b"2")
        self.assertEqual(first, "documents/cv/My CV(x).pdf")
        self.assertEqual(second, "documents/cv/My CV(x) (2).pdf")
        with self.assertRaises(ValueError):
            data.save_upload(self.root, "run.exe", b"x")


class Engines(unittest.TestCase):
    def test_codex_lines(self):
        events = [engines.parse("codex", json.dumps(line)) for line in (
            {"type": "thread.started", "thread_id": "t-9"},
            {"type": "item.started", "item": {"type": "command_execution",
             "command": "powershell.exe -Command 'python harness/fact_check.py cv/x.tex'"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Done."}},
            {"type": "turn.failed", "error": {"message": "usage limit reached"}})]
        self.assertEqual(events[0], [{"kind": "session", "text": "t-9"}])
        self.assertEqual(events[1][0]["text"], "Checking every claim against your evidence")
        self.assertEqual(events[2], [{"kind": "say", "text": "Done."}])
        self.assertEqual(events[3][0]["kind"], "error")
        self.assertEqual(engines.parse("codex", "not json"), [])

    def test_step_text_unwraps_powershell(self):
        self.assertEqual(engines.step_text(
            "\"C:\\powershell.exe\" -Command 'Get-Content state/x.json'"), "Reading your files")

    def test_resolution_prefers_codex_for_long_loops(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            both = {"claude": True, "codex": True}
            self.assertEqual(data.engine_for(root, "apply", both), "codex")
            self.assertEqual(data.engine_for(root, "ask", both), "claude")
            self.assertEqual(data.engine_for(root, "apply", {"claude": True}), "claude")
            self.assertIsNone(data.engine_for(root, "ask", {}))
            data.save_settings(root, {"engine": "claude"})
            self.assertEqual(data.engine_for(root, "apply", both), "claude")
            self.assertIsNone(data.engine_for(root, "apply", {"codex": True}))

    def test_no_api_key_reaches_the_engine(self):
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "k", "OPENAI_API_KEY": "k"}):
            env = engines.environment()
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("OPENAI_API_KEY", env)


class Prompts(unittest.TestCase):
    def test_posting_text_never_enters_the_prompt(self):
        prompt = tasks.build_prompt("apply", {"file": "documents/postings/pasted-1.md"})
        self.assertIn("documents/postings/pasted-1.md", prompt)
        self.assertIn("never submit".lower(), prompt.lower())
        self.assertIn(".claude/lite/apply.md", prompt)
        self.assertIn("apply-any", tasks.build_prompt("apply", {"number": 2}, "standard"))

    def test_url_pattern_rejects_shell_text(self):
        self.assertTrue(tasks.URL.fullmatch("https://jobs.example.com/a?id=4"))
        for bad in ("https://x.com/$(rm)", "javascript:alert(1)", "https://a.com/`x`", "ftp://a"):
            self.assertIsNone(tasks.URL.fullmatch(bad), bad)


class Queue(TempRoot):
    def test_question_reply_and_history(self):
        script = self.root / "fake.py"
        script.write_text(FAKE_ENGINE, encoding="utf-8")
        argv = lambda name, root, session="", network=False: [sys.executable, str(script)]
        runner = tasks.Runner(self.root)
        with mock.patch.object(engines, "argv", argv), \
                mock.patch.object(tasks, "build_prompt", lambda *a: "PING"):
            task = runner.submit(tasks.Task("ask", {"text": "hi"}, "claude"))
            self.assertEqual(wait(task), "question")
            self.assertEqual(task.session, "s-1")
            self.assertIn({"kind": "step", "text": "Reading today's list"},
                          [{k: e[k] for k in ("kind", "text")} for e in task.events])
            runner.answer(task.id, "Winnipeg")
            self.assertEqual(wait(task), "done")
        self.assertEqual(task.events[-1]["text"], "Thanks, saved: Winnipeg")
        history = data.history(self.root)
        self.assertEqual(history[0]["status"], "done")

    def test_cancel_queued(self):
        runner = tasks.Runner(self.root)
        with runner.lock:  # hold the worker so the task stays queued
            task = tasks.Task("ask", {"text": "x"}, "claude")
            runner.tasks[task.id] = task
            runner.queue.append(task)
        runner.cancel(task.id)
        self.assertEqual(task.status, "cancelled")


class Applications(TempRoot):
    def write_tracker(self, rows):
        header = "date,company,role,status,fit_rating,notes,source,submitted_date\n"
        (self.root / "job_search_tracker.csv").write_text(header + "".join(rows), encoding="utf-8")

    def test_rows_merge_and_label(self):
        self.write_tracker(["2026-08-04,Acme,Analyst,in_progress,82,,https://a,2026-08-04\n",
                            "2026-08-05,Acme,Analyst,in_progress,,drafted,,\n",
                            "2026-08-06,Beta,Clerk,in_progress,70,,,\n",
                            "2026-08-06,Gamma,Lead,rejected,60,,,2026-08-01\n"])
        apps = {a["company"]: a for a in data.applications(self.root)}
        self.assertEqual(apps["Acme"]["status_label"], "Sent, waiting")
        self.assertEqual(apps["Acme"]["fit"], 82)
        self.assertEqual(apps["Beta"]["status_label"], "Ready to send")
        self.assertEqual(apps["Gamma"]["stages"], ["found", "sent", "rejected"])

    def test_mark_sent(self):
        self.write_tracker(["2026-08-06,Beta,Clerk,in_progress,70,followed up 2026-08-20,,\n",
                            "2026-08-06,Beta,Senior Clerk,in_progress,70,,,\n"])
        data.mark(self.root, "Beta", "Clerk", "", sent=True)
        apps = {a["role"]: a for a in data.applications(self.root)}
        self.assertEqual(apps["Clerk"]["status_label"], "Sent, waiting")
        self.assertEqual(apps["Senior Clerk"]["status_label"], "Ready to send")  # exact match
        self.assertIn("followed up 2026-08-20; submitted",  # follow-up history kept
                      (self.root / "job_search_tracker.csv").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            data.mark(self.root, "Beta", "Clerk", "applied-ish", sent=False)
        with self.assertRaises(ValueError):
            data.mark(self.root, "Beta", "", "rejected", sent=False)


class Preferences(TempRoot):
    def test_strike_position_and_mode(self):
        (self.root / "preferences.yaml").write_text(
            "target_positions:\n  positions:\n  - {rank: 1, title: A, status: active}\n"
            "  - {rank: 2, title: B, status: active}\nusage:\n  plan: claude-pro\n  mode: lite\n",
            encoding="utf-8")
        data.set_position(self.root, 2, "dropped")
        self.assertEqual([p["status"] for p in data.profile(self.root)["positions"]],
                         ["active", "dropped"])
        self.assertEqual(data.save_settings(self.root, {"mode": "standard"})["mode"], "standard")
        self.assertIn("mode: focused", (self.root / "preferences.yaml").read_text())
        self.assertIn("plan: claude-pro", (self.root / "preferences.yaml").read_text())
        self.assertTrue((self.root / "preferences.yaml.bak").exists())

    def test_unreadable_preferences_are_never_overwritten(self):
        path = self.root / "preferences.yaml"
        path.write_text("location: [unclosed\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            data.save_settings(self.root, {"mode": "lite"})
        self.assertEqual(path.read_text(encoding="utf-8"), "location: [unclosed\n")

    def test_odd_positions_do_not_break_state(self):
        (self.root / "preferences.yaml").write_text("target_positions: [Analyst, Clerk]\n",
                                                    encoding="utf-8")
        self.assertFalse(data.setup_state(self.root)["has_positions"])
        self.assertEqual(data.profile(self.root)["positions"], [])


class Http(TempRoot):
    def setUp(self):
        super().setUp()
        self.server = server.create_server(self.root, 0)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()

    def call(self, path, token=True, host=None, body=None):
        headers = {"X-Candor-Token": self.server.token} if token else {}
        if host:
            headers["Host"] = host
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", headers=headers,
                                         data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read() or b"null")
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.loads(error.read() or b"null")

    def test_guards(self):
        self.assertEqual(self.call("/api/ping", token=False), (200, {"app": "candor"}))
        self.assertEqual(self.call("/api/state", token=False)[0], 403)
        self.assertEqual(self.call("/api/state", host="evil.example:80")[0], 403)
        self.assertEqual(self.call("/files/../preferences.yaml")[0], 404)
        self.assertEqual(self.call(f"/api/state?t={self.server.token}", token=False)[0], 403)
        (self.root / "documents" / "run.bat").write_text("echo hi", encoding="utf-8")
        self.assertEqual(self.call("/api/open", body={"path": "documents/run.bat"})[0], 400)

    def test_state_and_setup_gate(self):
        status, body = self.call("/api/state")
        self.assertEqual(status, 200)
        self.assertFalse(body["setup"]["onboarded"])
        status, body = self.call("/api/search", body={})
        self.assertEqual(status, 409)
        self.assertIn("setting up", body["error"])

    def test_index_carries_token(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/") as response:
            page = response.read().decode()
        self.assertIn(self.server.token, page)
        self.assertNotIn("__CANDOR_TOKEN__", page)


if __name__ == "__main__":
    unittest.main()
