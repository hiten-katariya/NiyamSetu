import { ApiErrorResponse, ApiResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: Array<{ field?: string; message: string }>;

  constructor(status: number, errorData: ApiErrorResponse['error']) {
    super(errorData.message || 'An API error occurred');
    this.name = 'ApiClientError';
    this.status = status;
    this.code = errorData.code || 'API_ERROR';
    this.details = errorData.details;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const token = localStorage.getItem('niyamsetu_token');
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
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

  const json: ApiResponse<T> = await response.json();
  return json.data;
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
};
