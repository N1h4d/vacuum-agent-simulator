// Renders the grid world and the vacuum robot. Pure view code: no AI logic.
const ROBOT_SVG = `<svg viewBox="0 0 40 40" aria-label="Vacuum agent">
  <circle cx="20" cy="20" r="16" fill="#e8f1ff"/><circle cx="20" cy="20" r="16" fill="none" stroke="#4cc9f0" stroke-width="2"/>
  <circle cx="20" cy="20" r="8" fill="#0b1220"/><circle cx="20" cy="20" r="3" fill="#4cc9f0"/>
  <rect x="17" y="2" width="6" height="5" rx="2" fill="#7b61ff"/></svg>`;

export const parseEnvironment = (snapshot) => ({
  width: snapshot.width, height: snapshot.height,
  cells: snapshot.cells.map((row) => [...row]), vacuum: [...snapshot.vacuum],
});
export const cloneEnvironment = (env) => ({ ...env, cells: env.cells.map((r) => [...r]), vacuum: [...env.vacuum] });
export const serializeEnvironment = (env) => ({
  width: env.width, height: env.height, cells: env.cells.map((r) => r.join('')), vacuum: [...env.vacuum],
});

export function reachableDirt(env) {
  const key = (r, c) => r * env.width + c;
  const seen = new Set([key(...env.vacuum)]);
  const queue = [env.vacuum];
  let dirt = 0;
  while (queue.length) {
    const [r, c] = queue.shift();
    if (env.cells[r][c] === 'D') dirt++;
    for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
      const nr = r + dr, nc = c + dc;
      if (nr < 0 || nc < 0 || nr >= env.height || nc >= env.width) continue;
      if (env.cells[nr][nc] === '#' || seen.has(key(nr, nc))) continue;
      seen.add(key(nr, nc));
      queue.push([nr, nc]);
    }
  }
  return dirt;
}

export class GridView {
  constructor(wrapEl, gridEl, vacuumEl, onCellPointer) {
    this.wrap = wrapEl; this.grid = gridEl; this.vacuum = vacuumEl;
    this.vacuum.innerHTML = ROBOT_SVG;
    this.onCellPointer = onCellPointer;
    this.editable = false; this.pointerDown = false; this.tiles = [];
    window.addEventListener('pointerup', () => { this.pointerDown = false; });
    this.grid.addEventListener('pointerdown', (e) => this._handle(e, true));
    this.grid.addEventListener('pointerover', (e) => { if (this.pointerDown) this._handle(e, false); });
  }

  _handle(event, isDown) {
    if (!this.editable) return;
    const cell = event.target.closest('.cell');
    if (!cell) return;
    if (isDown) this.pointerDown = true;
    this.onCellPointer(Number(cell.dataset.r), Number(cell.dataset.c));
  }

  build(env) {
    this.wrap.style.aspectRatio = `${env.width} / ${env.height}`;
    this.grid.style.gridTemplateColumns = `repeat(${env.width}, 1fr)`;
    this.grid.style.gridTemplateRows = `repeat(${env.height}, 1fr)`;
    this.grid.innerHTML = '';
    this.tiles = [];
    for (let r = 0; r < env.height; r++) {
      for (let c = 0; c < env.width; c++) {
        const cell = document.createElement('div');
        cell.className = 'cell'; cell.dataset.r = r; cell.dataset.c = c;
        cell.innerHTML = '<div class="tile"><div class="dirt"></div></div>';
        this.grid.appendChild(cell);
        this.tiles.push(cell);
      }
    }
    this.vacuum.style.width = `${100 / env.width}%`;
    this.vacuum.style.height = `${100 / env.height}%`;
    this.builtFor = `${env.width}x${env.height}`;
  }

  render(env, { visited = new Set(), plan = [] } = {}) {
    if (this.builtFor !== `${env.width}x${env.height}`) this.build(env);
    const planKeys = new Set(plan.map(([r, c]) => r * env.width + c));
    this.tiles.forEach((cell, index) => {
      const r = Math.floor(index / env.width), c = index % env.width, symbol = env.cells[r][c];
      cell.classList.toggle('dirty', symbol === 'D');
      cell.classList.toggle('obstacle', symbol === '#');
      cell.classList.toggle('visited', visited.has(index) && symbol !== '#');
      cell.classList.toggle('on-path', planKeys.has(index));
      cell.classList.toggle('editable', this.editable);
    });
    this.vacuum.style.left = `${(env.vacuum[1] / env.width) * 100}%`;
    this.vacuum.style.top = `${(env.vacuum[0] / env.height) * 100}%`;
  }

  flash(kind) {
    this.vacuum.classList.remove('bump', 'sucking');
    void this.vacuum.offsetWidth; // restart the CSS animation
    this.vacuum.classList.add(kind);
  }
}
