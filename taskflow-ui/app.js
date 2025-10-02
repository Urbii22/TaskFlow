import { getBoards, getBoardColumns, getTasksByColumn } from './apiClient.js';

// Utilidades simples de token; en un caso real vendría de login y storage
function getToken() {
  // Leer desde localStorage si existe
  try {
    const stored = localStorage.getItem('taskflow_token');
    if (stored) return stored;
  } catch (_) {}
  // También permitir lectura desde query param ?token=...
  const url = new URL(window.location.href);
  const qpToken = url.searchParams.get('token');
  if (qpToken) return qpToken;
  return null;
}

async function login(email, password) {
  const apiBase = getApiBase().replace(/\/$/, "");
  const url = `${apiBase}/auth/login`;
  const form = new URLSearchParams();
  form.set('username', email);
  form.set('password', password);
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '');
    throw new Error(`Login falló: ${resp.status} ${resp.statusText} ${txt}`);
  }
  return resp.json();
}

function logout() {
  try { localStorage.removeItem('taskflow_token'); } catch (_) {}
}

function getApiBase() {
  const url = new URL(window.location.href);
  const qpBase = url.searchParams.get('apiBase');
  if (qpBase) return qpBase;
  if (window.__API_BASE__) return window.__API_BASE__;
  return '/api/v1';
}

function $(selector) {
  return document.querySelector(selector);
}

function show(el) {
  el.classList.remove('hidden');
}

function hide(el) {
  el.classList.add('hidden');
}

export async function initializeDashboard() {
  const token = getToken();
  const selector = $('#board-selector');
  const empty = $('#empty-state');
  const container = $('#board-container');

  if (!token) {
    selector.disabled = true;
    container.innerHTML = '<p class="text-sm text-slate-600">Inicia sesión para ver tus tableros.</p>';
    show(empty);
    return;
  }

  selector.disabled = false;
  container.innerHTML = '<p class="text-sm text-slate-600">Cargando tableros...</p>';

  try {
    const page = await getBoards(token, { apiBase: getApiBase() });
    const items = Array.isArray(page?.items) ? page.items : [];

    // Limpiar opciones anteriores excepto la primera placeholder
    selector.innerHTML = '<option value="" disabled selected>Selecciona un tablero</option>';

    if (items.length === 0) {
      show(empty);
      container.innerHTML = '';
      return;
    }

    hide(empty);
    for (const board of items) {
      const opt = document.createElement('option');
      opt.value = String(board.id);
      opt.textContent = board.name;
      selector.appendChild(opt);
    }

    // Autocargar el primero
    selector.value = String(items[0].id);
    await loadBoard(items[0].id);
  } catch (err) {
    container.innerHTML = `<p class="text-sm text-red-600">Error al cargar tableros: ${err?.message ?? err}</p>`;
  }
}

export async function loadBoard(boardId) {
  const token = getToken();
  const container = $('#board-container');
  if (!token) {
    container.innerHTML = '<p class="text-sm text-slate-600">Sin token.</p>';
    return;
  }
  container.innerHTML = '<p class="text-sm text-slate-600">Cargando tablero...</p>';

  try {
    const columnsPage = await getBoardColumns(boardId, token, { apiBase: getApiBase() });
    const columns = Array.isArray(columnsPage?.items) ? columnsPage.items : [];

    const columnsWithTasks = await Promise.all(
      columns.map(async (col) => {
        const tasksPage = await getTasksByColumn(col.id, token, { apiBase: getApiBase() });
        const tasks = Array.isArray(tasksPage?.items) ? tasksPage.items : [];
        return { ...col, tasks };
      })
    );

    // Ordenar columnas por position y tareas por position
    columnsWithTasks.sort((a, b) => (a.position ?? 0) - (b.position ?? 0));
    for (const col of columnsWithTasks) {
      col.tasks.sort((a, b) => (a.position ?? 0) - (b.position ?? 0));
    }

    renderKanbanBoard(columnsWithTasks);
  } catch (err) {
    container.innerHTML = `<p class="text-sm text-red-600">Error al cargar el tablero: ${err?.message ?? err}</p>`;
  }
}

export function renderKanbanBoard(columns) {
  const kanban = $('#kanban-container');
  kanban.innerHTML = '';
  if (!Array.isArray(columns) || columns.length === 0) {
    kanban.innerHTML = '<p class="text-sm text-slate-600">Este tablero no tiene columnas.</p>';
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3';

  for (const col of columns) {
    const colEl = document.createElement('div');
    colEl.className = 'rounded-lg border border-slate-200 bg-white p-4 shadow-sm';

    const header = document.createElement('div');
    header.className = 'mb-3 flex items-center justify-between';
    header.innerHTML = `
      <h3 class="font-semibold text-slate-800">${col.name}</h3>
      <span class="text-xs text-slate-500">${Array.isArray(col.tasks) ? col.tasks.length : 0} tareas</span>
    `;
    colEl.appendChild(header);

    const list = document.createElement('div');
    list.className = 'space-y-2';
    for (const task of col.tasks || []) {
      const card = createTaskCard(task);
      list.appendChild(card);
    }
    colEl.appendChild(list);
    grid.appendChild(colEl);
  }

  kanban.appendChild(grid);
}

export function createTaskCard(task) {
  const card = document.createElement('div');
  const base = 'rounded-md border bg-white p-3 shadow-sm';
  const priorityToBorder = {
    LOW: 'border-slate-200',
    MEDIUM: 'border-blue-200',
    HIGH: 'border-amber-300',
    CRITICAL: 'border-red-400',
  };
  const border = priorityToBorder[task.priority] || 'border-slate-200';
  card.className = `${base} ${border}`;
  card.innerHTML = `
    <div class="text-sm font-medium text-slate-800">${task.title}</div>
    <div class="mt-1 text-xs text-slate-600">Prioridad: ${task.priority}</div>
  `;
  return card;
}

function attachBoardSelectorListener() {
  const selector = $('#board-selector');
  if (!selector) return;
  selector.addEventListener('change', async (e) => {
    const value = e.target.value;
    if (value) await loadBoard(value);
  });
}

function attachAuthListeners() {
  const form = document.querySelector('#login-form');
  const emailInput = document.querySelector('#email-input');
  const passwordInput = document.querySelector('#password-input');
  const errorBox = document.querySelector('#login-error');
  const logoutBtn = document.querySelector('#logout-btn');

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      hide(errorBox);
      errorBox.textContent = '';
      try {
        const result = await login(emailInput.value, passwordInput.value);
        const token = result?.access_token;
        if (!token) throw new Error('Respuesta de login inválida');
        try { localStorage.setItem('taskflow_token', token); } catch (_) {}
        // Toggle UI
        hide(document.querySelector('#login-section'));
        show(logoutBtn);
        show(document.querySelector('#empty-state'));
        await initializeDashboard();
      } catch (err) {
        errorBox.textContent = err?.message ?? String(err);
        show(errorBox);
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      logout();
      show(document.querySelector('#login-section'));
      hide(logoutBtn);
      // Limpiar vistas
      document.querySelector('#board-selector').innerHTML = '<option value="" disabled selected>Selecciona un tablero</option>';
      document.querySelector('#board-container').innerHTML = '';
      document.querySelector('#kanban-container').innerHTML = '';
      show(document.querySelector('#empty-state'));
    });
  }
}

async function render() {
  attachBoardSelectorListener();
  attachAuthListeners();
  const token = getToken();
  if (token) {
    hide(document.querySelector('#login-section'));
    show(document.querySelector('#logout-btn'));
    await initializeDashboard();
  } else {
    show(document.querySelector('#login-section'));
    hide(document.querySelector('#logout-btn'));
  }
}

// Ejecutar render al cargar la página
window.addEventListener('DOMContentLoaded', () => {
  render();
});


