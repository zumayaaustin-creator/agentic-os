const api = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  async post(path, body = {}, controller) {
    const opts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
    if (controller) opts.signal = controller.signal;
    const r = await fetch(path, opts);
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  async put(path, body = {}) {
    const r = await fetch(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  async del(path) {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed: ${r.status}`); }
    return r.json();
  },
  getStatus: () => api.get('/api/status'),
  getBrain: () => api.get('/api/brain'),
  getBrainFile: (name) => api.get(`/api/brain/${encodeURIComponent(name)}`),
  updateBrainFile: (name, content) => api.put(`/api/brain/${encodeURIComponent(name)}`, { content }),
  getSkills: () => api.get('/api/skills'),
  getSkill: (name) => api.get(`/api/skills/${encodeURIComponent(name)}`),
  runSkill: (name, input = '', agent = 'auto') => api.post(`/api/skills/${encodeURIComponent(name)}/run`, { input, agent }),
  getSkillEval: (name) => api.get(`/api/skills/${encodeURIComponent(name)}/eval`),
  getJobs: () => api.get('/api/scheduler/jobs'),
  createJob: (job) => api.post('/api/scheduler/jobs', job),
  deleteJob: (id) => api.del(`/api/scheduler/jobs/${encodeURIComponent(id)}`),
  getAudit: (limit = 100) => api.get(`/api/audit?limit=${limit}`),
  getCost: () => api.get('/api/cost'),
  recordCost: (data) => api.post('/api/cost/record', data),
  getPlugins: () => api.get('/api/plugins'),
  installPlugin: (name) => api.post('/api/plugins/install', { name }),
  getBackups: () => api.get('/api/backups'),
  createBackup: () => api.post('/api/backup'),
  restoreBackup: (file) => api.post('/api/backup/restore', { file }),
  getPrompts: () => api.get('/api/prompts'),
  getSettings: () => api.get('/api/settings'),
  updateSettings: (settings) => api.put('/api/settings', { settings }),
  getStandards: () => api.get('/api/standards'),
  discoverStandards: () => api.post('/api/standards/discover'),
  chat: (agent, message, controller) => api.post('/api/chat', { agent, message }, controller),
  getChatHistory: () => api.get('/api/chat/history'),
};
