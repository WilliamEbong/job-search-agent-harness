// Candor shell: rail, routing, the Ask box, and the state poll.
import { h, icon, toast, num } from './js/core.js';
import { store, load, onChange, start, isBusy, blockedReason } from './js/store.js';
import { initRunPanel } from './js/runpanel.js';
import * as today from './js/today.js';
import * as jobs from './js/jobs.js';
import * as applications from './js/applications.js';
import * as profile from './js/profile.js';
import * as settings from './js/settings.js';
import * as setup from './js/setup.js';

const SCREENS = { today, jobs, applications, profile, settings, setup };
const NAV = [
  ['today', 'Today'], ['jobs', 'Jobs'], ['applications', 'Applications'],
  ['profile', 'Profile'], ['settings', 'Settings'],
];
const main = document.getElementById('main');
let route = null;

function currentRoute() {
  const name = (location.hash.match(/^#\/([a-z]+)/) || [])[1];
  return SCREENS[name] ? name : 'today';
}

function render({ keepScroll = false } = {}) {
  const screen = SCREENS[route];
  const focusId = document.activeElement?.id;
  const y = window.scrollY;
  main.replaceChildren(screen.render());
  if (keepScroll) {
    window.scrollTo(0, y);
    if (focusId && main.contains(document.getElementById(focusId))) document.getElementById(focusId).focus({ preventScroll: true });
  }
}

function go() {
  let next = currentRoute();
  // First run: send everything to the wizard until setup is done.
  if (store.state && !store.state.setup?.onboarded && next !== 'setup' && next !== 'settings') {
    location.replace('#/setup');
    return;
  }
  const changed = next !== route;
  route = next;
  document.body.dataset.route = route;
  const label = route === 'setup' ? 'Setup' : NAV.find(([k]) => k === route)?.[1];
  document.title = `${label} · Candor`;
  renderNav();
  (SCREENS[route].deps || []).forEach((k) => { if (!store.loaded[k] || SCREENS[route].fresh?.includes(k)) load(k); });
  render();
  if (changed) { window.scrollTo(0, 0); main.focus({ preventScroll: true }); }
  closeMenu();
}

function renderNav() {
  const c = store.state?.counts || {};
  const t = store.state?.today || {};
  const counts = {
    today: (t.drafted?.length || 0) + (t.followups?.length || 0) + (t.deadlines?.length || 0) + (t.interviews?.length || 0),
    jobs: c.jobs_new, applications: c.applications_open, profile: null, settings: null,
  };
  const nav = document.getElementById('nav');
  nav.replaceChildren(...NAV.map(([key, label]) => h('li', h('a', {
    href: `#/${key}`, 'aria-current': route === key ? 'page' : null,
  }, icon(key), h('span.nav-label', label),
  counts[key] ? h('span.badge', { 'aria-label': `${counts[key]} to look at` }, num(counts[key])) : null))));

  const busy = isBusy();
  const eng = store.state?.settings?.engine || 'auto';
  const engText = { auto: 'Engine: automatic', claude: 'Engine: Claude', codex: 'Engine: Codex' }[eng] || `Engine: ${eng}`;
  document.getElementById('engine-text').textContent = busy ? `${engText} · Working…` : engText;
  document.getElementById('engine-line').classList.toggle('is-busy', busy);
}

// Mobile menu
const menuBtn = document.getElementById('menu-btn');
const rail = document.getElementById('rail');
menuBtn.append(icon('menu'));
function closeMenu() {
  rail.classList.remove('is-open');
  menuBtn.setAttribute('aria-expanded', 'false');
}
menuBtn.addEventListener('click', () => {
  const open = !rail.classList.contains('is-open');
  rail.classList.toggle('is-open', open);
  menuBtn.setAttribute('aria-expanded', String(open));
  if (open) rail.querySelector('a')?.focus();
});
document.addEventListener('click', (e) => {
  if (rail.classList.contains('is-open') && !rail.contains(e.target) && !menuBtn.contains(e.target)) closeMenu();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && rail.classList.contains('is-open')) { closeMenu(); menuBtn.focus(); }
});

document.getElementById('privacy-line').append(icon('lock'), h('span', 'Everything stays on this computer'));

// Ask box
const dialog = document.getElementById('ask-dialog');
const askText = document.getElementById('ask-text');
function openAsk() {
  const reason = blockedReason();
  document.getElementById('ask-hint').textContent = reason
    ? `${reason}: Candor needs your profile before it can answer.`
    : isBusy() ? 'Another task is running. Your question will start after it.' : '';
  document.getElementById('ask-send').disabled = !!reason;
  dialog.showModal();
  askText.focus();
}
document.getElementById('ask-rail').append(icon('ask'), h('span', 'Ask Candor'));
document.getElementById('ask-rail').addEventListener('click', openAsk);
document.getElementById('ask-top').addEventListener('click', openAsk);
document.getElementById('ask-form').addEventListener('submit', async (e) => {
  if (e.submitter?.value !== 'send') return;
  e.preventDefault();
  const text = askText.value.trim();
  if (!text) { askText.focus(); return; }
  const b = e.submitter;
  b.disabled = true;
  try {
    await start('/api/ask', { text });
    askText.value = '';
    dialog.close();
  } catch (err) { toast(err.message); } finally { b.disabled = false; }
});

// Data changes re-render only the parts that use them.
onChange((key) => {
  if (key === 'state' || key === 'taskstatus') renderNav();
  if (key === 'state' && store.state && !store.state.setup?.onboarded && route !== 'setup' && route !== 'settings') { go(); return; }
  if (route && (SCREENS[route].deps || []).includes(key)) render({ keepScroll: true });
});

window.addEventListener('hashchange', go);

(async function boot() {
  initRunPanel();
  route = currentRoute();
  main.replaceChildren(h('div.screen', h('div.skeleton-head'), h('div.skeleton', h('div.sk-line'), h('div.sk-line'))));
  await load('state');
  if (store.errors.state) {
    main.replaceChildren(h('div.screen', h('h1', 'Candor could not start'), h('p.inline-error', store.errors.state)));
    return;
  }
  route = null;
  go();
  setInterval(() => load('state'), 15000);
})();
