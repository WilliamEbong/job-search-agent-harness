// Today: one sentence, one primary action, the rest numbered, recent activity.
import { h, icon, num, button, busyClick, plural, ago, skeleton, fmtDate } from './core.js';
import { store, start, blockedReason, queueNote } from './store.js';
import { leagueTable } from './jobs.js';

export const deps = ['state', 'history', 'jobs'];

const goto = (hash) => () => { location.hash = hash; };

export function actions(t) {
  const list = [];
  for (const d of t.drafted || []) {
    list.push({ title: `Read and send ${d.company}`, detail: `${d.role}. Your CV and letter are checked and ready. Read them, then send them yourself.`,
      who: 'You', time: '10-15 min', label: 'Open the package', ico: 'applications', onclick: goto('#/applications') });
  }
  for (const f of t.followups || []) {
    list.push({ title: `Draft a follow-up to ${f.company}`, detail: `${f.role}. No reply for ${plural(f.days_quiet, 'day')}. Candor drafts a short, polite email; you send it.`,
      who: 'Candor, then you', time: 'about 5 min', label: 'Draft a follow-up', agent: true,
      onclick: busyClick(() => start('/api/followup', { company: f.company, role: f.role })) });
  }
  for (const i of t.interviews || []) {
    list.push({ title: `Get ready for your ${i.company} interview`, detail: `${i.role}. Likely questions and answers built only from your real experience.`,
      who: 'Candor, then you', time: '5-10 min', label: 'Prep me', agent: true,
      onclick: busyClick(() => start('/api/interview', { company: i.company, role: i.role })) });
  }
  for (const d of t.deadlines || []) {
    list.push({ title: `Prepare an application for ${d.company}`, detail: `${d.role}. Closes in ${plural(d.closes_in, 'day')}.`,
      who: 'Candor', time: '10-15 min', label: 'Prepare application', agent: true,
      onclick: d.url ? busyClick(() => start('/api/apply', { url: d.url })) : goto('#/jobs') });
  }
  for (const u of t.undrafted || []) {
    if ((t.deadlines || []).some((d) => d.company === u.company && d.role === u.role)) continue;
    list.push({ title: `Prepare an application for ${u.company}`, detail: `${u.role}${u.score ? `. Fit ${u.score}` : ''}. It passed every check and has no package yet.`,
      who: 'Candor', time: '10-15 min', label: 'Prepare application', agent: true,
      onclick: u.url ? busyClick(() => start('/api/apply', { url: u.url })) : goto('#/jobs') });
  }
  if (t.search_age_days == null || t.search_age_days >= 7) {
    list.push({ title: 'Find jobs', detail: t.search_age_days == null
      ? 'Candor has not searched yet. It checks the job boards for your best-fit roles and ranks what it finds.'
      : `The last search was ${plural(t.search_age_days, 'day')} ago. New postings appear every day.`,
    who: 'Candor', time: 'a few minutes', label: 'Find jobs', agent: true,
    onclick: busyClick(async () => { await start('/api/search', { top: store.state?.settings?.search_top || 5 }); location.hash = '#/jobs'; }) });
  }
  if (t.needs_positions) {
    list.push({ title: 'Choose your best-fit roles', detail: 'Candor searches only for the roles you keep. Strike the ones you do not want.',
      who: 'You', time: '2 min', label: 'Open Profile', ico: 'profile', onclick: goto('#/profile') });
  }
  return list;
}

function statusSentence(t, c) {
  const parts = [];
  if (c.ready_to_send) parts.push(`${plural(c.ready_to_send, 'application')} ready for you to send`);
  if (c.applications_open) parts.push(`${plural(c.applications_open, 'application')} out and waiting`);
  if (t.interviews?.length) parts.push(plural(t.interviews.length, 'interview') + ' coming up');
  if (c.jobs_new) parts.push(`${plural(c.jobs_new, 'job')} from the last search to look at`);
  if (!parts.length) return 'Nothing is waiting on you right now.';
  const s = parts.join(', ');
  return s[0].toUpperCase() + s.slice(1) + '.';
}

export function render() {
  const s = store.state;
  if (!s) return h('div.screen', skeleton(6));
  const t = s.today || {};
  const c = s.counts || {};
  const date = new Date((t.date || new Date().toISOString().slice(0, 10)) + 'T12:00:00');
  const list = actions(t);
  const blocked = blockedReason();
  const note = queueNote();

  const head = h('header.page-head',
    h('h1', date.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })),
    h('p.lede', statusSentence(t, c)));

  let primary;
  if (!list.length) {
    primary = h('section.action-row.is-calm', { 'aria-label': 'Next action' },
      h('div.action-text', h('h2', 'You are up to date'),
        h('p', 'Nothing needs you today. Candor will list follow-ups and deadlines here as they come up. Searching again in a few days keeps the list fresh.')),
      button('Find jobs anyway', { kind: 'secondary', ico: 'jobs', disabled: !!blocked, reason: blocked,
        onclick: busyClick(() => start('/api/search', { top: s.settings?.search_top || 5 })) }));
  } else {
    const a = list[0];
    primary = h('section.action-row', { 'aria-labelledby': 'next-title' },
      h('span.action-num.num', { 'aria-hidden': 'true' }, '1'),
      h('div.action-text', h('h2#next-title', a.title), h('p', a.detail),
        h('p.who', whoTag(a.who), h('span.time', a.time))),
      button(a.label, { kind: 'primary', ico: a.ico || 'arrow', onclick: a.onclick,
        disabled: a.agent && !!blocked, reason: a.agent ? (blocked || note) : null }));
  }

  const rest = list.slice(1);
  const restPanel = rest.length ? h('section.panel', { 'aria-labelledby': 'more-title' },
    panelHead('more-title', 'Also today', rest.length),
    h('ol.action-list', rest.map((a, i) => h('li',
      h('span.action-num.num', { 'aria-hidden': 'true' }, String(i + 2)),
      h('div.action-text', h('h3', a.title), h('p', a.detail), h('p.who', whoTag(a.who), h('span.time', a.time))),
      button(a.label, { kind: 'secondary', small: true, onclick: a.onclick, disabled: a.agent && !!blocked,
        reason: a.agent && blocked ? blocked : null }))))) : null;

  const hist = store.tasks?.history || [];
  const activity = h('section.panel', { 'aria-labelledby': 'act-title' },
    panelHead('act-title', 'Recent activity', hist.length ? Math.min(hist.length, 6) : null),
    hist.length
      ? h('ul.activity', hist.slice(0, 6).map((r) => h('li',
        h('span.act-mark', { class: r.status === 'done' ? 'ok' : r.status === 'failed' ? 'bad' : '' }, icon(r.status === 'failed' ? 'warn' : 'check')),
        h('div', h('p.act-title', r.title, h('span.act-when', ago(r.at))), r.summary ? h('p.act-sum', r.summary) : null))))
      : h('p.empty-note', 'When Candor finishes something for you (a search, an application, a follow-up) it is listed here, newest first.'));

  const results = store.jobs?.search?.results || [];
  const preview = h('section.panel.today-league', { 'aria-labelledby': 'lg-title' },
    panelHead('lg-title', 'Best fits from the last search', results.length || null),
    results.length
      ? [leagueTable(results.slice(0, 8), { compact: true }),
        h('p.panel-foot', h('a.link', { href: '#/jobs' }, `All ${results.length} jobs`, icon('arrow')),
          store.jobs.search.date ? h('span.muted', ` Searched ${fmtDate(store.jobs.search.date)}`) : null)]
      : h('p.empty-note', 'After your first search, the jobs Candor found appear here, ranked by how well they fit you.'));

  const howto = t.total_applications ? null : h('section.panel.teach', { 'aria-labelledby': 'how-title' },
    panelHead('how-title', 'How Candor works', null),
    h('ol.steps-teach',
      h('li', h('strong', 'Candor finds jobs'), ' and ranks them by how well they fit your real experience.'),
      h('li', h('strong', 'You pick one.'), ' Candor writes a CV and cover letter for it in 10-15 minutes.'),
      h('li', h('strong', 'Every claim is checked'), ' against your profile. Anything Candor cannot back up is blocked.'),
      h('li', h('strong', 'You read it and send it yourself.'), ' Candor never sends anything.')));

  return h('div.screen.today',
    head, primary,
    h('div.today-grid', h('div.today-main', restPanel, howto, activity), preview));
}

export function whoTag(who) {
  const you = who.startsWith('You');
  return h('span.who-tag', { class: you ? 'is-you' : '' }, icon(you ? 'person' : 'spark'), you ? 'You do this' : who);
}

export function panelHead(id, title, count) {
  return h('header.panel-head', h('h2', { id }, title), count != null ? h('span.tab-count', num(count)) : null);
}
