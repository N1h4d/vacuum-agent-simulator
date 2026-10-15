// Comparison tab: same environment -> several agents -> table, bars, learning curve.
import { runComparison } from './api.js';

const SHORT = { reflex: 'Reflex', goal: 'Goal', utility: 'Utility', learning: 'Learning' };
const ROWS = [
  ['Steps', 'steps', 'min'], ['Dirt cleaned', 'dirt_cleaned', 'max'], ['Remaining dirt', 'remaining_dirt', 'min'],
  ['Invalid actions', 'invalid_actions', 'min'], ['Score', 'score', 'max'], ['Efficiency (dirt/step)', 'efficiency', 'max'],
  ['Status', 'status', null],
];

function bestSet(rows, key, goal) {
  if (!goal || rows.length < 2) return new Set();
  const values = rows.map((r) => r[key]);
  const best = goal === 'max' ? Math.max(...values) : Math.min(...values);
  if (values.every((v) => v === best)) return new Set();
  return new Set(rows.filter((r) => r[key] === best).map((r) => r.agent));
}

function renderTable(rows, title) {
  const head = rows.map((r) => `<th class="num">${SHORT[r.agent] || r.agent}</th>`).join('');
  const body = ROWS.map(([name, key, goal]) => {
    const best = bestSet(rows, key, goal);
    const cells = rows.map((r) => {
      const value = key === 'efficiency' ? r[key].toFixed(2) : String(r[key]).replaceAll('_', ' ');
      return `<td class="num ${best.has(r.agent) ? 'best' : ''}">${value}</td>`;
    }).join('');
    return `<tr><td>${name}</td>${cells}</tr>`;
  }).join('');
  return `<div class="card"><h2>${title}</h2><div class="table-scroll"><table class="data"><thead><tr><th></th>${head}</tr></thead><tbody>${body}</tbody></table></div>
    <div class="row wrap">${rows.map((r) => `<button class="btn watch" data-kind="${r.agent}">Watch ${SHORT[r.agent]} in simulator</button>`).join('')}</div></div>`;
}

function renderBars(rows, key, title) {
  const max = Math.max(...rows.map((r) => Math.abs(r[key])), 1);
  const lines = rows.map((r) => `<div class="line"><span>${SHORT[r.agent]}</span>
    <div class="track"><div class="fill ${r[key] < 0 ? 'neg' : ''}" style="width:${(Math.abs(r[key]) / max) * 100}%"></div></div><b>${r[key]}</b></div>`).join('');
  return `<div><h2>${title}</h2><div class="bars">${lines}</div></div>`;
}

function renderCurve(curve) {
  const width = 400, height = 160, pad = 28, windowSize = 8;
  const min = Math.min(...curve), max = Math.max(...curve), span = max - min || 1;
  const x = (i) => pad + (i / Math.max(1, curve.length - 1)) * (width - pad - 8);
  const y = (v) => height - pad - ((v - min) / span) * (height - pad - 10);
  const avg = curve.map((_, i) => {
    const slice = curve.slice(Math.max(0, i - windowSize + 1), i + 1);
    return slice.reduce((a, b) => a + b, 0) / slice.length;
  });
  const line = (values, color, w) => `<polyline fill="none" stroke="${color}" stroke-width="${w}" points="${values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')}"/>`;
  return `<div class="card"><h2>Learning curve (training episodes)</h2>
    <svg class="curve" viewBox="0 0 ${width} ${height}" role="img" aria-label="Score per training episode">
      ${line(curve, '#3b4a78', 1)}${line(avg, '#4cc9f0', 2.5)}
      <text x="4" y="14" fill="#8e9bbd" font-size="10">${Math.round(max)}</text><text x="4" y="${height - pad}" fill="#8e9bbd" font-size="10">${Math.round(min)}</text>
      <text x="${pad}" y="${height - 8}" fill="#8e9bbd" font-size="10">episode 1</text><text x="${width - 70}" y="${height - 8}" fill="#8e9bbd" font-size="10">episode ${curve.length}</text></svg>
    <p class="muted small">Score of each random training world (grey) and its moving average (blue). The agent improves by trial and error; epsilon (exploration) shrinks over time. Evaluation on your environment uses the learned policy without exploration.</p></div>`;
}

export function initCompare({ getContext, onWatch, toast }) {
  const button = document.getElementById('btn-compare');
  const result = document.getElementById('compare-result');
  const note = document.getElementById('compare-note');

  button.addEventListener('click', async () => {
    const kinds = [...document.querySelectorAll('#compare-agents input:checked')].map((i) => i.value);
    if (!kinds.length) { toast('Select at least one agent.'); return; }
    const ctx = getContext();
    button.disabled = true;
    note.textContent = kinds.includes('learning') ? 'Running… the learning agent trains first (a few seconds).' : 'Running…';
    try {
      const data = await runComparison({ environment: ctx.environment, agents: kinds, sensor_mode: ctx.sensorMode });
      const dirty = ctx.environment.cells.join('').split('D').length - 1;
      result.innerHTML = renderTable(data.table, `${ctx.label} &middot; ${ctx.environment.width}&times;${ctx.environment.height} &middot; ${dirty} dirty cells &middot; sensors ${ctx.sensorMode}`)
        + `<div class="card"><div class="chart-grid">${renderBars(data.table, 'score', 'Score (higher is better)')}${renderBars(data.table, 'steps', 'Steps (lower is better)')}</div></div>`
        + (data.traces.learning?.training_curve ? renderCurve(data.traces.learning.training_curve) : '');
      result.querySelectorAll('.watch').forEach((b) => b.addEventListener('click', () => onWatch(b.dataset.kind, data.traces[b.dataset.kind])));
      note.textContent = '';
    } catch (error) {
      note.textContent = ''; toast(error.message);
    } finally {
      button.disabled = false;
    }
  });
}
