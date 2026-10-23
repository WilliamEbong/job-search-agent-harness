// Jobs: the ranked league table with the 80 and 60 lines, batch prepare, and
// "apply to a posting you found".
import { h, icon, num, button, busyClick, plural, fmtDate, skeleton, api, toast } from './core.js';
import { store, start, blockedReason, queueNote } from './store.js';
import { panelHead } from './today.js';

export const deps = ['jobs', 'state'];
export const fresh = ['jobs'];

const selected = new Set();
const draft = { how: 'url', url: '', text: '', file: null };

const VERDICT = {
  'gate-fail': 'Set aside', qualified: 'Checked: worth applying',
  'not-drafted': 'Not drafted', 'not-resolved': 'Could not open',
};

function statusOf(r) {
  if (r.applied) return { label: 'Applied', cls: 'st-applied' };
  if (VERDICT[r.verdict]) return { label: VERDICT[r.verdict], cls: 'st-' + r.verdict };
  if (r.score >= 80) return { label: 'Strong fit', cls: 'st-strong' };
  if (r.score >= 60) return { label: 'Possible', cls: 'st-maybe' };
  return { label: 'Weak fit', cls: 'st-weak' };
}

const canPrepare = (r) => !r.applied && r.verdict !== 'gate-fail';

function ruleRow(cols, at, text) {
  return h('tr.threshold', { class: `t${at}` }, h('td', { colspan: cols },
    h('div.rule', h('span.rule-num.num', String(at)), h('span.rule-text', text))));
}

// Shared with Today's preview (compact: fewer columns, no actions).
// A threshold line is drawn only where the ranking actually crosses it, plus the 80
// line under a list that never drops below it, so no rule ever sits over nothing.
export function leagueTable(results, { compact = false, onPrepare } = {}) {
  const rows = [...results].sort((a, b) => (b.score ?? -1) - (a.score ?? -1) || a.number - b.number);
  const cols = compact ? 4 : 10;
  const head = compact
    ? ['#', 'Fit', 'Job', 'Status']
    : ['', '#', 'Fit', 'Job', 'Location', 'Board', 'Posted', 'Deadline', 'Status', ''];
  const body = h('tbody');
  let drew80 = false; let drew60 = false;
  for (const r of rows) {
    const sc = r.score ?? 0;
    if (!drew80 && sc < 80) { body.append(ruleRow(cols, 80, 'Strong fit above this line: Candor drafts these')); drew80 = true; }
    if (!drew60 && sc < 60) { body.append(ruleRow(cols, 60, 'Below 60: not worth drafting')); drew60 = true; }
    body.append(jobRow(r, compact, onPrepare));
  }
  if (!drew80 && rows.length) body.append(ruleRow(cols, 80, 'Strong fit above this line: Candor drafts these'));
  return h('div.table-wrap', { tabindex: compact ? null : '0', role: compact ? null : 'region', 'aria-label': compact ? null : 'Ranked jobs' },
    h('table.league', { class: compact ? 'is-compact' : '' },
      h('caption.sr-only', 'Jobs ranked by fit score, highest first. Lines at 80 and 60 show which ones Candor will draft.'),
      h('thead', h('tr', head.map((c, i) => h('th', { scope: 'col', class: `c${i}` },
        c || h('span.sr-only', i === 0 && !compact ? 'Select' : 'Actions'))))),
      body));
}

function jobRow(r, compact, onPrepare) {
  const st = statusOf(r);
  const gate = r.verdict === 'gate-fail';
  const job = h('div.job',
    h('span.job-title', r.title), h('span.job-co', r.company),
    !compact && r.location ? h('span.job-loc', r.location) : null,
    gate && r.rationale ? h('span.job-why', icon('warn'), `Set aside because: ${r.rationale}`)
      : r.rationale ? h('span.job-note', r.rationale) : null);
  const tier = (r.score ?? 0) >= 80 ? 'tier-a' : (r.score ?? 0) >= 60 ? 'tier-b' : 'tier-c';
  const cls = `${tier}${gate ? ' is-gate' : ''}${r.applied ? ' is-applied' : ''}`;
  const status = h('span.status', { class: st.cls }, st.label);
  if (compact) {
    return h('tr', { class: cls },
      h('th', { scope: 'row' }, num(r.number)), h('td.score', num(r.score)), h('td', job), h('td', status));
  }
  const id = `pick-${r.number}`;
  const box = canPrepare(r)
    ? h('input', { type: 'checkbox', id, checked: selected.has(r.number), 'aria-label': `Select ${r.title} at ${r.company}`,
      onchange: (e) => { e.target.checked ? selected.add(r.number) : selected.delete(r.number); updateBatch(); } })
    : null;
  return h('tr', { class: cls, 'data-n': r.number },
    h('td.c-pick', box),
    h('th.c-no', { scope: 'row' }, num(r.number)),
    h('td.score', num(r.score)),
    h('td.c-job', job),
    h('td.c-loc', r.location || '–'),
    h('td.c-board', r.board || '–'),
    h('td.c-date.c-posted', num(fmtDate(r.date) || '–')),
    h('td.c-date.c-deadline', { class: r.deadline ? '' : 'is-none' },
      r.deadline ? [h('span.cell-label', 'Closes '), num(fmtDate(r.deadline))] : h('span.muted', 'none given')),
    h('td.c-status', status),
    h('td.c-act',
      r.url ? h('a.post-link', { href: r.url, target: '_blank', rel: 'noopener noreferrer' },
        icon('external'), h('span', 'Open posting'), h('span.sr-only', ` for ${r.title} (opens in your browser)`)) : null,
      canPrepare(r) ? h('button.btn.btn-secondary.btn-sm', {
        type: 'button', disabled: !!blockedReason(), title: blockedReason() || null,
        onclick: busyClick(() => onPrepare([r.number])),
      }, h('span', 'Prepare'), h('span.sr-only', ` an application for ${r.title}`)) : null));
}

let batchBar = null;
function updateBatch() {
  if (!batchBar) return;
  const n = selected.size;
  const blocked = blockedReason();
  batchBar.replaceChildren(
    h('p.batch-text', n ? [num(n), ` selected. Candor prepares them one after another, about ${n * 10}-${n * 15} minutes in all.`]
      : 'Tick the jobs you want, or press Prepare on one row. Each takes Candor 10-15 minutes.'),
    button(n ? `Prepare ${plural(n, 'application')}` : 'Prepare applications', {
      kind: 'primary', disabled: !n || !!blocked, reason: blocked || (n ? queueNote() : null),
      onclick: busyClick(() => prepare([...selected])),
    }));
}

async function prepare(numbers) {
  const body = numbers.length === 1 ? { number: numbers[0] } : { numbers };
  await start('/api/apply', body);
  numbers.forEach((n) => selected.delete(n));
  updateBatch();
}

export function render() {
  const j = store.jobs;
  const blocked = blockedReason();
  const top = store.state?.settings?.search_top || 5;
  const find = button('Find jobs', { kind: j?.search ? 'secondary' : 'primary', ico: 'refresh', disabled: !!blocked,
    reason: blocked || queueNote(), onclick: busyClick(() => start('/api/search', { top })) });

  if (!j) {
    return h('div.screen', h('header.page-head', h('h1', 'Jobs')),
      store.errors.jobs ? h('p.inline-error', store.errors.jobs) : skeleton(8));
  }
  const s = j.search;
  const head = h('header.page-head.with-action',
    h('div', h('h1', 'Jobs'),
      s ? h('p.lede', `Last searched ${fmtDate(s.date, { day: 'numeric', month: 'long' })} near ${s.home || 'home'}, for `,
        h('span', (s.positions || []).join(', ') || 'your roles'), '.')
        : h('p.lede', 'Candor searches the job boards for the roles on your Profile, then ranks every job by fit.')),
    find);

  let table;
  if (!s || !(s.results || []).length) {
    table = h('section.panel.empty', { 'aria-labelledby': 'jobs-empty' },
      h('h2#jobs-empty', s ? 'The last search found nothing' : 'No search yet'),
      h('p', s ? 'Try again in a few days, or add more roles on your Profile so Candor looks wider.'
        : 'Press Find jobs. Candor checks the job boards for the roles on your Profile (a few minutes), then ranks what it finds here. A line at 80 marks the jobs worth a tailored application.'),
      h('p.muted', 'Searching only reads public job boards. Nothing about you is sent to them.'));
  } else {
    batchBar = h('div.batch-bar', { role: 'group', 'aria-label': 'Prepare several applications' });
    updateBatch();
    table = h('section.panel', { 'aria-labelledby': 'rank-title' },
      panelHead('rank-title', 'Ranked by fit', s.results.length),
      leagueTable(s.results, { onPrepare: prepare }),
      batchBar);
  }

  return h('div.screen.jobs', head, table, postingPanel(blocked), historyPanel(j.history || []));
}

function postingPanel(blocked) {
  const opt = (value, label) => h('label.seg', h('input', { type: 'radio', name: 'how', value, checked: draft.how === value,
    onchange: () => { draft.how = value; swap(); } }), h('span', label));
  const slot = h('div.posting-slot');
  const err = h('p.inline-error', { hidden: true, role: 'alert' });

  function swap() {
    err.hidden = true;
    if (draft.how === 'url') {
      slot.replaceChildren(h('label.field', h('span.label', 'Link to the job posting'),
        h('input#post-url', { type: 'url', placeholder: 'https://…', value: draft.url, oninput: (e) => { draft.url = e.target.value; } })));
    } else if (draft.how === 'text') {
      slot.replaceChildren(h('label.field', h('span.label', 'Paste the whole posting'),
        h('textarea#post-text', { rows: 7, value: draft.text, oninput: (e) => { draft.text = e.target.value; } })));
    } else {
      const name = h('span.drop-name', draft.file ? draft.file.name : 'No file chosen');
      const input = h('input#post-file.sr-only', { type: 'file', accept: '.pdf,.png,.jpg,.jpeg,.txt,.md,.docx,.doc',
        onchange: (e) => { draft.file = e.target.files[0] || null; name.textContent = draft.file?.name || 'No file chosen'; } });
      slot.replaceChildren(dropZone(input, name, 'A PDF or a screenshot of the posting', (f) => { draft.file = f; name.textContent = f.name; }));
    }
  }
  swap();

  const submit = async (e) => {
    e.preventDefault();
    err.hidden = true;
    let body;
    if (draft.how === 'url') {
      if (!/^https?:\/\/\S+\.\S+/.test(draft.url.trim())) { err.textContent = 'That does not look like a link. It should start with https://'; err.hidden = false; return; }
      body = { url: draft.url.trim() };
    } else if (draft.how === 'text') {
      if (draft.text.trim().length < 80) { err.textContent = 'Paste the whole posting, including the duties and requirements.'; err.hidden = false; return; }
      body = { text: draft.text.trim() };
    } else {
      if (!draft.file) { err.textContent = 'Choose a file first.'; err.hidden = false; return; }
      const up = await api(`/api/upload?name=${encodeURIComponent(draft.file.name)}&to=posting`, { method: 'POST', raw: draft.file });
      body = { file: up.path };
    }
    await start('/api/apply', body);
    Object.assign(draft, { url: '', text: '', file: null });
    swap();
    toast('Added. Candor will read the posting and check it against your profile first.', 'ok');
  };

  return h('section.panel', { 'aria-labelledby': 'own-title' },
    panelHead('own-title', 'Apply to a posting you found', null),
    h('p.panel-intro', 'Found a job somewhere else? Give Candor the posting. It checks the posting against your limits and your profile before writing anything.'),
    h('form.posting-form', { onsubmit: busyClick(submit), novalidate: true },
      h('fieldset.segs', h('legend.label', 'How do you have it?'), opt('url', 'A link'), opt('text', 'The text'), opt('file', 'A file')),
      slot, err,
      h('div.row-actions', button('Prepare application', { kind: 'secondary', type: 'submit', ico: 'arrow', disabled: !!blocked, reason: blocked || queueNote() }),
        h('p.muted.small', 'About 10-15 minutes. You will read it before anything is sent, and you send it yourself.'))));
}

export function dropZone(input, nameEl, hint, onFile) {
  const zone = h('label.drop', { for: input.id,
    ondragover: (e) => { e.preventDefault(); zone.classList.add('is-over'); },
    ondragleave: () => zone.classList.remove('is-over'),
    ondrop: (e) => { e.preventDefault(); zone.classList.remove('is-over'); const f = e.dataTransfer.files[0]; if (f) onFile(f); },
  }, icon('upload'), h('span.drop-main', 'Drop the file here or ', h('span.link', 'choose a file')), h('span.drop-hint', hint), nameEl);
  return h('div.drop-wrap', input, zone);
}

function historyPanel(rows) {
  if (!rows.length) return null;
  return h('details.panel.history',
    h('summary', h('span.summary-title', 'Everything Candor has checked before'), h('span.tab-count', num(rows.length)), icon('down')),
    h('div.table-wrap', { tabindex: '0', role: 'region', 'aria-label': 'Shortlist history' },
      h('table.plain',
        h('thead', h('tr', ['Date', 'Company', 'Role', 'Location', 'Fit', 'Result', 'Why'].map((c) => h('th', { scope: 'col' }, c)))),
        h('tbody', rows.map((r) => h('tr', { class: r.verdict === 'gate-fail' ? 'is-gate' : '' },
          h('td', num(fmtDate(r.date) || '–')), h('th', { scope: 'row' }, r.company), h('td', r.role), h('td', r.location),
          h('td.score', num(r.score)), h('td', h('span.status', { class: 'st-' + r.verdict }, VERDICT[r.verdict] || r.verdict || '–')),
          h('td.why', r.rationale || '')))))));
}
