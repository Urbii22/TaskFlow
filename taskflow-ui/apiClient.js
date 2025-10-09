// Pequeño cliente de API para TaskFlow UI
// Exporta funciones para consumir la API protegida con Bearer Token

const DEFAULT_API_BASE = "/api/v1";

function buildHeaders(token) {
  const headers = new Headers();
  headers.set("Accept", "application/json");
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return headers;
}

async function request(path, token, init = {}, apiBase = DEFAULT_API_BASE) {
  const url = `${apiBase}${path}`;
  const resp = await fetch(url, {
    method: "GET",
    mode: "cors",
    ...init,
    headers: {
      ...Object.fromEntries(buildHeaders(token).entries()),
      ...(init.headers || {}),
    },
  });
  if (!resp.ok) {
    const errorText = await resp.text().catch(() => "");
    const err = new Error(`Error ${resp.status} ${resp.statusText}: ${errorText}`.trim());
    err.status = resp.status;
    throw err;
  }
  return resp.json();
}

// Obtiene lista paginada de tableros del usuario
export async function getBoards(token, { apiBase } = {}) {
  return request(`/boards/`, token, {}, apiBase);
}

// Obtiene columnas de un tablero (lista paginada)
export async function getBoardColumns(boardId, token, { apiBase } = {}) {
  if (boardId == null) throw new Error("boardId es requerido");
  return request(`/boards/${encodeURIComponent(boardId)}/columns`, token, {}, apiBase);
}

// Obtiene tareas de una columna (lista paginada)
export async function getTasksByColumn(columnId, token, { apiBase } = {}) {
  if (columnId == null) throw new Error("columnId es requerido");
  return request(`/columns/${encodeURIComponent(columnId)}/tasks`, token, {}, apiBase);
}

// Crear tablero
export async function createBoard(name, token, { apiBase } = {}) {
  if (!name) throw new Error("name es requerido");
  return request(`/boards/`, token, {
    method: "POST",
    body: JSON.stringify({ name }),
  }, apiBase);
}

// Crear columna
export async function createColumn(boardId, name, position, token, { apiBase } = {}) {
  if (boardId == null) throw new Error("boardId es requerido");
  if (!name) throw new Error("name es requerido");
  if (position == null) throw new Error("position es requerido");
  return request(`/columns/`, token, {
    method: "POST",
    body: JSON.stringify({ board_id: boardId, name, position }),
  }, apiBase);
}

// Crear tarea
export async function createTask(columnId, title, description, priority, token, { apiBase } = {}) {
  if (columnId == null) throw new Error("columnId es requerido");
  if (!title) throw new Error("title es requerido");
  if (!priority) throw new Error("priority es requerido");
  const body = { column_id: columnId, title, priority };
  if (description != null) body.description = description;
  return request(`/tasks/`, token, {
    method: "POST",
    body: JSON.stringify(body),
  }, apiBase);
}

// Actualizar tarea
export async function updateTask(taskId, data, token, { apiBase } = {}) {
  if (taskId == null) throw new Error("taskId es requerido");
  if (!data || typeof data !== "object") throw new Error("data inválido");
  return request(`/tasks/${encodeURIComponent(taskId)}`, token, {
    method: "PATCH",
    body: JSON.stringify(data),
  }, apiBase);
}

// Eliminar tarea
export async function deleteTask(taskId, token, { apiBase } = {}) {
  if (taskId == null) throw new Error("taskId es requerido");
  return request(`/tasks/${encodeURIComponent(taskId)}`, token, {
    method: "DELETE",
  }, apiBase);
}

// Registro de usuario
export async function register(email, password, { apiBase } = {}) {
  if (!email) throw new Error("email es requerido");
  if (!password) throw new Error("password es requerido");
  return request(`/auth/register`, undefined, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }, apiBase);
}

// Factoría opcional para crear un cliente con apiBase preconfigurado
export function createApiClient({ apiBase = DEFAULT_API_BASE } = {}) {
  return {
    getBoards: (token) => getBoards(token, { apiBase }),
    getBoardColumns: (boardId, token) => getBoardColumns(boardId, token, { apiBase }),
    getTasksByColumn: (columnId, token) => getTasksByColumn(columnId, token, { apiBase }),
    createBoard: (name, token) => createBoard(name, token, { apiBase }),
    createColumn: (boardId, name, position, token) => createColumn(boardId, name, position, token, { apiBase }),
    createTask: (columnId, title, description, priority, token) => createTask(columnId, title, description, priority, token, { apiBase }),
    updateTask: (taskId, data, token) => updateTask(taskId, data, token, { apiBase }),
    deleteTask: (taskId, token) => deleteTask(taskId, token, { apiBase }),
    register: (email, password) => register(email, password, { apiBase }),
  };
}


