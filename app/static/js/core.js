// Shared plumbing: API calls, DOM building, icons, safe Markdown, toasts, formatting.
// Server text only ever becomes text nodes; innerHTML is used solely for the icon
// paths authored below.

export const TOKEN = document.querySelector('meta[name=candor-token]')?.content || '';

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

export async function api(path, { method = 'GET', body, raw } = {}) {
  const headers = { 'X-Candor-Token': TOKEN };
  let payload;
  if (raw !== undefined) { payload = raw; headers['Content-Type'] = 'application/octet-stream'; }
  else if (body !== undefined) { payload = JSON.stringify(body); headers['Content-Type'] = 'application/json'; }
  let res;
  try {
    res = await fetch(path, { method, headers, body: payload });
  } catch {
    throw new ApiError('Candor cannot reach its own background program. Close this window and start Candor again.', 0);
  }
  let data = null;
  try { data = await res.json(); } catch { /* empty or not JSON */ }
  if (!res.ok) {
    const msg = data?.error || (res.status === 403
      ? 'This window has lost its connection key. Close it and start Candor again.'
      : `Something went wrong (code ${res.status}). Try again.`);
    throw new ApiError(msg, res.status);
  }
  return data || {};
}

export const post = (path, body = {}) => api(path, { method: 'POST', body });
export const fileUrl = (path) => '/files/' + path.split('/').map(encodeURIComponent).join('/') + '?t=' + encodeURIComponent(TOKEN);

// h('div.cls#id', {attrs}, ...children). Strings and numbers become text nodes.
export function h(sel, attrs, ...kids) {
  if (attrs == null || typeof attrs !== 'object' || attrs instanceof Node || Array.isArray(attrs)) {
    if (attrs != null) kids.unshift(attrs);
    attrs = {};
  }
  const [, tag = 'div', rest = ''] = sel.match(/^([a-z0-9-]*)(.*)$/i);
  const el = document.createElement(tag || 'div');
  for (const part of rest.match(/[.#][^.#]+/g) || []) {
    if (part[0] === '.') el.classList.add(part.slice(1)); else el.id = part.slice(1);
  }
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className += (el.className ? ' ' : '') + v;
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k === 'value') el.value = v;
    else if (k === 'checked') el.checked = !!v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  append(el, kids);
  return el;
}

function append(el, kids) {
  for (const k of kids.flat(Infinity)) {
    if (k == null || k === false || k === '') continue;
    el.append(k instanceof Node ? k : document.createTextNode(String(k)));
  }
}

const PATHS = {
  today: '<rect x="3.5" y="5" width="17" height="15" rx="1.5"/><path d="M3.5 9.5h17M8 3v4M16 3v4M8 14h3"/>',
  jobs: '<path d="M4 6h16M4 12h16M4 18h10"/><path d="M18 16.5l1.5 1.5 3-3"/>',
  applications: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
  profile: '<circle cx="12" cy="8.5" r="3.75"/><path d="M4.5 20c1.2-3.6 4-5.5 7.5-5.5s6.3 1.9 7.5 5.5"/>',
  settings: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  ask: '<path d="M4 5h16v11H9l-5 4z"/><path d="M8.5 9.5h7M8.5 12.5h4"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v6H4V6h6"/>',
  folder: '<path d="M3 6.5h6l2 2h10v10.5H3z"/>',
  down: '<path d="M6 9l6 6 6-6"/>',
  up: '<path d="M6 15l6-6 6 6"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v4h16v-4"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  warn: '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17v.5"/>',
  lock: '<rect x="5" y="10.5" width="14" height="10" rx="1"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/>',
  person: '<circle cx="12" cy="8" r="3.5"/><path d="M5.5 20c.9-3.4 3.4-5.2 6.5-5.2s5.6 1.8 6.5 5.2"/>',
  spark: '<path d="M12 3.5l2 6.5 6.5 2-6.5 2-2 6.5-2-6.5-6.5-2 6.5-2z"/>',
  refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 5v6h-6"/>',
  strike: '<path d="M5 12h14"/>',
  restore: '<path d="M9 7L4 12l5 5"/><path d="M4 12h11a5 5 0 0 1 0 10h-2"/>',
};

export function icon(name, cls = '') {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', '0 0 24 24');
  s.setAttribute('aria-hidden', 'true');
  s.setAttribute('focusable', 'false');
  s.setAttribute('class', 'ico ' + cls);
  s.innerHTML = PATHS[name] || '';
  return s;
}

// Light Markdown -> DOM: paragraphs, "-"/"*" and "1." lists, **bold**, `code`.
export function md(text) {
  const frag = document.createDocumentFragment();
  const blocks = String(text || '').replace(/\r/g, '').split(/\n{2,}/);
  for (const block of blocks) {
    const lines = block.split('\n').filter((l) => l.trim());
    if (!lines.length) continue;
    let list = null;
    let para = null;
    for (const line of lines) {
      const ul = line.match(/^\s*[-*]\s+(.*)$/);
      const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
      if (ul || ol) {
        const tag = ul ? 'ul' : 'ol';
        if (!list || list.tagName.toLowerCase() !== tag) { list = h(tag); frag.append(list); }
        list.append(h('li', inline((ul || ol)[1])));
        para = null;
      } else {
        list = null;
        if (!para) { para = h('p'); frag.append(para); } else para.append(h('br'));
        para.append(inline(line.replace(/^#+\s*/, '')));
      }
    }
  }
  return frag;
}

function inline(s) {
  const frag = document.createDocumentFragment();
  const re = /(\*\*([^*]+)\*\*|`([^`]+)`)/g;
  let last = 0; let m;
  while ((m = re.exec(s))) {
    if (m.index > last) frag.append(s.slice(last, m.index));
    frag.append(m[2] != null ? h('strong', m[2]) : h('code', m[3]));
    last = re.lastIndex;
  }
  if (last < s.length) frag.append(s.slice(last));
  return frag;
}

export function toast(message, kind = 'error') {
  const box = document.getElementById('toasts');
  const t = h('div.toast', { class: 'toast-' + kind },
    icon(kind === 'error' ? 'warn' : 'check'), h('p', message),
    h('button.icon-btn', { type: 'button', 'aria-label': 'Dismiss', onclick: () => t.remove() }, icon('close')));
  box.append(t);
  setTimeout(() => t.remove(), kind === 'error' ? 12000 : 5000);
}

export function announce(msg) {
  const live = document.getElementById('live');
  live.textContent = '';
  setTimeout(() => { live.textContent = msg; }, 50);
}

// Dates
export function parseDate(s) {
  if (!s) return null;
  if (typeof s === 'number') return new Date(s * 1000);
  const d = /^\d{4}-\d{2}-\d{2}$/.test(s) ? new Date(s + 'T12:00:00') : new Date(s);
  return isNaN(d) ? null : d;
}
export function fmtDate(s, opts = { day: 'numeric', month: 'short' }) {
  const d = parseDate(s);
  return d ? d.toLocaleDateString(undefined, opts) : '';
}
export function ago(s) {
  const d = parseDate(s);
  if (!d) return '';
  const mins = Math.round((Date.now() - d) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} h ago`;
  const days = Math.round(hrs / 24);
  return days === 1 ? 'yesterday' : `${days} days ago`;
}
export const plural = (n, one, many = one + 's') => `${n} ${n === 1 ? one : many}`;
export const num = (v, cls = '') => h('span.num', { class: cls }, v == null || v === '' ? '–' : String(v));

// A button with an optional reason it is disabled; the reason stays visible.
export function button(label, { kind = 'secondary', onclick, disabled, reason, ico, type = 'button', id, small } = {}) {
  const rid = reason ? 'r' + Math.random().toString(36).slice(2, 8) : null;
  const b = h('button.btn', {
    type, id, class: `btn-${kind}${small ? ' btn-sm' : ''}`, onclick,
    disabled: !!disabled, 'aria-describedby': rid,
  }, ico ? icon(ico) : null, h('span', label));
  if (!reason) return b;
  return h('span.btn-wrap', b, h('span.reason', { id: rid }, reason));
}

// Wraps an async click: disables the button while it works, shows server errors.
export function busyClick(fn) {
  return async (ev) => {
    const b = ev?.currentTarget;
    if (b) b.disabled = true;
    try { await fn(ev); }
    catch (e) { toast(e.message || String(e)); }
    finally { if (b && b.isConnected) b.disabled = false; }
  };
}

export function skeleton(rows = 4) {
  return h('div.skeleton', { 'aria-busy': 'true', 'aria-label': 'Loading' },
    Array.from({ length: rows }, (_, i) => h('div.sk-line', { style: { width: `${90 - (i % 3) * 18}%` } })));
}
