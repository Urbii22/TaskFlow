import { getBoards, getBoardColumns, getTasksByColumn, createBoard, createColumn, createTask, updateTask, deleteTask, register } from './apiClient.js';

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

// Estado actual del tablero cargado
let currentBoardId = null;
let currentColumns = [];
let draggedTask = null;

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('hidden');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('hidden');
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
    const createColumnBtn = $('#create-column-btn');
    if (createColumnBtn) createColumnBtn.disabled = false;
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

    // Guardar estado actual
    currentBoardId = boardId;
    currentColumns = columnsWithTasks;

    // Limpiar el placeholder de carga antes de renderizar
    container.innerHTML = '';

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
      <div class="flex items-center gap-2">
        <span class="task-count text-xs text-slate-500">${Array.isArray(col.tasks) ? col.tasks.length : 0} tareas</span>
        <button type="button" class="add-task-btn rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 shadow-sm hover:bg-slate-50" data-column-id="${col.id}">+ Tarea</button>
      </div>
    `;
    colEl.appendChild(header);

    const list = document.createElement('div');
    list.className = 'space-y-2 min-h-[20px]';
    list.dataset.columnId = String(col.id);
    // DnD targets: permitir soltar
    list.addEventListener('dragover', (e) => {
      e.preventDefault();
      list.classList.add('ring-2', 'ring-indigo-300');
    });
    list.addEventListener('dragleave', () => {
      list.classList.remove('ring-2', 'ring-indigo-300');
    });
    list.addEventListener('drop', async (e) => {
      e.preventDefault();
      list.classList.remove('ring-2', 'ring-indigo-300');
      if (!draggedTask) return;
      const taskId = draggedTask.dataset.taskId;
      const fromColumnId = draggedTask.dataset.columnId;
      const toColumnId = list.dataset.columnId;
      if (!taskId || !toColumnId || toColumnId === fromColumnId) return;
      const token = getToken();
      if (!token) return;
      try {
        await updateTask(Number(taskId), { column_id: Number(toColumnId) }, token, { apiBase: getApiBase() });
        // Mover DOM de forma optimista
        const fromList = draggedTask.parentElement;
        list.appendChild(draggedTask);
        draggedTask.dataset.columnId = String(toColumnId);
        // Actualizar contadores
        const toColEl = list.closest('.rounded-lg.border.border-slate-200.bg-white.p-4.shadow-sm');
        const fromColEl = fromList?.closest('.rounded-lg.border.border-slate-200.bg-white.p-4.shadow-sm');
        const toCount = toColEl?.querySelector('.task-count');
        const fromCount = fromColEl?.querySelector('.task-count');
        if (toCount) toCount.textContent = `${list.querySelectorAll('.task-card').length} tareas`;
        if (fromCount && fromList) fromCount.textContent = `${fromList.querySelectorAll('.task-card').length} tareas`;
      } catch (err) {
        alert(err?.message ?? String(err));
      }
    });
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
  card.className = `${base} ${border} task-card cursor-pointer`;
  card.setAttribute('draggable', 'true');
  card.dataset.taskId = String(task.id);
  card.dataset.columnId = String(task.column_id);
  card.dataset.title = task.title;
  if (task.description != null) card.dataset.description = task.description;
  card.dataset.priority = task.priority;
  card.innerHTML = `
    <div class="text-sm font-medium text-slate-800">${task.title}</div>
    <div class="mt-1 text-xs text-slate-600">Prioridad: ${task.priority}</div>
  `;
  // Drag events
  card.addEventListener('dragstart', (e) => {
    draggedTask = card;
    card.classList.add('opacity-50');
  });
  card.addEventListener('dragend', () => {
    if (draggedTask === card) draggedTask = null;
    card.classList.remove('opacity-50');
  });
  return card;
}

function attachKanbanListeners() {
  const kanban = $('#kanban-container');
  if (!kanban) return;
  kanban.addEventListener('click', (e) => {
    const card = e.target.closest('.task-card');
    if (card) {
      const taskId = card.dataset.taskId;
      const columnId = card.dataset.columnId;
      const title = card.dataset.title || '';
      const description = card.dataset.description || '';
      const priority = card.dataset.priority || 'MEDIUM';
      // Prefill modal for edit
      $('#task-modal-title').textContent = 'Editar tarea';
      $('#task-id-input').value = String(taskId);
      $('#task-column-id-input').value = String(columnId);
      $('#task-title-input').value = title;
      $('#task-desc-input').value = description;
      $('#task-priority-input').value = priority;
      $('#task-delete-btn').classList.remove('hidden');
      openModal('task-modal');
      return;
    }
    const addBtn = e.target.closest('.add-task-btn');
    if (addBtn) {
      const columnId = addBtn.getAttribute('data-column-id');
      $('#task-modal-title').textContent = 'Crear tarea';
      $('#task-id-input').value = '';
      $('#task-column-id-input').value = String(columnId);
      $('#task-title-input').value = '';
      $('#task-desc-input').value = '';
      $('#task-priority-input').value = 'MEDIUM';
      $('#task-delete-btn').classList.add('hidden');
      openModal('task-modal');
    }
  });
}

function attachModalListeners() {
  // Cerrar por botones data-modal-close
  document.body.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-modal-close]');
    if (btn) closeModal(btn.getAttribute('data-modal-close'));
  });

  const createBoardBtn = $('#create-board-btn');
  if (createBoardBtn) {
    createBoardBtn.addEventListener('click', () => {
      $('#board-name-input').value = '';
      openModal('board-modal');
    });
  }

  const createColumnBtn = $('#create-column-btn');
  if (createColumnBtn) {
    createColumnBtn.addEventListener('click', () => {
      const selector = $('#board-selector');
      const boardId = selector?.value;
      if (!boardId) return;
      $('#column-board-id-input').value = String(boardId);
      const defaultPos = Array.isArray(currentColumns) ? currentColumns.length : 0;
      $('#column-position-input').value = String(defaultPos);
      $('#column-name-input').value = '';
      openModal('column-modal');
    });
  }

  const boardForm = $('#board-form');
  if (boardForm) {
    boardForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const token = getToken();
      if (!token) return;
      const name = $('#board-name-input').value.trim();
      try {
        await createBoard(name, token, { apiBase: getApiBase() });
        closeModal('board-modal');
        await initializeDashboard();
      } catch (err) {
        alert(err?.message ?? String(err));
      }
    });
  }

  const columnForm = $('#column-form');
  if (columnForm) {
    columnForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const token = getToken();
      if (!token) return;
      const boardId = Number($('#column-board-id-input').value);
      const name = $('#column-name-input').value.trim();
      const position = Number($('#column-position-input').value);
      try {
        await createColumn(boardId, name, position, token, { apiBase: getApiBase() });
        closeModal('column-modal');
        await loadBoard(boardId);
      } catch (err) {
        alert(err?.message ?? String(err));
      }
    });
  }

  const taskForm = $('#task-form');
  const deleteBtn = $('#task-delete-btn');
  if (taskForm) {
    taskForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const token = getToken();
      if (!token) return;
      const taskId = $('#task-id-input').value;
      const columnId = Number($('#task-column-id-input').value);
      const title = $('#task-title-input').value.trim();
      const description = $('#task-desc-input').value;
      const priority = $('#task-priority-input').value;
      try {
        if (taskId) {
          await updateTask(Number(taskId), { title, description, priority, column_id: columnId }, token, { apiBase: getApiBase() });
        } else {
          await createTask(columnId, title, description, priority, token, { apiBase: getApiBase() });
        }
        closeModal('task-modal');
        await loadBoard(currentBoardId ?? Number($('#board-selector').value));
      } catch (err) {
        alert(err?.message ?? String(err));
      }
    });
  }
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async () => {
      const token = getToken();
      if (!token) return;
      const taskId = $('#task-id-input').value;
      if (!taskId) return;
      if (!confirm('¿Eliminar esta tarea?')) return;
      try {
        await deleteTask(Number(taskId), token, { apiBase: getApiBase() });
        closeModal('task-modal');
        await loadBoard(currentBoardId ?? Number($('#board-selector').value));
      } catch (err) {
        alert(err?.message ?? String(err));
      }
    });
  }
}

function attachBoardSelectorListener() {
  const selector = $('#board-selector');
  if (!selector) return;
  selector.addEventListener('change', async (e) => {
    const value = e.target.value;
    if (value) await loadBoard(value);
    const btn = $('#create-column-btn');
    if (btn) btn.disabled = !value;
  });
}

function attachAuthListeners() {
  const form = document.querySelector('#login-form');
  const emailInput = document.querySelector('#email-input');
  const passwordInput = document.querySelector('#password-input');
  const errorBox = document.querySelector('#login-error');
  const logoutBtn = document.querySelector('#logout-btn');
  const openRegisterBtn = document.querySelector('#open-register-btn');
  const registerForm = document.querySelector('#register-form');
  const registerEmailInput = document.querySelector('#register-email-input');
  const registerPasswordInput = document.querySelector('#register-password-input');
  const registerErrorBox = document.querySelector('#register-error');
  const registerSuccessBox = document.querySelector('#register-success');

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

  if (openRegisterBtn) {
    openRegisterBtn.addEventListener('click', () => {
      if (registerEmailInput) registerEmailInput.value = '';
      if (registerPasswordInput) registerPasswordInput.value = '';
      if (registerErrorBox) { registerErrorBox.textContent = ''; hide(registerErrorBox); }
      if (registerSuccessBox) { registerSuccessBox.textContent = ''; hide(registerSuccessBox); }
      openModal('register-modal');
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (registerErrorBox) { registerErrorBox.textContent = ''; hide(registerErrorBox); }
      if (registerSuccessBox) { registerSuccessBox.textContent = ''; hide(registerSuccessBox); }
      try {
        const email = registerEmailInput?.value?.trim();
        const password = registerPasswordInput?.value;
        await register(email, password, { apiBase: getApiBase() });
        if (registerSuccessBox) {
          registerSuccessBox.textContent = 'Registro exitoso. Iniciando sesión...';
          show(registerSuccessBox);
        }
        // Auto login
        const result = await login(email, password);
        const token = result?.access_token;
        if (!token) throw new Error('Login automático falló');
        try { localStorage.setItem('taskflow_token', token); } catch (_) {}
        closeModal('register-modal');
        hide(document.querySelector('#login-section'));
        show(logoutBtn);
        show(document.querySelector('#empty-state'));
        await initializeDashboard();
      } catch (err) {
        if (registerErrorBox) {
          registerErrorBox.textContent = err?.message ?? String(err);
          show(registerErrorBox);
        } else {
          alert(err?.message ?? String(err));
        }
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
  attachModalListeners();
  attachKanbanListeners();
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


