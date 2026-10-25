import { ApiErrorResponse, PaginatedResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: Array<{ field?: string; message: string }>;

  constructor(status: number, errorData: ApiErrorResponse['error']) {
    let msg = errorData.message || 'An API error occurred';
    if (errorData.details && errorData.details.length > 0) {
      const fieldDetails = errorData.details
        .map((d) => (d.field && d.field !== 'request' ? `${d.field}: ${d.message}` : d.message))
        .join('; ');
      msg = `${msg}: ${fieldDetails}`;
    }
    super(msg);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = errorData.code || 'API_ERROR';
    this.details = errorData.details;
  }
}

/**
 * Extracts a cookie value by name from document.cookie safely.
 */
export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3]) : null;
}

/**
 * Ensures a CSRF cookie exists before state-changing operations.
 */
async function ensureCsrfToken(): Promise<string | null> {
  let token = getCookie('niyamsetu_csrf');
  if (!token) {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/csrf`, {
        method: 'GET',
        credentials: 'include',
      });
      if (res.ok) {
        const json = await res.json();
        token = json.data?.csrf_token || getCookie('niyamsetu_csrf');
      }
    } catch {
      // Best effort; backend will reject if token is strictly required
    }
  }
  return token;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  // Attach Anti-CSRF token for state-changing HTTP methods
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    let csrfToken = getCookie('niyamsetu_csrf');
    if (!csrfToken) {
      csrfToken = await ensureCsrfToken();
    }
    if (csrfToken && !headers.has('X-CSRF-Token')) {
      headers.set('X-CSRF-Token', csrfToken);
    }
  }

  // Always include HTTP credentials (cookies) for server-side session management
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers,
  });

  if (!response.ok) {
    let errorData: ApiErrorResponse['error'] = {
      code: `HTTP_${response.status}`,
      message: response.statusText || 'Request failed',
    };
    try {
      const parsed = await response.json();
      if (parsed.error) {
        errorData = parsed.error;
      }
    } catch {
      // Non-JSON response
    }
    throw new ApiClientError(response.status, errorData);
  }

  if (response.status === 204) {
    return {} as T;
  }

  const json = await response.json();
  if (json && typeof json === 'object' && 'data' in json) {
    return json.data as T;
  }
  return json as T;
}

export async function apiRequestPaginated<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<PaginatedResponse<T>> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const headers = new Headers(options.headers || {});

  const response = await fetch(url, {
    ...options,
    method: 'GET',
    credentials: 'include',
    headers,
  });

  if (!response.ok) {
    let errorData: ApiErrorResponse['error'] = {
      code: `HTTP_${response.status}`,
      message: response.statusText || 'Request failed',
    };
    try {
      const parsed = await response.json();
      if (parsed.error) {
        errorData = parsed.error;
      }
    } catch {
      // Non-JSON response
    }
    throw new ApiClientError(response.status, errorData);
  }

  const json = await response.json();
  const data = Array.isArray(json?.data) ? json.data : (Array.isArray(json) ? json : []);
  const meta = json?.meta || {
    page: 1,
    page_size: data.length,
    total: data.length,
    total_pages: 1,
  };
  return { data, meta };
}

export async function downloadFile(endpoint: string, defaultFilename = 'download'): Promise<void> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const response = await fetch(url, {
    method: 'GET',
    credentials: 'include',
  });
  if (!response.ok) {
    let errorMsg = `Download failed with status ${response.status}`;
    try {
      const err = await response.json();
      if (err.error?.message) errorMsg = err.error.message;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  const blob = await response.blob();
  const disposition = response.headers.get('Content-Disposition');
  let filename = defaultFilename;
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) filename = match[1];
  }
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),
  getPaginated: <T>(endpoint: string, options?: RequestInit) =>
    apiRequestPaginated<T>(endpoint, options),
  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  postForm: <T>(endpoint: string, formData: FormData, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
    }),
  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};
