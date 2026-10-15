// Controller: environment editing, playback of a recorded trace, tab switching.
import { generateEnvironment, runSimulation } from './api.js';
import { initCompare } from './compare.js';
import { GridView, cloneEnvironment, parseEnvironment, reachableDirt, serializeEnvironment } from './grid_view.js';
import { renderBrain, renderDashboard, renderHistory } from './panels.js';

const $ = (id) => document.getElementById(id);
const AGENTS = JSON.parse($('agents-data').textContent);
const state = { env0: null, env: null, label: '', trace: null, traceKey: null, frame: 0, timer: null, visited: new Set(), plan: [], tool: null, busy: false };

// ---------- helpers ----------
let toastTimer;
function toast(message) {
  const el = $('toast');
  el.textContent = message; el.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { el.hidden = true; }, 4500);
}
const cellIndex = (env, [r, c]) => r * env.width + c;
const delay = () => 1100 - Number($('in-speed').value) * 100;
const currentKey = () => JSON.stringify([serializeEnvironment(state.env0), $('in-agent').value, $('in-sensors').value]);
const agentName = () => AGENTS.find((a) => a.kind === $('in-agent').value)?.name ?? '';

function blankPerformance() {
  return { score: 0, steps: 0, dirt_cleaned: 0, remaining_dirt: reachableDirt(state.env0), invalid_actions: 0, efficiency: 0, status: 'READY' };
}

// ---------- rendering ----------
const view = new GridView($('grid-wrap'), $('grid'), $('vacuum'), paintCell);

function render() {
  view.editable = state.tool !== null;
  view.render(state.env, { visited: state.visited, plan: state.plan });
  const records = state.trace?.records ?? [];
  const record = state.frame ? records[state.frame - 1] : null;
  renderBrain($('brain'), record, state.trace?.name ?? agentName(), state.trace?.sensor_mode ?? $('in-sensors').value);
  renderHistory($('history'), records, state.frame);
  let performance = record ? record.performance : blankPerformance();
  if (!record && state.trace && !records.length) performance = state.trace.summary;
  renderDashboard($('dashboard'), performance);
  updateButtons();
}

function updateButtons() {
  $('btn-start').disabled = state.busy || Boolean(state.timer);
  $('btn-pause').disabled = !state.timer;
  $('btn-step').disabled = state.busy;
  $('btn-replay').disabled = state.busy || !state.trace;
  document.querySelectorAll('.tool').forEach((b) => b.classList.toggle('active', b.dataset.tool === state.tool));
}

// ---------- environment ----------
function setEnvironment(snapshot, label) {
  state.env0 = parseEnvironment(snapshot);
  state.label = label;
  state.trace = null; state.traceKey = null;
  $('env-label').textContent = label;
  resetPlayback();
}

function paintCell(r, c) {
  const env = state.env0, here = env.vacuum;
  const isStart = here[0] === r && here[1] === c;
  if (state.tool === 'start') {
    if (env.cells[r][c] === '#') env.cells[r][c] = '.';
    env.vacuum = [r, c];
  } else if (state.tool === '#' && isStart) {
    return;
  } else {
    env.cells[r][c] = state.tool;
  }
  state.label = 'Custom layout'; $('env-label').textContent = 'Custom layout';
  state.trace = null; state.traceKey = null;
  resetPlayback();
}

async function onGenerate() {
  const seedText = $('in-seed').value.trim();
  const params = {
    width: Number($('in-width').value), height: Number($('in-height').value),
    dirt_percent: Number($('in-dirt').value), obstacle_percent: Number($('in-obstacles').value),
    random_start: $('in-start').value === 'random', seed: seedText === '' ? null : Number(seedText),
  };
  try {
    const data = await generateEnvironment(params);
    setEnvironment(data.environment, `Environment #${data.seed}`);
  } catch (error) { toast(error.message); }
}

// ---------- playback ----------
function stopTimer() {
  clearInterval(state.timer); state.timer = null; updateButtons();
}

function resetPlayback() {
  stopTimer();
  state.frame = 0;
  state.env = cloneEnvironment(state.env0);
  state.visited = new Set([cellIndex(state.env, state.env.vacuum)]);
  state.plan = [];
  render();
}

async function ensureTrace() {
  const key = currentKey();
  if (state.trace && state.traceKey === key) return true;
  state.busy = true; updateButtons(); $('dashboard').classList.add('loading');
  try {
    state.trace = await runSimulation({ environment: serializeEnvironment(state.env0), agent: $('in-agent').value, sensor_mode: $('in-sensors').value });
    state.traceKey = key;
    return true;
  } catch (error) {
    toast(error.message); return false;
  } finally {
    state.busy = false; $('dashboard').classList.remove('loading'); updateButtons();
  }
}

function advance() {
  const record = state.trace.records[state.frame];
  if (!record) { stopTimer(); return false; }
  const { outcome, position_after: after } = record.result;
  if (outcome === 'MOVED') state.env.vacuum = [...after];
  if (outcome === 'CLEANED') state.env.cells[after[0]][after[1]] = '.';
  state.visited.add(cellIndex(state.env, state.env.vacuum));
  state.plan = record.decision.plan;
  state.frame += 1;
  render();
  if (outcome === 'CLEANED') view.flash('sucking');
  else if (outcome.startsWith('BUMPED') || outcome === 'WASTED_SUCK') view.flash('bump');
  if (state.frame >= state.trace.records.length) { stopTimer(); state.plan = []; render(); }
  return true;
}

function startTimer() {
  clearInterval(state.timer);
  state.timer = setInterval(advance, delay());
  updateButtons();
}

async function onStart() {
  if (!(await ensureTrace())) return;
  if (state.frame >= state.trace.records.length) resetPlayback();
  if (!state.trace.records.length) { render(); return; }
  startTimer();
}

async function onStep() {
  stopTimer();
  if (!(await ensureTrace())) return;
  if (state.frame >= state.trace.records.length) {
    if (state.frame === 0) render(); else toast('The run is finished. Press Reset or Replay.');
    return;
  }
  advance();
}

function onReplay() {
  if (!state.trace) return;
  resetPlayback();
  if (state.trace.records.length) startTimer();
}

function onAgentOrSensorChange() {
  $('agent-description').textContent = AGENTS.find((a) => a.kind === $('in-agent').value)?.description ?? '';
  resetPlayback();
}

// ---------- wiring ----------
$('btn-generate').addEventListener('click', onGenerate);
$('btn-start').addEventListener('click', onStart);
$('btn-pause').addEventListener('click', stopTimer);
$('btn-step').addEventListener('click', onStep);
$('btn-reset').addEventListener('click', resetPlayback);
$('btn-replay').addEventListener('click', onReplay);
$('in-agent').addEventListener('change', onAgentOrSensorChange);
$('in-sensors').addEventListener('change', onAgentOrSensorChange);
$('in-speed').addEventListener('input', () => { if (state.timer) startTimer(); });
document.querySelectorAll('.tool').forEach((button) => button.addEventListener('click', () => {
  state.tool = state.tool === button.dataset.tool ? null : button.dataset.tool;
  render();
}));

document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => showView(tab.dataset.view)));
function showView(name) {
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('active', t.dataset.view === name));
  document.querySelectorAll('.view').forEach((v) => v.classList.toggle('active', v.id === `view-${name}`));
}

initCompare({
  toast,
  getContext: () => ({ environment: serializeEnvironment(state.env0), sensorMode: $('in-sensors').value, label: state.label }),
  onWatch: (kind, trace) => {
    $('in-agent').value = kind;
    $('agent-description').textContent = AGENTS.find((a) => a.kind === kind)?.description ?? '';
    state.trace = trace; state.traceKey = currentKey();
    resetPlayback();
    showView('simulate');
  },
});

onGenerate().then(() => { $('agent-description').textContent = AGENTS.find((a) => a.kind === $('in-agent').value)?.description ?? ''; });
