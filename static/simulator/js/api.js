// Thin fetch wrapper around the Django JSON API.
const csrfToken = () => document.querySelector('meta[name="csrf-token"]').content;

async function post(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

export const generateEnvironment = (params) => post('/api/environment/generate', params);
export const runSimulation = (body) => post('/api/simulation/run', body);
export const runComparison = (body) => post('/api/comparison/run', body);
