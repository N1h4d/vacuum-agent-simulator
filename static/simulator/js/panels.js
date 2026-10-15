// Agent Brain, Percept History and Performance dashboard.
const esc = (value) => String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
const fmt = (n, digits = 1) => (Number.isInteger(n) ? String(n) : n.toFixed(digits));
const signed = (n) => `${n >= 0 ? '+' : ''}${fmt(n)}`;
const label = (action) => action.replace('MOVE_', '');

export function renderBrain(el, record, agentName, sensorMode) {
  if (!record) {
    el.innerHTML = `<h2>Agent Brain</h2><p class="empty">Press <b>Step</b> or <b>Start</b>. The agent's percept, its options and the reason for its choice will appear here.</p>`;
    return;
  }
  const { percept, decision, result } = record;
  const nb = percept.neighbors;
  const cell = (type, extra = '') => `<div class="t-${type} ${extra}">${type}</div>`;
  const compass = `<div class="compass"><div></div>${cell(nb.MOVE_UP)}<div></div>${cell(nb.MOVE_LEFT)}${cell(percept.current_cell, 'center')}${cell(nb.MOVE_RIGHT)}<div></div>${cell(nb.MOVE_DOWN)}<div></div></div>`;
  const chips = decision.available_actions.map((a) => `<span class="chip ${a === decision.action ? 'selected' : ''}">${a}</span>`).join('');
  const resultClass = result.success ? 'good' : 'bad';

  let candidates = '';
  if (decision.candidates.length) {
    const rows = decision.candidates.map((c) => {
      const parts = Object.entries(c.components).filter(([, v]) => v !== 0)
        .map(([k, v]) => `${esc(k.replaceAll('_', ' '))} ${signed(v)}`).join(', ');
      return `<tr class="${c.action === decision.action ? 'chosen' : ''}"><td>${c.action}</td><td class="num">${c.utility === null ? '—' : signed(c.utility)}</td><td>${parts || esc(c.note) || '—'}</td></tr>`;
    }).join('');
    const header = decision.candidates[0].components.q_value !== undefined ? 'Q-value' : 'Utility';
    candidates = `<div class="section-title">Options considered</div><div class="table-scroll"><table class="data"><thead><tr><th>Action</th><th class="num">${header}</th><th>Breakdown</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }
  const plan = decision.plan.length ? `<div class="section-title">Plan</div><div class="small">${decision.plan.length} step(s) to target (${decision.plan.at(-1)[0]},${decision.plan.at(-1)[1]}) &mdash; highlighted on the grid</div>` : '';

  el.innerHTML = `<h2>Agent Brain &middot; ${esc(agentName)}</h2>
    <div class="brain-grid">${compass}
      <div class="kv"><span>Step</span><b>${record.step}</b><span>Position</span><b>(${percept.position[0]}, ${percept.position[1]})</b>
      <span>Sensors</span><b>${esc(sensorMode)}</b><span>Cell</span><b>${percept.current_cell}</b></div></div>
    <div class="section-title">Available actions</div><div class="chips">${chips}</div>
    <div class="section-title">Selected action</div><div class="chips"><span class="chip selected">${decision.action}</span></div>
    <div class="reason"><b>Reason:</b> ${esc(decision.reason)}</div>
    <div class="kv"><span>Outcome</span><b class="${resultClass}">${result.outcome}</b><span>Reward</span><b class="${record.reward >= 0 ? 'good' : 'bad'}">${signed(record.reward)}</b></div>
    ${candidates}${plan}`;
}

export function renderHistory(el, records, frame) {
  if (!frame) { el.innerHTML = '<p class="empty">No percepts yet.</p>'; return; }
  const rows = [];
  for (let i = frame - 1; i >= 0; i--) {
    const r = records[i];
    rows.push(`<div class="item"><b>#${r.step}</b><span>(${r.percept.position[0]},${r.percept.position[1]})</span><span>${r.percept.current_cell}</span><span>${r.decision.action} &rarr; ${r.result.outcome}</span><span class="${r.reward >= 0 ? 'good' : 'bad'}">${signed(r.reward)}</span></div>`);
  }
  el.innerHTML = rows.join('');
}

export function renderDashboard(el, perf) {
  const total = perf.dirt_cleaned + perf.remaining_dirt;
  const pct = total ? Math.round((perf.dirt_cleaned / total) * 100) : 100;
  const metric = (name, value) => `<div class="metric"><span>${name}</span><b>${value}</b></div>`;
  el.innerHTML = `<h2>Performance <span class="pill ${perf.status}" style="float:right">${perf.status.replaceAll('_', ' ')}</span></h2>
    <div class="metrics">${metric('Total score', fmt(perf.score))}${metric('Steps', perf.steps)}${metric('Dirt cleaned', perf.dirt_cleaned)}
    ${metric('Remaining dirt', perf.remaining_dirt)}${metric('Invalid actions', perf.invalid_actions)}${metric('Efficiency', perf.efficiency.toFixed(2))}</div>
    <div class="bar" title="${pct}% of reachable dirt cleaned"><i style="width:${pct}%"></i></div>`;
}
