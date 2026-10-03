# Setting up your job search assistant (first time, with Codex)

Plan for 30 to 60 minutes, most of it waiting while things install. You need a ChatGPT
account and your CV (PDF or Word).

1. **Install Codex.** Go to [chatgpt.com/codex](https://chatgpt.com/codex), download the
   app for your computer, open it, and sign in with your ChatGPT account.
2. **Make a folder.** In your Documents, create a new empty folder called **Job Search**.
3. **Open that folder in Codex.** If Codex asks whether to trust or allow access to the
   folder, say yes.
4. **Copy this whole message into the Codex chat and send it:**

   ```text
   Set up the Job Search Agent Harness in this folder. I'm not technical: do every step
   you can yourself, and tell me in plain words when I need to click or type something.

   1. Download https://github.com/WilliamEbong/job-search-agent-harness into this folder
      itself, not a subfolder. Use git if it is installed; otherwise download the ZIP and
      unpack it here.
   2. Run `python harness_setup.py --yes` here. If Python is missing, install it first.
   3. For anything the installer reports MISSING, install it with the command it prints,
      then run the installer again. Repeat until it says all required prerequisites are
      in place.
   4. If something needs my computer password or a window I must click, tell me exactly
      what to do. If a program you just installed is not found, tell me to restart Codex.
   5. When everything is ready, tell me to start a new chat in this folder and say
      "set me up".
   ```

5. **Approve as it works.** Codex will stop several times to ask permission to download
   or install something. Allow each one. Windows may also ask "Do you want to allow this
   app to make changes?": click Yes. You can leave it running.
6. **Start fresh.** When Codex says it's finished, start a **new chat** in the same
   Job Search folder. If it told you to restart Codex, close and reopen it first.
7. **Type: set me up.** It asks which ChatGPT plan you have and suggests the cheaper
   "lite" mode on most plans. Then it asks for your CV: tell it where the file is (for
   example "it's in Downloads, called My CV.pdf") or paste the text. Answer its few
   questions.
8. **When it asks about internet access** for job searches, pick **"approve each
   search"** if you're unsure.

## After that, just talk to it

- "find me jobs"
- "apply to this" plus a job link, or the number of a job from its list
- "I applied" once you've sent it
- "what should I do today?"

It never sends anything to an employer. Your finished CV and cover letter are saved in
**Job Search → documents → applications**. You read them and send them yourself.
