// The docked panel that shows one assistant run: steps, messages, a reply box, Cancel.
// It is built once per task and then only appended to, so typing a reply survives polls.
import { api, post, h, icon, md, announce, toast, busyClick } from './core.js';
import { store, load, loadAll, ACTIVE, taskHooks } from './store.js';

const FINISHED = ['done', 'failed', 'cancelled'];
const STATUS = {
  queued: 'Waiting to start', running: 'Working', question: 'Needs your answer',
  cancelling: 'Stopping', done: 'Finished', failed: 'Stopped with a problem', cancelled: 'Cancelled',
};
const ENGINE = { claude: 'Claude', codex: 'Codex', script: 'Candor', '': 'Candor' };

const el = () => document.getElementById('runpanel');
let cur = null;        // { id, view, count, startedAt, endedAt, dom }
let minimised = false;
let batch = new Set(); // task ids seen active since the panel was last idle
let timer = null;
let lastStatus = {};

export function initRunPanel() {
  taskHooks.started = (views) => {
    for (const v of views) batch.add(v.id);
    if (!cur || FINISHED.includes(cur.view.status)) show(views[0]);
    minimised = false;
    layout();
    if (views.length > 1) announce(`${views.length} tasks queued. Candor runs them one after another.`);
    schedule(200);
  };
  schedule(0);
  setInterval(tick, 1000);
}

export const panelOpen = () => !!cur && !minimised;

function schedule(ms) {
  clearTimeout(timer);
  timer = setTimeout(poll, ms);
}

async function poll() {
  let anyActive = false;
  try {
    const before = JSON.stringify(store.tasks?.tasks?.map((t) => [t.id, t.status]) || []);
    await load('tasks');
    const tasks = store.tasks?.tasks || [];
    const active = tasks.filter((t) => ACTIVE.includes(t.status));
    anyActive = active.length > 0;
    active.forEach((t) => batch.add(t.id));

    // Something finished since last time: refresh everything it may have changed.
    let finishedNow = false;
    for (const t of tasks) {
      if (lastStatus[t.id] && !FINISHED.includes(lastStatus[t.id]) && FINISHED.includes(t.status)) finishedNow = true;
      lastStatus[t.id] = t.status;
    }
    if (finishedNow) loadAll('state', 'jobs', 'apps', 'profile');
    else if (before !== JSON.stringify(tasks.map((t) => [t.id, t.status]))) load('state');

    const pick = active.find((t) => t.status !== 'queued') || active[0];
    if (!cur && pick) show(pick);
    else if (cur && FINISHED.includes(cur.view.status) && pick && pick.id !== cur.id) {
      toast(`Finished: ${cur.view.title}. Now: ${pick.title}.`, 'ok');
      show(pick);
    }
    if (cur) await refreshCurrent();
    if (!anyActive && (!cur || FINISHED.includes(cur.view.status))) batch = new Set(cur ? [cur.id] : []);
  } catch (e) {
    // The poller keeps going; a toast would repeat every second.
    console.warn(e);
  }
  schedule(anyActive || (cur && !FINISHED.includes(cur.view.status)) ? 1000 : 15000);
}

async function refreshCurrent() {
  const id = cur.id;
  const v = await api(`/api/tasks/${id}?since=${cur.count}`);
  if (!cur || cur.id !== id) return;
  const prev = cur.view.status;
  cur.view = { ...cur.view, ...v, events: [...cur.view.events, ...(v.events || [])] };
  for (const ev of v.events || []) addEvent(ev);
  cur.count = v.count ?? cur.count + (v.events || []).length;
  if (!cur.startedAt && v.status !== 'queued') cur.startedAt = (cur.view.events[0]?.at * 1000) || Date.now();
  if (prev !== v.status) {
    if (FINISHED.includes(v.status)) cur.endedAt = Date.now();
    announce(`${cur.view.title}: ${STATUS[v.status] || v.status}.`);
    renderChrome();
  }
}

function show(view) {
  cur = { id: view.id, view: { ...view, events: [] }, count: 0, startedAt: null, endedAt: null, dom: {} };
  build();
  layout();
}

function layout() {
  const p = el();
  p.hidden = !cur;
  p.classList.toggle('is-min', minimised);
  document.getElementById('shell').classList.toggle('with-panel', !!cur && !minimised);
}

function close() {
  cur = null;
  minimised = false;
  layout();
  document.getElementById('main').focus();
}

function build() {
  const p = el();
  p.replaceChildren();
  const d = cur.dom;
  d.title = h('h2.rp-title#rp-title');
  d.status = h('span.rp-status');
  d.pos = h('span.rp-pos.num');
  d.meta = h('p.rp-meta');
  d.elapsed = h('span.num');
  d.minBtn = h('button.icon-btn', { type: 'button', onclick: () => { minimised = !minimised; layout(); renderChrome(); } });
  d.steps = h('ol.rp-steps', { 'aria-label': 'Progress' });
  d.talk = h('div.rp-talk');
  d.reply = h('div.rp-reply');
  d.actions = h('div.rp-actions');
  d.stepCount = 0;
  p.append(
    h('header.rp-head', h('div.rp-head-text', d.title, h('p.rp-line', d.status, d.pos)), d.minBtn),
    h('div.rp-body', d.meta, d.steps, d.talk, d.reply),
    d.actions,
  );
  p.setAttribute('aria-labelledby', 'rp-title');
  renderChrome();
}

function renderChrome() {
  if (!cur) return;
  const d = cur.dom;
  const v = cur.view;
  d.title.textContent = v.title || 'Working';
  d.status.textContent = STATUS[v.status] || v.status;
  el().dataset.status = v.status;
  const ids = [...batch].sort((a, b) => a - b);
  d.pos.textContent = ids.length > 1 && ids.includes(cur.id) ? `${ids.indexOf(cur.id) + 1} of ${ids.length}` : '';
  d.meta.replaceChildren(h('span', ENGINE[v.engine] ?? v.engine), h('span.sep', { 'aria-hidden': 'true' }, '·'), d.elapsed);
  tick();
  d.minBtn.replaceChildren(icon(minimised ? 'up' : 'down'));
  d.minBtn.setAttribute('aria-label', minimised ? 'Show progress panel' : 'Minimise progress panel');
  d.minBtn.setAttribute('aria-expanded', String(!minimised));

  // Reply box: a question always; a finished agent run may also be continued.
  const canReply = v.can_reply ?? (v.status === 'question');
  if (canReply && !d.reply.firstChild) {
    d.reply.append(replyForm(v.status === 'question'));
    const body = el().querySelector('.rp-body');
    if (body) body.scrollTop = body.scrollHeight;
  }
  if (!canReply) d.reply.replaceChildren();
  else d.reply.querySelector('.rp-reply-label').textContent =
    v.status === 'question' ? 'Your answer' : 'Anything to add? (optional)';

  const live = ACTIVE.includes(v.status);
  d.actions.replaceChildren(
    live
      ? h('button.btn.btn-on-dark', { type: 'button', disabled: v.status === 'cancelling', onclick: busyClick(async () => {
          const r = await post(`/api/tasks/${cur.id}/cancel`);
          cur.view.status = r.task?.status || 'cancelling';
          renderChrome();
          schedule(300);
        }) }, icon('close'), h('span', v.status === 'queued' ? 'Remove from queue' : 'Cancel'))
      : h('button.btn.btn-on-dark', { type: 'button', onclick: close }, icon('check'), h('span', 'Close')),
    v.status === 'running' ? h('p.rp-leave', 'You can keep using Candor or leave this window open and do something else.') : '',
  );
}

function tick() {
  if (!cur?.dom.elapsed) return;
  const start = cur.startedAt;
  const ms = start ? (cur.endedAt || Date.now()) - start : 0;
  const s = Math.max(0, Math.round(ms / 1000));
  cur.dom.elapsed.textContent = start ? `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}` : 'not started';
}

function addEvent(ev) {
  const d = cur.dom;
  const text = ev.text || '';
  if (ev.kind === 'step') {
    d.steps.querySelector('.is-now')?.classList.replace('is-now', 'is-done');
    d.stepCount += 1;
    d.steps.append(h('li.is-now', h('span.rp-step-mark', { 'aria-hidden': 'true' }), h('span', text)));
    announce(text);
  } else if (ev.kind === 'say') {
    d.talk.append(h('div.rp-say', h('p.rp-who', 'Candor'), md(text)));
  } else if (ev.kind === 'you') {
    d.talk.append(h('div.rp-you', h('p.rp-who', 'You'), md(text)));
  } else if (ev.kind === 'error') {
    d.steps.querySelector('.is-now')?.classList.replace('is-now', 'is-done');
    d.talk.append(h('div.rp-error', { role: 'alert' }, icon('warn'),
      h('div', h('p.rp-error-title', 'This run stopped'), md(text),
        h('p.rp-error-help', 'Nothing was sent to anyone. You can try again; if it keeps happening, open Settings and press “Check my computer”.'))));
  } else if (ev.kind === 'done') {
    d.steps.querySelector('.is-now')?.classList.replace('is-now', 'is-done');
    if (text) d.talk.append(h('p.rp-done', icon('check'), h('span', text)));
  } else if (text) {
    d.talk.append(h('p.rp-note', text));
  }
  const body = el().querySelector('.rp-body');
  if (body) body.scrollTop = body.scrollHeight;
}

function replyForm(isQuestion) {
  const ta = h('textarea#rp-reply-text', { rows: 3, required: true });
  const form = h('form.rp-form', {
    onsubmit: async (e) => {
      e.preventDefault();
      const text = ta.value.trim();
      if (!text) { ta.focus(); return; }
      const btn = form.querySelector('button');
      btn.disabled = true;
      try {
        const r = await post(`/api/tasks/${cur.id}/reply`, { text });
        ta.value = '';
        if (r.task) cur.view.status = r.task.status;
        cur.endedAt = null;
        renderChrome();
        schedule(200);
      } catch (err) { toast(err.message); } finally { btn.disabled = false; }
    },
  },
  h('label.field', { for: 'rp-reply-text' }, h('span.label.rp-reply-label', isQuestion ? 'Your answer' : 'Anything to add? (optional)')),
  ta,
  h('button.btn.btn-primary', { type: 'submit' }, icon('arrow'), h('span', 'Send to Candor')));
  return form;
}
