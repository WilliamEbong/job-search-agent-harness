// Profile: what the evidence register lets Candor claim, best-fit roles, preferences.
import { h, icon, num, button, busyClick, post, skeleton, toast } from './core.js';
import { store, load, start, blockedReason, queueNote } from './store.js';
import { panelHead } from './today.js';

export const deps = ['profile', 'state'];
export const fresh = ['profile'];

let factDraft = '';

const ym = (s) => {
  if (!s) return '';
  if (s === 'present') return 'now';
  const [y, m] = s.split('-');
  return m ? new Date(+y, +m - 1, 1).toLocaleDateString(undefined, { month: 'short', year: 'numeric' }) : y;
};

export function positionsList(positions, { onToggle } = {}) {
  return h('ol.positions', positions.map((p) => {
    const dropped = p.status === 'dropped';
    return h('li', { class: dropped ? 'is-dropped' : '' },
      h('span.pos-fit.num', { 'aria-label': `Fit ${p.fit}` }, String(p.fit ?? '–')),
      h('div.pos-text',
        h('p.pos-title', dropped ? h('s', p.title) : p.title, h('span.pos-tier', p.tier)),
        p.because ? h('p.pos-why', p.because) : null,
        p.gap && p.gap !== 'none' ? h('p.pos-gap', h('strong', 'Gap: '), p.gap) : null),
      h('button.btn.btn-sm', {
        type: 'button', class: dropped ? 'btn-secondary' : 'btn-quiet',
        onclick: busyClick(async () => {
          await post('/api/positions', { rank: p.rank, status: dropped ? 'active' : 'dropped' });
          await (onToggle ? onToggle() : load('profile'));
        }),
      }, icon(dropped ? 'restore' : 'strike'), h('span', dropped ? 'Restore' : 'Strike'), h('span.sr-only', ` ${p.title}`)));
  }));
}

export function render() {
  const p = store.profile;
  if (!p) {
    return h('div.screen', h('header.page-head', h('h1', 'Profile')),
      store.errors.profile ? h('p.inline-error', store.errors.profile) : skeleton(8));
  }
  const r = p.register;
  if (!r) {
    return h('div.screen', h('header.page-head', h('h1', 'Profile')),
      h('section.panel.empty', h('h2', 'Your profile is not built yet'),
        h('p', 'Candor builds your profile from your CV during setup. It lists every fact Candor may use in an application, so nothing is ever made up.'),
        h('a.btn.btn-primary', { href: '#/setup' }, icon('arrow'), h('span', 'Start setup'))));
  }
  const blocked = blockedReason();
  const emp = r.employers || [];
  const pos = p.positions || [];
  const pref = p.preferences || {};

  const factForm = h('form.fact-form', { onsubmit: busyClick(async (e) => {
    e.preventDefault();
    const ta = document.getElementById('fact-text');
    const text = ta.value.trim();
    if (!text) { ta.focus(); return; }
    await start('/api/fact', { text });
    factDraft = ''; ta.value = '';
    toast('Sent to Candor. It will ask for proof if it needs any, then update your profile.', 'ok');
  }) },
  h('label.field', h('span.label', 'What should Candor know?'),
    h('textarea#fact-text', { rows: 3, value: factDraft, placeholder: 'For example: I finished the Google Data Analytics certificate in May 2026.', oninput: (e) => { factDraft = e.target.value; } })),
  h('div.row-actions', button('Add to my profile', { kind: 'secondary', type: 'submit', ico: 'check', disabled: !!blocked, reason: blocked || queueNote() })));

  return h('div.screen.profile',
    h('header.page-head', h('h1', r.owner || 'Profile'),
      h('p.lede', 'This is everything Candor may claim for you. Anything not here is blocked.'),
      h('p.contact', [r.location, r.email, r.phone].filter(Boolean).join(' · '))),

    h('div.profile-grid',
      h('section.panel', { 'aria-labelledby': 'emp-title' }, panelHead('emp-title', 'Work history', emp.length),
        emp.length ? h('ul.ledger', emp.map((e) => h('li', h('p.ledger-main', e.name),
          h('ul.titles', (e.titles || []).map((t) => h('li', h('span', t.title), h('span.num.dates', `${ym(t.start)} – ${ym(t.end)}`)))))))
          : h('p.empty-note', 'No employers recorded.')),

      h('section.panel', { 'aria-labelledby': 'edu-title' }, panelHead('edu-title', 'Education and credentials', (r.education || []).length + (r.credentials || []).length),
        h('ul.ledger', (r.education || []).map((e) => h('li', h('p.ledger-main', e.degree), h('p.muted', e.institution, e.status && e.status !== 'completed' ? h('span.flag', e.status) : null))),
          (r.credentials || []).map((c) => h('li', h('p.ledger-main', c.name,
            c.status === 'in-progress' || c.qualifier ? h('span.flag', c.qualifier || c.status) : null),
          c.status === 'in-progress' ? h('p.muted.small', 'Candor always says “in progress” for this one.') : null))))),

    h('section.panel', { 'aria-labelledby': 'tech-title' }, panelHead('tech-title', 'Tools and how far Candor may go', (r.technologies || []).length),
      h('p.panel-intro', 'Each tool can only be claimed up to its limit. “AI-assisted only” means Candor will never say you write it yourself.'),
      h('div.table-wrap', h('table.plain',
        h('thead', h('tr', h('th', { scope: 'col' }, 'Tool'), h('th', { scope: 'col' }, 'Most Candor may claim'))),
        h('tbody', (r.technologies || []).map((t) => h('tr', { class: /only|familiar/i.test(t.ceiling) ? 'is-limited' : '' },
          h('th', { scope: 'row' }, t.name), h('td', t.ceiling))))))),

    h('section.panel', { 'aria-labelledby': 'met-title' }, panelHead('met-title', 'Numbers you can back up', (r.metrics || []).length),
      (r.metrics || []).length
        ? h('ul.metrics', r.metrics.map((m) => h('li', h('span.metric-v.num', m.value), h('span', m.claim))))
        : h('p.empty-note', 'No numbers yet. Candor will not put any number in a CV unless it is listed here.')),

    h('section.panel', { 'aria-labelledby': 'pos-title' }, panelHead('pos-title', 'Best-fit roles', pos.filter((x) => x.status !== 'dropped').length),
      h('p.panel-intro', 'Candor searches for these roles. Strike any you do not want; you can restore them later.'),
      pos.length ? positionsList(pos) : h('p.empty-note', 'No roles yet. Setup suggests them from your CV.')),

    h('section.panel', { 'aria-labelledby': 'pref-title' }, panelHead('pref-title', 'Your limits', null),
      h('dl.prefs',
        pair('Home', pref.home), pair('Longest commute', pref.commute_km != null ? `${pref.commute_km} km` : ''),
        pair('Ways of working', (pref.arrangements || []).join(', ')), pair('Lowest pay', pref.minimum_pay || 'not set'),
        pair('Never suggest', (pref.exclusions || []).join(', ') || 'nothing'),
        pair('Skip jobs that need', (pref.hard_skips || []).join(', ') || 'nothing'),
        pair('CV length', pref.cv_pages ? `${pref.cv_pages} pages` : ''))),

    h('section.panel', { 'aria-labelledby': 'fact-title' }, panelHead('fact-title', 'Add or correct a fact', null),
      h('p.panel-intro', 'Finished a course, got a licence, or spotted a mistake? Tell Candor in plain words.'), factForm),
    h('p.muted.small', `Candor's record holds ${r.entries ?? 'several'} facts, each tied to where it came from.`));
}

const pair = (k, v) => [h('dt', k), h('dd', v || '–')];
