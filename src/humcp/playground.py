"""HuMCP Playground - interactive tool browser and executor."""


def get_playground_html() -> str:
    """Return self-contained HTML playground page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>HuMCP Playground</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { margin: 0; font-family: system-ui, -apple-system, sans-serif; }
    .category-tools { display: none; }
    .category-tools.open { display: block; }
    .tool-card:hover { background-color: #f1f5f9; }
    .tool-card.selected { background-color: #e0f2fe; border-left: 3px solid #0284c7; }
    #app-iframe { border: none; width: 100%; min-height: 200px; }
    .json-key { color: #0369a1; }
    .json-string { color: #15803d; }
    .json-number { color: #c2410c; }
    .json-boolean { color: #7c3aed; }
    .json-null { color: #6b7280; }
    .spinner { border: 3px solid #e2e8f0; border-top-color: #0284c7;
               border-radius: 50%; width: 20px; height: 20px;
               animation: spin 0.6s linear infinite; display: inline-block; }
    @keyframes spin { to { transform: rotate(360deg); } }
    input:focus, textarea:focus, select:focus {
      outline: none; box-shadow: 0 0 0 2px #0284c7;
    }
  </style>
</head>
<body class="bg-slate-50 h-screen flex flex-col">

  <!-- Header -->
  <header class="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 bg-sky-600 rounded-lg flex items-center justify-center">
        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2"
             viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round"
             d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" /></svg>
      </div>
      <h1 class="text-lg font-semibold text-slate-800">HuMCP Playground</h1>
    </div>
    <div class="flex items-center gap-4 text-sm text-slate-500">
      <span id="tool-count"></span>
      <a href="/docs" class="hover:text-sky-600 transition-colors">Swagger</a>
      <a href="/mcp" class="hover:text-sky-600 transition-colors">MCP</a>
    </div>
  </header>

  <!-- Main -->
  <div class="flex flex-1 overflow-hidden">

    <!-- Sidebar -->
    <aside class="w-80 bg-white border-r border-slate-200 flex flex-col shrink-0">
      <div class="p-3 border-b border-slate-100">
        <input id="search" type="text" placeholder="Search tools..."
               class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50" />
      </div>
      <div id="sidebar" class="flex-1 overflow-y-auto p-2"></div>
    </aside>

    <!-- Detail Panel -->
    <main id="detail" class="flex-1 overflow-y-auto">
      <div id="empty-state" class="flex items-center justify-center h-full text-slate-400 text-sm">
        Select a tool from the sidebar to get started
      </div>
      <div id="tool-detail" class="hidden p-6 max-w-3xl">
        <!-- Tool header -->
        <div class="mb-6">
          <div class="flex items-center gap-3 mb-2">
            <h2 id="tool-name" class="text-xl font-semibold text-slate-800"></h2>
            <span id="tool-category" class="text-xs font-medium px-2 py-0.5 rounded-full bg-sky-100 text-sky-700"></span>
            <span id="tool-app-badge" class="hidden text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">MCP App</span>
          </div>
          <p id="tool-desc" class="text-sm text-slate-600"></p>
        </div>

        <!-- Input form -->
        <div class="mb-6">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">Parameters</h3>
          <form id="tool-form" class="space-y-4"></form>
          <button id="execute-btn" type="button"
                  class="mt-4 px-5 py-2 bg-sky-600 text-white text-sm font-medium rounded-lg
                         hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            Execute
          </button>
        </div>

        <!-- Result -->
        <div id="result-section" class="hidden">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">Result</h3>
          <div id="result-container" class="border border-slate-200 rounded-lg overflow-hidden bg-white"></div>
        </div>
      </div>
    </main>
  </div>

<script>
// ── State ──────────────────────────────────────────────────────────
const state = {
  tools: {},        // category -> [{name, description, endpoint}]
  apps: new Set(),  // tool names that have MCP App bundles
  selected: null,   // {category, name, description, endpoint, schema}
};

// ── API Client ─────────────────────────────────────────────────────
async function fetchTools() {
  const res = await fetch('/tools');
  return res.json();
}

async function fetchApps() {
  const res = await fetch('/apps');
  return res.json();
}

async function fetchToolDetail(category, name) {
  const res = await fetch(`/tools/${category}/${name}`);
  return res.json();
}

async function executeTool(name, params) {
  const res = await fetch(`/tools/${name}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Execution failed');
  }
  return res.json();
}

async function fetchAppHtml(name) {
  const res = await fetch(`/apps/${name}`);
  if (!res.ok) return null;
  return res.text();
}

// ── Sidebar Renderer ───────────────────────────────────────────────
function renderSidebar(filter = '') {
  const sidebar = document.getElementById('sidebar');
  const lowerFilter = filter.toLowerCase();
  let html = '';

  for (const [category, tools] of Object.entries(state.tools).sort()) {
    const filtered = tools.filter(t =>
      t.name.toLowerCase().includes(lowerFilter) ||
      (t.description || '').toLowerCase().includes(lowerFilter)
    );
    if (filtered.length === 0) continue;

    const isOpen = filter || filtered.some(t =>
      state.selected && t.name === state.selected.name
    );

    html += `
      <div class="mb-1">
        <button onclick="toggleCategory(this)"
                class="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold
                       text-slate-500 uppercase tracking-wide hover:bg-slate-50 rounded-lg">
          <span>${escapeHtml(category.replace(/_/g, ' '))}</span>
          <span class="flex items-center gap-1">
            <span class="text-slate-400 font-normal normal-case">${filtered.length}</span>
            <svg class="w-3 h-3 transition-transform ${isOpen ? 'rotate-90' : ''}"
                 fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
            </svg>
          </span>
        </button>
        <div class="category-tools ${isOpen ? 'open' : ''} ml-2">
          ${filtered.map(t => `
            <div class="tool-card px-3 py-2 text-sm rounded-lg cursor-pointer mb-0.5
                        ${state.selected && state.selected.name === t.name ? 'selected' : ''}"
                 data-category="${escapeAttr(category)}" data-tool="${escapeAttr(t.name)}"
                 onclick="selectTool(this.dataset.category, this.dataset.tool)">
              <div class="flex items-center gap-2">
                <span class="font-medium text-slate-700">${escapeHtml(t.name)}</span>
                ${state.apps.has(t.name) ? '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0"></span>' : ''}
              </div>
              ${t.description ? `<div class="text-xs text-slate-400 mt-0.5 truncate">${escapeHtml(t.description)}</div>` : ''}
            </div>
          `).join('')}
        </div>
      </div>`;
  }

  sidebar.innerHTML = html || '<div class="p-4 text-sm text-slate-400">No tools found</div>';
}

function toggleCategory(btn) {
  const tools = btn.nextElementSibling;
  const arrow = btn.querySelector('svg');
  tools.classList.toggle('open');
  arrow.classList.toggle('rotate-90');
}

// ── Tool Selection ─────────────────────────────────────────────────
async function selectTool(category, name) {
  document.getElementById('empty-state').classList.add('hidden');
  document.getElementById('tool-detail').classList.remove('hidden');
  document.getElementById('result-section').classList.add('hidden');

  const detail = await fetchToolDetail(category, name);
  state.selected = { ...detail, category };

  document.getElementById('tool-name').textContent = detail.name;
  document.getElementById('tool-category').textContent = category;
  document.getElementById('tool-desc').textContent = detail.description || '';

  const appBadge = document.getElementById('tool-app-badge');
  if (state.apps.has(name)) {
    appBadge.classList.remove('hidden');
  } else {
    appBadge.classList.add('hidden');
  }

  renderForm(detail.input_schema);
  renderSidebar(document.getElementById('search').value);
}

// ── Schema Form Generator ──────────────────────────────────────────
function renderForm(schema) {
  const form = document.getElementById('tool-form');
  if (!schema || !schema.properties || Object.keys(schema.properties).length === 0) {
    form.innerHTML = '<p class="text-sm text-slate-400">No parameters required</p>';
    return;
  }

  const required = new Set(schema.required || []);
  let html = '';

  for (const [name, prop] of Object.entries(schema.properties)) {
    const isRequired = required.has(name);
    const label = `${name}${isRequired ? ' <span class="text-red-500">*</span>' : ''}`;
    const desc = prop.description ? `<p class="text-xs text-slate-400 mt-1">${escapeHtml(prop.description)}</p>` : '';

    html += `<div>
      <label class="block text-sm font-medium text-slate-700 mb-1">${label}</label>
      ${generateInput(name, prop, isRequired)}
      ${desc}
    </div>`;
  }

  form.innerHTML = html;
}

function generateInput(name, prop, isRequired) {
  const reqAttr = isRequired ? 'required' : '';
  const defaultVal = prop.default !== undefined && prop.default !== null ? prop.default : '';

  // Enum -> select
  if (prop.enum) {
    const options = prop.enum.map(v =>
      `<option value="${escapeHtml(String(v))}" ${v === defaultVal ? 'selected' : ''}>${escapeHtml(String(v))}</option>`
    ).join('');
    return `<select name="${name}" ${reqAttr}
              class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white">
              <option value="">-- select --</option>${options}</select>`;
  }

  const type = prop.type || 'string';

  if (type === 'boolean') {
    const checked = defaultVal === true ? 'checked' : '';
    return `<label class="flex items-center gap-2">
      <input type="checkbox" name="${name}" ${checked}
             class="w-4 h-4 rounded border-slate-300 text-sky-600" />
      <span class="text-sm text-slate-600">${name}</span>
    </label>`;
  }

  if (type === 'integer') {
    return `<input type="number" name="${name}" step="1" value="${escapeHtml(String(defaultVal))}" ${reqAttr}
              class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg" />`;
  }

  if (type === 'number') {
    return `<input type="number" name="${name}" step="any" value="${escapeHtml(String(defaultVal))}" ${reqAttr}
              class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg" />`;
  }

  if (type === 'array' || type === 'object') {
    const placeholder = type === 'array' ? '["item1", "item2"]' : '{"key": "value"}';
    return `<textarea name="${name}" rows="3" placeholder="${placeholder}" ${reqAttr}
              class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg font-mono">${escapeHtml(String(defaultVal))}</textarea>`;
  }

  // String: use textarea for long-form fields
  const longFields = ['content', 'body', 'query', 'sql', 'text', 'description', 'prompt', 'message', 'code'];
  if (longFields.includes(name.toLowerCase())) {
    return `<textarea name="${name}" rows="4" ${reqAttr}
              class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg">${escapeHtml(String(defaultVal))}</textarea>`;
  }

  return `<input type="text" name="${name}" value="${escapeHtml(String(defaultVal))}" ${reqAttr}
            class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg" />`;
}

// ── Execution ──────────────────────────────────────────────────────
document.getElementById('execute-btn').addEventListener('click', async () => {
  if (!state.selected) return;

  const btn = document.getElementById('execute-btn');
  const resultSection = document.getElementById('result-section');
  const resultContainer = document.getElementById('result-container');

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Executing...';
  resultSection.classList.remove('hidden');
  resultContainer.innerHTML = '<div class="p-4 text-sm text-slate-400">Running...</div>';

  try {
    const params = collectFormData();
    const result = await executeTool(state.selected.name, params);

    if (state.apps.has(state.selected.name)) {
      await renderWithApp(state.selected.name, result);
    } else {
      renderJson(result, resultContainer);
    }
  } catch (err) {
    resultContainer.innerHTML = `<div class="p-4 text-sm text-red-600 bg-red-50">${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Execute';
  }
});

function collectFormData() {
  const form = document.getElementById('tool-form');
  const schema = state.selected.input_schema;
  if (!schema || !schema.properties) return {};

  const params = {};
  for (const [name, prop] of Object.entries(schema.properties)) {
    const type = prop.type || 'string';

    if (type === 'boolean') {
      const el = form.querySelector(`[name="${name}"]`);
      if (el) params[name] = el.checked;
      continue;
    }

    const el = form.querySelector(`[name="${name}"]`);
    if (!el) continue;
    const val = el.value.trim();
    if (val === '') continue;

    if (type === 'integer') {
      params[name] = parseInt(val, 10);
    } else if (type === 'number') {
      params[name] = parseFloat(val);
    } else if (type === 'array' || type === 'object') {
      try { params[name] = JSON.parse(val); } catch { params[name] = val; }
    } else {
      params[name] = val;
    }
  }
  return params;
}

// ── MCP App Renderer ───────────────────────────────────────────────
async function renderWithApp(toolName, result) {
  const container = document.getElementById('result-container');
  const html = await fetchAppHtml(toolName);

  if (!html) {
    renderJson(result, container);
    return;
  }

  const iframe = document.createElement('iframe');
  iframe.id = 'app-iframe';
  iframe.sandbox = 'allow-scripts';
  container.innerHTML = '';
  container.appendChild(iframe);

  // Wait for iframe to signal ready, then send data
  const handler = (event) => {
    if (event.source !== iframe.contentWindow) return;
    const msg = event.data;
    if (!msg || typeof msg !== 'object') return;

    // MCP JSON-RPC: ui/ready
    if (msg.jsonrpc === '2.0' && msg.method === 'ui/ready') {
      window.removeEventListener('message', handler);

      // Send ui/initialize
      iframe.contentWindow.postMessage({
        jsonrpc: '2.0',
        id: 1,
        method: 'ui/initialize',
        params: { protocolVersion: '0.1.0' },
      }, '*');

      // Send tool result as MCP content format
      const toolResult = resultToMcpContent(result);
      iframe.contentWindow.postMessage({
        jsonrpc: '2.0',
        method: 'ui/toolResult',
        params: toolResult,
      }, '*');

      // Also send simple format for REST delivery
      iframe.contentWindow.postMessage({
        type: 'toolResult',
        data: result.result || result,
      }, '*');
    }
  };

  window.addEventListener('message', handler);
  iframe.srcdoc = html;
}

function resultToMcpContent(result) {
  const data = result.result || result;
  return {
    content: [{ type: 'text', text: JSON.stringify(data) }],
  };
}

// ── JSON Renderer ──────────────────────────────────────────────────
function renderJson(data, container) {
  container.innerHTML = `<pre class="p-4 text-sm font-mono overflow-x-auto bg-slate-50">${syntaxHighlight(data)}</pre>`;
}

function syntaxHighlight(obj) {
  const json = JSON.stringify(obj, null, 2);
  return json.replace(
    /("(\\\\u[a-zA-Z0-9]{4}|\\\\[^u]|[^\\\\"])*"(\\s*:)?|\\b(true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)/g,
    (match) => {
      let cls = 'json-number';
      if (/^"/.test(match)) {
        cls = /:$/.test(match) ? 'json-key' : 'json-string';
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean';
      } else if (/null/.test(match)) {
        cls = 'json-null';
      }
      return `<span class="${cls}">${escapeHtml(match)}</span>`;
    }
  );
}

// ── Utils ──────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Init ───────────────────────────────────────────────────────────
async function init() {
  try {
    const [toolsData, appsData] = await Promise.all([fetchTools(), fetchApps()]);

    // Build state
    state.tools = {};
    for (const [category, info] of Object.entries(toolsData.categories || {})) {
      state.tools[category] = info.tools || [];
    }

    for (const app of (appsData.apps || [])) {
      state.apps.add(app.tool_name);
    }

    // Update count
    document.getElementById('tool-count').textContent = `${toolsData.total_tools || 0} tools`;

    renderSidebar();
  } catch (err) {
    document.getElementById('sidebar').innerHTML =
      `<div class="p-4 text-sm text-red-500">Failed to load tools: ${escapeHtml(err.message)}</div>`;
  }
}

// Search handler
document.getElementById('search').addEventListener('input', (e) => {
  renderSidebar(e.target.value);
});

init();
</script>
</body>
</html>"""
