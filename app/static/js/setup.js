// First-run wizard: welcome, engine, CV, five questions, building, best-fit roles.
import { h, icon, button, busyClick, api, toast, skeleton } from './core.js';
import { store, load, start, ACTIVE } from './store.js';
import { engineCards } from './settings.js';
import { dropZone } from './jobs.js';
import { positionsList } from './profile.js';
import { whoTag } from './today.js';

export const deps = ['state', 'engines', 'taskstatus', 'profile'];

const STEPS = ['Assistant', 'Your CV', 'Five questions', 'Building', 'Your roles'];
const ACCEPT = ['pdf', 'docx', 'doc', 'txt', 'md'];
const a = { loc: '', auth: '', km: '', arr: '', pay: '', cur: '', per: '', refuse: '', lack: '', gap: '' };
let step = null;
let cv = null;
let taskId = null;
let uploading = false;

function initialStep() {
  const s = store.state?.setup || {};
  const running = (store.tasks?.tasks || []).find((t) => t.kind === 'setup' && ACTIVE.includes(t.status));
  if (running) { taskId = running.id; return 4; }
  if (s.has_register && s.has_positions && !s.onboarded) return 5;
  return 0;
}

const to = (n) => () => {
  step = n;
  document.getElementById('main').replaceChildren(render());
  document.getElementById('step-title')?.focus();
};

export function render() {
  if (!store.state) return h('div.screen', skeleton(6));
  if (step == null) step = initialStep();
  if (step === 1 && !store.engines && !store.errors.engines) load('engines');
  if (step === 5 && !store.profile) load('profile');
  if (!cv && store.state.setup?.cv_files?.length) cv = store.state.setup.cv_files[0];

  const body = [welcome, engine, cvStep, questions, building, roles][step]();
  return h('div.screen.setup',
    step > 0 ? h('ol.wizard-steps', { 'aria-label': 'Setup steps' }, STEPS.map((label, i) =>
      h('li', { class: i + 1 < step ? 'is-done' : i + 1 === step ? 'is-now' : '', 'aria-current': i + 1 === step ? 'step' : null },
        h('span.num', String(i + 1)), h('span.ws-label', label)))) : null,
    body);
}

function head(title, lede) {
  return h('header.page-head', h('h1#step-title', { tabindex: '-1' }, title), lede ? h('p.lede', lede) : null);
}

function nav(back, next) {
  return h('div.wizard-nav', back != null ? h('button.btn.btn-quiet', { type: 'button', onclick: to(back) }, 'Back') : h('span'), next);
}

function welcome() {
  return h('div.wizard',
    head('Welcome to Candor', 'Candor finds jobs you are genuinely strong for, and writes a CV and cover letter for each one in which every claim is true.'),
    h('section.panel.teach',
      h('ol.steps-teach',
        h('li', h('strong', 'Pick an assistant.'), ' Candor uses Claude or ChatGPT (Codex) through your own subscription.'),
        h('li', h('strong', 'Give it your CV'), ' and answer five short questions.'),
        h('li', h('strong', 'Candor builds your profile'), ' (5-10 minutes): every fact it may ever use for you.'),
        h('li', h('strong', 'Choose the kinds of job'), ' you want, then search.'))),
    h('p.privacy-note', icon('lock'), h('span', 'Everything stays on this computer. Candor never sends an application or an email for you.')),
    h('div.wizard-nav', h('span'), button('Start', { kind: 'primary', ico: 'arrow', onclick: to(1) })));
}

function engine() {
  const e = store.engines;
  const ready = (e?.engines || []).some((x) => x.installed && x.signed_in);
  const missing = e && !ready;
  return h('div.wizard',
    head('Your assistant', 'Candor does its writing through Claude or Codex, using the subscription you already pay for. No API key, no extra bill.'),
    store.errors.engines ? h('p.inline-error', store.errors.engines) : engineCards(e),
    missing ? h('section.panel.howto', h('h2', 'Set one up first'),
      h('p', whoTag('You'), ' Do one of these, then press Check again.'),
      h('ol.plain-list',
        h('li', h('strong', 'Claude: '), 'install Claude Code from claude.com/code (or the Claude desktop app) and sign in with your Claude account.'),
        h('li', h('strong', 'Codex: '), 'install Codex from chatgpt.com/codex and sign in with your ChatGPT account.'))) : null,
    h('div.row-actions', h('button.btn.btn-quiet', { type: 'button', onclick: busyClick(() => load('engines')) }, icon('refresh'), h('span', 'Check again'))),
    nav(0, button('Next: your CV', { kind: 'primary', ico: 'arrow', onclick: to(2), disabled: !ready,
      reason: !e ? 'Checking what is installed…' : ready ? null : 'Set up Claude or Codex first' })));
}

function cvStep() {
  const name = h('span.drop-name', cv ? cv.split('/').pop() : 'No file chosen');
  const err = h('p.inline-error', { hidden: true, role: 'alert' });
  async function take(f) {
    err.hidden = true;
    const ext = f.name.split('.').pop().toLowerCase();
    if (!ACCEPT.includes(ext)) { err.textContent = 'Candor reads PDF, Word (.docx, .doc) and text files. Save your CV as one of those and try again.'; err.hidden = false; return; }
    if (f.size > 20 * 1024 * 1024) { err.textContent = 'That file is larger than 20 MB. Save a smaller copy and try again.'; err.hidden = false; return; }
    uploading = true; name.textContent = `Saving ${f.name}…`;
    try {
      const r = await api(`/api/upload?name=${encodeURIComponent(f.name)}`, { method: 'POST', raw: f });
      cv = r.path;
      to(2)();
    } catch (e) { err.textContent = e.message; err.hidden = false; name.textContent = 'No file chosen'; } finally { uploading = false; }
  }
  const input = h('input#cv-file.sr-only', { type: 'file', accept: ACCEPT.map((x) => '.' + x).join(','), onchange: (e) => e.target.files[0] && take(e.target.files[0]) });
  return h('div.wizard',
    head('Your CV', 'Your most recent CV. Candor reads it to learn what you have done, and never claims anything beyond it.'),
    dropZone(input, name, 'PDF, Word or text, up to 20 MB', take),
    err,
    cv ? h('p.saved-file', icon('check'), h('span', 'Saved: ', h('strong', cv.split('/').pop()))) : null,
    nav(1, button('Next: five questions', { kind: 'primary', ico: 'arrow', onclick: to(3), disabled: !cv || uploading, reason: cv ? null : 'Add your CV first' })));
}

const field = (key, label, attrs = {}) => h('label.field', h('span.label', label),
  h(attrs.rows ? 'textarea' : 'input', { id: `q-${key}`, value: a[key], ...attrs, oninput: (e) => { a[key] = e.target.value; } }));
const select = (key, label, opts) => h('label.field', h('span.label', label),
  h('select', { id: `q-${key}`, onchange: (e) => { a[key] = e.target.value; } },
    opts.map(([v, l]) => h('option', { value: v, selected: a[key] === v ? true : null }, l))));

function answers() {
  const loc = [a.loc && `location: ${a.loc}`, a.auth && `work authorization: ${a.auth}`, a.km && `max commute: ${a.km} km`, a.arr && `arrangement: ${a.arr}`].filter(Boolean).join('; ');
  const pay = a.pay ? `${a.pay} ${a.cur || ''} ${a.per || 'salary'}`.replace(/\s+/g, ' ').trim() : '';
  return [loc, pay, a.refuse.trim(), a.lack.trim(), a.gap.trim()];
}

function questions() {
  const q = (n, title, help, ...fields) => h('fieldset.question', h('legend', h('span.num.q-num', String(n)), h('span', title)),
    help ? h('p.muted', help) : null, h('div.q-fields', fields));
  const submit = busyClick(async (e) => {
    e.preventDefault();
    if (a.km && !(+a.km > 0)) { toast('The commute should be a number of kilometres, like 30.'); return; }
    const views = await start('/api/setup', { cv, answers: answers() });
    taskId = views[0]?.id ?? null;
    to(4)();
  });
  return h('form.wizard', { onsubmit: submit, novalidate: true },
    head('Five questions', 'Leave any blank to keep the default shown in grey. You can change all of this later.'),
    q(1, 'Where can you work?', null,
      field('loc', 'City, region and country', { placeholder: 'e.g. Winnipeg, Manitoba, Canada', autocomplete: 'address-level2' }),
      field('auth', 'Allowed to work there as', { placeholder: 'e.g. citizen, permanent resident, work permit' }),
      field('km', 'Longest commute (km)', { type: 'number', min: 1, inputmode: 'numeric', placeholder: '30' }),
      select('arr', 'Remote, hybrid or on site', [['', 'Any'], ['remote', 'Remote only'], ['hybrid', 'Hybrid or remote'], ['onsite', 'On site is fine']])),
    q(2, 'What is the lowest pay you would accept?', 'Jobs that clearly pay less are flagged for you to decide.',
      field('pay', 'Amount', { type: 'number', min: 0, inputmode: 'numeric', placeholder: 'none' }),
      field('cur', 'Currency', { placeholder: 'e.g. CAD', maxlength: 3 }),
      select('per', 'Per', [['', 'Year (salary)'], ['hourly', 'Hour']])),
    q(3, 'Any jobs, industries, shifts or travel you refuse?', 'Candor never suggests these.',
      field('refuse', 'I will not do', { rows: 2, placeholder: 'none' })),
    q(4, 'Any skills a job must not require, because you do not have them?', 'Jobs that insist on these are set aside.',
      field('lack', 'Skip jobs that require', { rows: 2, placeholder: 'none' })),
    q(5, 'Is there one gap in your CV that changes what may be claimed?', 'For example, a course you have not finished, or a tool you only used with help.',
      field('gap', 'The gap', { rows: 2, placeholder: 'unclaimed' })),
    nav(2, h('span.btn-wrap', h('button.btn.btn-primary', { type: 'submit' }, icon('arrow'), h('span', 'Build my profile')),
      h('span.reason', 'Takes 5-10 minutes'))));
}

function building() {
  const t = (store.tasks?.tasks || []).find((x) => x.id === taskId) || (store.tasks?.tasks || []).find((x) => x.kind === 'setup');
  const status = t?.status;
  if (status === 'done' && step === 4) {
    queueMicrotask(async () => { await Promise.all([load('profile'), load('state')]); if (step === 4) to(5)(); });
  }
  const failed = status === 'failed' || status === 'cancelled';
  return h('div.wizard',
    head('Building your profile', 'Candor is reading your CV and writing down every fact it may use for you, with where each one came from.'),
    h('section.panel.building', { class: failed ? 'is-failed' : '' },
      failed
        ? [h('p.inline-error', status === 'cancelled' ? 'Setup was cancelled.' : 'Setup stopped with a problem. The details are in the progress panel.'),
          h('div.row-actions', button('Try again', { kind: 'primary', onclick: to(3) }))]
        : [h('p.big-time', h('span.num', '5-10'), ' minutes'),
          h('p', status === 'question'
            ? 'Candor has a question for you. Answer it in the progress panel.'
            : 'You can leave this window open and do something else. Progress shows in the panel, and this page moves on by itself when it is done.'),
          t ? null : h('p.muted', 'Waiting for Candor to start…')]),
    h('p.privacy-note', icon('lock'), h('span', 'Your CV stays on this computer. Only your own assistant account reads it.')));
}

function roles() {
  const p = store.profile;
  const pos = p?.positions || [];
  const kept = pos.filter((x) => x.status !== 'dropped').length;
  return h('div.wizard',
    head('Your best-fit roles', 'From your CV, these are the kinds of job you are a strong candidate for, best fit first. Strike any you do not want.'),
    !p ? skeleton(5) : pos.length ? positionsList(pos) : h('p.empty-note', 'Candor did not save any roles. Use Ask Candor to ask what jobs fit your CV.'),
    nav(null, button('Find jobs', { kind: 'primary', ico: 'jobs', disabled: !kept, reason: kept ? 'Takes a few minutes' : 'Keep at least one role',
      onclick: busyClick(async () => {
        await start('/api/search', { top: store.state?.settings?.search_top || 5 });
        await load('state');
        step = null;
        location.hash = '#/jobs';
      }) })));
}
