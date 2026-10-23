// Settings: engine, mode, search size, screening, the doctor, privacy.
import { h, icon, num, busyClick, post, toast, skeleton } from './core.js';
import { store, load } from './store.js';
import { panelHead } from './today.js';

export const deps = ['state', 'engines'];
export const fresh = ['engines'];

let doctorOut = null;

async function save(patch) {
  await post('/api/settings', patch);
  await load('state');
  toast('Saved.', 'ok');
}

// Ready means installed and signed in with a plan; an API key bills per use, so it is not.
export const engineReady = (e) => !!(e.installed && e.signed_in && !e.api_key);

export function engineCards(engines) {
  if (!engines) return skeleton(3);
  return h('ul.engine-cards', (engines.engines || []).map((e) => {
    const ok = engineReady(e);
    const plan = e.name === 'codex' ? 'ChatGPT' : 'Claude';
    return h('li.engine-card', { class: ok ? 'is-ok' : e.api_key ? 'is-warn' : '' },
      h('p.engine-name', e.label, h('span.status', { class: ok ? 'st-strong' : e.api_key ? 'st-gate-fail' : e.installed ? 'st-maybe' : 'st-weak' },
        ok ? 'Ready' : e.api_key ? 'API key' : e.installed ? 'Not signed in' : 'Not installed')),
      e.api_key ? h('p.engine-warn', icon('warn'), h('span', `Signed in with an API key: runs would be billed per use. Sign in with your ${plan} plan instead.`)) : null,
      h('dl.facts',
        h('dt', 'Installed'), h('dd', e.installed ? h('span', icon('check'), ' Yes', e.version ? h('span.num.muted', ` (${e.version})`) : null) : 'No'),
        h('dt', 'Signed in'), h('dd', e.signed_in ? h('span', icon('check'), ' Yes') : 'No')));
  }));
}

export function render() {
  const s = store.state?.settings;
  if (!s) return h('div.screen', skeleton(8));
  const eng = store.engines;
  const radio = (name, value, label, desc, current) => h('label.choice', { class: current === value ? 'is-on' : '' },
    h('input', { type: 'radio', name, value, checked: current === value,
      onchange: busyClick(() => save({ [name]: value })) }),
    h('span.choice-text', h('span.choice-label', label), h('span.choice-desc', desc)));

  const resolved = eng?.resolved;
  return h('div.screen.settings',
    h('header.page-head', h('h1', 'Settings'), h('p.lede', 'Most people never need to change these.')),

    h('section.panel', { 'aria-labelledby': 'eng-title' }, panelHead('eng-title', 'Which assistant does the work', null),
      h('fieldset.choices', h('legend.sr-only', 'Engine'),
        radio('engine', 'auto', 'Automatic (recommended)', 'Uses Codex for the long application runs when it is installed, otherwise Claude.', s.engine),
        radio('engine', 'claude', 'Claude', 'Always use Claude.', s.engine),
        radio('engine', 'codex', 'Codex', 'Always use Codex (ChatGPT).', s.engine)),
      h('p.panel-intro', 'Both run on your own subscription. There is no API key and no extra bill.'),
      store.errors.engines ? h('p.inline-error', store.errors.engines) : engineCards(eng),
      resolved && (resolved.apply || resolved.other)
        ? h('p.muted', `Right now: applications use ${cap(resolved.apply) || 'nothing'}, everything else uses ${cap(resolved.other) || 'nothing'}.`)
        : eng ? h('p.inline-error', 'No assistant is ready. Install Claude (claude.com/code) or Codex (chatgpt.com/codex) and sign in, then press Check again.') : null,
      h('button.btn.btn-quiet.btn-sm', { type: 'button', onclick: busyClick(() => load('engines')) }, icon('refresh'), h('span', 'Check again'))),

    h('section.panel', { 'aria-labelledby': 'mode-title' }, panelHead('mode-title', 'How thorough', null),
      h('fieldset.choices', h('legend.sr-only', 'Mode'),
        radio('mode', 'lite', 'Lite (recommended)', 'Uses a fraction of your plan. Right for most plans below Claude Max or ChatGPT Pro. Every fact check still runs.', s.mode),
        radio('mode', 'standard', 'Standard', 'Adds a style pass, a second reviewer and company research. Uses much more of your plan.', s.mode))),

    h('section.panel', { 'aria-labelledby': 'search-title' }, panelHead('search-title', 'Job search', null),
      h('div.form-row',
        h('label.field.narrow', h('span.label', 'Jobs to look at per role, each search'),
          h('input#search-top', { type: 'number', min: 1, max: 50, value: s.search_top,
            onchange: busyClick(async (e) => {
              const v = Math.round(+e.target.value);
              if (!(v >= 1 && v <= 50)) { toast('Choose a number from 1 to 50.'); e.target.value = s.search_top; return; }
              await save({ search_top: v });
            }) }))),
      h('label.check', h('input', { type: 'checkbox', checked: s.screen_after_search,
        onchange: busyClick((e) => save({ screen_after_search: e.target.checked })) }),
      h('span', h('span.choice-label', 'Check new jobs against my limits after each search'),
        h('span.choice-desc', 'Candor sets aside jobs that break your limits (pay, commute, jobs you refuse) before you see them. Takes a few extra minutes.')))),

    h('section.panel', { 'aria-labelledby': 'doc-title' }, panelHead('doc-title', 'Check my computer', null),
      h('p.panel-intro', 'Checks that everything Candor needs is installed and working. Takes up to a minute.'),
      h('button.btn.btn-secondary', { type: 'button', onclick: busyClick(async () => {
        doctorOut = { running: true };
        rerender();
        try {
          const r = await post('/api/doctor');
          doctorOut = { text: r.output || '', ok: r.ok };
        } catch (e) { doctorOut = { text: e.message, ok: false }; }
        rerender();
      }) }, icon('refresh'), h('span', 'Check my computer')),
      doctorOut?.running ? h('div', { 'aria-live': 'polite' }, skeleton(3), h('p.muted', 'Checking…'))
        : doctorOut ? h('div', { 'aria-live': 'polite' },
          h('p', { class: doctorOut.ok ? 'ok-line' : 'inline-error' }, doctorOut.ok ? 'Everything needed is in place.' : 'Something needs attention. The details are below.'),
          h('pre.doctor', doctorOut.text)) : null),

    h('section.panel', { 'aria-labelledby': 'priv-title' }, panelHead('priv-title', 'Your privacy', null),
      h('ul.plain-list',
        h('li', 'Your CV, profile and applications are saved in this folder on this computer only.'),
        h('li', 'The assistant (Claude or Codex) reads them to do the work, through your own account.'),
        h('li', 'Job searches read public job boards. Nothing about you is sent to them.'),
        h('li', 'Candor never sends an application or an email. You do that yourself.'))),

    h('section.panel', { 'aria-labelledby': 'rerun-title' }, panelHead('rerun-title', 'Start again', null),
      h('p.panel-intro', 'Run setup again with a new CV or different answers. Your existing applications stay.'),
      h('a.btn.btn-quiet', { href: '#/setup' }, icon('arrow'), h('span', 'Re-run setup'))),
    h('p.muted.small', `Candor ${store.state?.app?.version || ''}`));
}

const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : '');

function rerender() {
  if (document.body.dataset.route === 'settings') document.getElementById('main').replaceChildren(render());
}
