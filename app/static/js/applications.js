// Applications: the list with form-guide chips, and the detail pane with the PDFs.
import { h, icon, md, num, button, busyClick, post, fmtDate, fileUrl, skeleton, toast, plural, TOKEN } from './core.js';
import { store, load, start, blockedReason, queueNote } from './store.js';
import { panelHead, whoTag } from './today.js';

export const deps = ['apps', 'state', 'profile'];
export const fresh = ['apps'];

let selectedId = null;
let tab = 'cv';
let confirming = false;

const STAGES = {
  found: ['F', 'Found'], drafted: ['D', 'Drafted'], sent: ['S', 'Sent'], interview: ['I', 'Interview'],
  offer: ['O', 'Offer'], hired: ['H', 'Hired'], rejected: ['R', 'Rejected'],
  no_response: ['N', 'No response'], withdrawn: ['W', 'Withdrawn'], declined: ['X', 'Declined offer'],
};
const PATH = ['found', 'drafted', 'sent', 'interview', 'offer'];
const BAD = ['rejected', 'no_response', 'withdrawn', 'declined'];

const OUTCOMES = [
  ['', 'Choose what happened…'], ['interview_only', 'Interview'], ['interview_only|offer', 'Offer'],
  ['hired', 'Hired'], ['rejected', 'Rejected'], ['no_response', 'No response'],
  ['withdrawn', 'Withdrawn'], ['offer_declined', 'Declined offer'],
];

// The form guide: one square per stage reached, then empty squares for what could come next.
export function chips(stages, { full = false } = {}) {
  const ended = stages.some((s) => BAD.includes(s) || s === 'hired');
  const ahead = ended ? [] : PATH.filter((s) => !stages.includes(s)).slice(0, 5 - Math.min(stages.length, 5));
  const label = 'Progress: ' + stages.map((s) => STAGES[s]?.[1] || s).join(', ');
  return h('ol.chips', { 'aria-label': label, class: full ? 'is-full' : '' },
    stages.map((s) => h('li.chip', { class: `ch-${BAD.includes(s) ? 'bad' : s === 'hired' ? 'win' : ['interview', 'offer'].includes(s) ? 'up' : 'done'}`, title: STAGES[s]?.[1] || s },
      h('span', { 'aria-hidden': 'true' }, full ? (STAGES[s]?.[1] || s) : (STAGES[s]?.[0] || '?')))),
    ahead.map((s) => h('li.chip.ch-ahead', { title: `Not yet: ${STAGES[s][1]}`, 'aria-hidden': 'true' }, h('span', full ? STAGES[s][1] : ''))));
}

function numbered() {
  const apps = store.apps?.applications || [];
  // One stable number per application, from the server: order of first contact, oldest is 1.
  return apps.map((a) => ({ ...a, no: a.number }));
}

const ready = (a) => a.status === 'in_progress' && !a.submitted_date;

export function render() {
  if (!store.apps) {
    return h('div.screen', h('header.page-head', h('h1', 'Applications')),
      store.errors.apps ? h('p.inline-error', store.errors.apps) : skeleton(6));
  }
  const apps = numbered();
  const list = [...apps].reverse();
  if (!apps.length) {
    return h('div.screen', h('header.page-head', h('h1', 'Applications')),
      h('section.panel.empty', h('h2', 'No applications yet'),
        h('p', 'When Candor prepares an application, it appears here with its CV and cover letter to read. Pick a job on the Jobs screen and press Prepare.'),
        h('a.btn.btn-primary', { href: '#/jobs' }, icon('jobs'), h('span', 'Go to Jobs'))));
  }
  if (!selectedId || !apps.some((a) => a.id === selectedId)) selectedId = (list.find(ready) || list[0]).id;
  const sel = apps.find((a) => a.id === selectedId);

  const table = h('div.table-wrap', { tabindex: '0', role: 'region', 'aria-label': 'Applications' },
    h('table.apps',
      h('caption.sr-only', 'Your applications, newest first. Choose one to see its documents.'),
      h('thead', h('tr', ['No.', 'Application', 'Fit', 'Where it stands', 'Form', 'Quiet'].map((c, i) =>
        h('th', { scope: 'col', class: `a${i}` }, c)))),
      h('tbody', list.map((a) => h('tr', { class: `${a.id === selectedId ? 'is-sel' : ''}${ready(a) ? ' is-ready' : ''}${['rejected', 'withdrawn', 'no_response', 'offer_declined'].includes(a.status) ? ' is-closed' : ''}` },
        h('th', { scope: 'row' }, num(a.no)),
        h('td', h('button.row-pick', { type: 'button', 'aria-pressed': String(a.id === selectedId),
          onclick: () => { selectedId = a.id; confirming = false; tab = 'cv'; rerender(); document.getElementById('detail')?.focus(); } },
        h('span.job-title', a.company), h('span.job-co', a.role))),
        h('td.score', num(a.fit)),
        h('td', h('span.status', { class: ready(a) ? 'st-ready' : `st-${a.status}` }, a.status_label)),
        h('td', chips(a.stages || [])),
        h('td.quiet', a.submitted_date ? [num(a.days_quiet), h('span.unit', ' days')] : h('span.muted', '–')))))));

  return h('div.screen.apps-screen',
    h('header.page-head', h('h1', 'Applications'),
      h('p.lede', 'Everything Candor prepared for you. Read each one, send it yourself, then tell Candor what happened.')),
    h('section.panel', { 'aria-labelledby': 'apps-title' }, panelHead('apps-title', 'Your applications', apps.length), table,
      h('p.legend', 'Form: ', ['found', 'drafted', 'sent', 'interview', 'offer'].map((s) => h('span.legend-item', h('span.chip.mini', STAGES[s][0]), ' ', STAGES[s][1].toLowerCase())))),
    detail(sel));
}

function rerender() {
  const main = document.getElementById('main');
  main.replaceChildren(render());
}

function detail(a) {
  const blocked = blockedReason();
  const pdf = (kind) => (a.files || []).find((f) => f.kind === kind && f.ext === 'pdf');
  const docs = {
    cv: pdf('cv') || pdf('combined'),
    letter: pdf('letter'),
    posting: pdf('posting') || (a.files || []).find((f) => f.kind === 'posting'),
  };
  const tabs = [['cv', 'CV'], ['letter', 'Cover letter'], ['posting', 'Posting']];
  const tablist = h('div.tabs', { role: 'tablist', 'aria-label': 'Documents' }, tabs.map(([k, label]) =>
    h('button.tab', { type: 'button', role: 'tab', id: `tab-${k}`, 'aria-selected': String(tab === k), 'aria-controls': 'doc-view',
      tabindex: tab === k ? '0' : '-1', onclick: () => { tab = k; rerender(); document.getElementById(`tab-${k}`)?.focus(); },
      onkeydown: (e) => {
        const i = tabs.findIndex(([x]) => x === k);
        const n = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (n) { tab = tabs[(i + n + tabs.length) % tabs.length][0]; rerender(); document.getElementById(`tab-${tab}`)?.focus(); }
      } }, label)));
  const f = docs[tab];
  let view;
  if (!f) view = h('p.empty-note', tab === 'posting' ? 'Candor did not keep a copy of this posting.' : 'This document has not been made yet.');
  else if (f.ext === 'pdf') view = h('iframe.doc-frame', { src: fileUrl(f.path), title: `${tabs.find(([k]) => k === tab)[1]} for ${a.company}` });
  else {
    // Markdown postings render through the same safe text-only renderer as the run panel.
    const isMd = f.ext === 'md';
    view = h(isMd ? 'div.doc-text.doc-md' : 'pre.doc-text', 'Loading…');
    fetch(fileUrl(f.path), { headers: { 'X-Candor-Token': TOKEN } }).then((r) => (r.ok ? r.text() : Promise.reject()))
      .then((t) => { if (isMd) view.replaceChildren(md(t)); else view.textContent = t; }, () => { view.textContent = 'Candor could not open this file. Use Open folder to see it.'; });
  }

  const actions = [];
  if (ready(a)) {
    actions.push(confirming ? confirmBox(a) : button('I sent it', { kind: 'primary', ico: 'check', onclick: () => { confirming = true; rerender(); document.getElementById('confirm-yes')?.focus(); } }));
  }
  if (a.folder) actions.push(button('Open folder', { kind: 'secondary', ico: 'folder', onclick: busyClick(() => post('/api/open', { path: a.folder })) }));
  if (a.submitted_date) {
    actions.push(button('Draft a follow-up', { kind: 'secondary', ico: 'ask', disabled: !!blocked, reason: blocked,
      onclick: busyClick(() => start('/api/followup', { company: a.company, role: a.role })) }));
    actions.push(button('Prep me for the interview', { kind: 'secondary', ico: 'person', disabled: !!blocked, reason: blocked,
      onclick: busyClick(() => start('/api/interview', { company: a.company, role: a.role })) }));
  }
  const note = queueNote();

  const outcome = h('select#outcome', { onchange: busyClick(async (e) => {
    const [status] = e.target.value.split('|');
    if (!status) return;
    await post('/api/applications/status', { company: a.company, role: a.role, status });
    toast(`Saved: ${e.target.selectedOptions[0].textContent} for ${a.company}.`, 'ok');
    await load('apps'); load('state');
  }) }, OUTCOMES.map(([v, l]) => h('option', { value: v }, l)));

  const cvPages = store.profile?.preferences?.cv_pages || 2;
  const cells = [...Array.from({ length: cvPages }, (_, i) => ['CV', i + 1, !!docs.cv]), ['Letter', 1, !!docs.letter]];
  const capacity = h('div.capacity', { role: 'group', 'aria-label': 'Page budget and time' },
    h('div.cap-row',
      h('span.cap-label', 'Page budget'),
      h('ol.cap-bar', cells.map(([k, p, has]) => h('li', { class: `${k === 'CV' ? 'cap-cv' : 'cap-letter'}${has ? ' is-full' : ''}` },
        h('span', `${k} ${k === 'CV' ? p : ''}`.trim())))),
      h('span.cap-note', docs.cv || docs.letter ? `Checked to fit: CV ${plural(cvPages, 'page')}, letter 1 page` : 'Not built yet')),
    h('div.cap-row',
      h('span.cap-label', 'Your time'),
      h('div.cap-time', h('span.cap-seg.is-done', 'Candor: 10-15 min, done'), h('span.cap-seg', { class: ready(a) ? 'is-you' : 'is-done' }, ready(a) ? 'You: about 10-15 min to read and send' : 'You: sent')),
      null));

  return h('section.panel.detail#detail', { tabindex: '-1', 'aria-labelledby': 'detail-title' },
    h('header.panel-head', h('h2#detail-title', h('span.num.detail-no', `No. ${a.no}`), ` ${a.company}`), a.fit != null ? h('span.tab-count', h('span.sr-only', 'Fit '), num(a.fit)) : null),
    h('div.detail-top',
      h('div', h('p.detail-role', a.role, a.location ? h('span.muted', ` · ${a.location}`) : null),
        h('p.detail-status', h('span.status', { class: ready(a) ? 'st-ready' : `st-${a.status}` }, a.status_label),
          a.submitted_date ? h('span.muted', ` Sent ${fmtDate(a.submitted_date, { day: 'numeric', month: 'long' })}, quiet for ${plural(a.days_quiet, 'day')}.`) : null),
        a.rationale ? h('p.detail-why', a.rationale) : null),
      chips(a.stages || [], { full: true })),
    ready(a) ? h('p.you-do', whoTag('You'), ' Read both documents. If they are right, send them to the employer yourself, the way the posting asks. Then press “I sent it”.') : null,
    h('div.detail-actions', actions, note && a.submitted_date ? h('p.reason', note) : null),
    a.submitted_date ? h('label.field.outcome', h('span.label', 'Heard back? Tell Candor what happened'), outcome) : null,
    capacity,
    tablist,
    h('div.doc-view#doc-view', { role: 'tabpanel', 'aria-labelledby': `tab-${tab}` }, view));
}

function confirmBox(a) {
  return h('div.confirm', { role: 'group', 'aria-labelledby': 'confirm-q' },
    h('p#confirm-q', h('strong', 'Did you send it yourself?'), ' Candor never sends anything. Only confirm once you have sent this application to ', a.company, ' yourself.'),
    h('div.row-actions',
      h('button.btn.btn-primary#confirm-yes', { type: 'button', onclick: busyClick(async () => {
        await post('/api/applications/status', { company: a.company, role: a.role, status: 'in_progress', sent: true });
        confirming = false;
        toast(`Marked as sent: ${a.company}. Candor will remind you to follow up if they go quiet.`, 'ok');
        await load('apps'); load('state');
      }) }, icon('check'), h('span', 'Yes, I sent it')),
      h('button.btn.btn-quiet', { type: 'button', onclick: () => { confirming = false; rerender(); } }, 'Not yet')));
}
