// All modules must use the same public API endpoint in deployed builds.
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : '/api/v1')
).replace(/\/+$/, '');
