// One shared copy of what the server said, plus "something changed" notifications.
import { api, post } from './core.js';

const ENDPOINTS = {
  state: '/api/state', jobs: '/api/jobs', apps: '/api/applications',
  profile: '/api/profile', engines: '/api/engines', tasks: '/api/tasks',
};

export const store = { errors: {}, loaded: {} };
const raw = {};
const listeners = new Set();
export const onChange = (fn) => listeners.add(fn);

export async function load(key) {
  if (key === 'history' || key === 'taskstatus') key = 'tasks';
  try {
    const data = await api(ENDPOINTS[key]);
    const text = JSON.stringify(data);
    const changed = text !== raw[key] || store.errors[key];
    raw[key] = text;
    store[key] = data;
    store.errors[key] = null;
    store.loaded[key] = true;
    if (changed) listeners.forEach((fn) => fn(key));
    if (key === 'tasks') {
      // Live tasks change every second; screens only care about these two slices.
      derived('history', data.history || []);
      derived('taskstatus', (data.tasks || []).map((t) => [t.id, t.status]));
    }
  } catch (e) {
    const changed = store.errors[key] !== e.message;
    store.errors[key] = e.message;
    store.loaded[key] = true;
    if (changed) listeners.forEach((fn) => fn(key));
  }
  return store[key];
}

function derived(key, value) {
  const text = JSON.stringify(value);
  if (text === raw[key]) return;
  raw[key] = text;
  listeners.forEach((fn) => fn(key));
}

export const loadAll =(...keys) => Promise.all(keys.map(load));

export const ACTIVE = ['queued', 'running', 'question', 'cancelling'];
export const activeTasks = () => (store.tasks?.tasks || []).filter((t) => ACTIVE.includes(t.status));
export const isBusy = () => activeTasks().length > 0 || !!store.state?.busy;

// Why an agent action cannot start yet (null when it can).
export function blockedReason() {
  const s = store.state?.setup;
  if (s && !s.has_register) return 'Finish setup first';
  return null;
}
export const queueNote = () => (isBusy() ? 'Another task is running. This one will start after it.' : null);

// The run panel registers itself here so any screen can start a task.
export const taskHooks = { started: () => {} };

export async function start(path, body) {
  const res = await post(path, body);
  const views = res.tasks || (res.task ? [res.task] : []);
  taskHooks.started(views);
  return views;
}
