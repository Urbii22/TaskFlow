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

// Factoría opcional para crear un cliente con apiBase preconfigurado
export function createApiClient({ apiBase = DEFAULT_API_BASE } = {}) {
  return {
    getBoards: (token) => getBoards(token, { apiBase }),
    getBoardColumns: (boardId, token) => getBoardColumns(boardId, token, { apiBase }),
    getTasksByColumn: (columnId, token) => getTasksByColumn(columnId, token, { apiBase }),
  };
}


