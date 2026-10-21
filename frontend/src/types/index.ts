export type UserRole =
  | 'institution_user'
  | 'scrutiny_officer'
  | 'regional_officer'
  | 'bureau_officer'
  | 'committee_member'
  | 'senior_authority'
  | 'system_admin';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  region_id?: string | null;
  institution_id?: string | null;
  is_active: boolean;
}

export interface ApiResponse<T> {
  data: T;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Array<{ field?: string; message: string }>;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export interface HealthCheckData {
  status: string;
  timestamp: string;
  environment: string;
  version: string;
}

export interface ReadinessCheckData {
  status: string;
  timestamp: string;
  environment: string;
  database: {
    status: string;
    details: string;
  };
  worker: {
    status: string;
    details: string;
  };
}

export interface DashboardMetrics {
  total_applications: number;
  in_progress: number;
  pending_scrutiny: number;
  pending_evc: number;
  pending_undertakings: number;
  overdue_items: number;
  completed_this_cycle: number;
  is_demo_data: boolean;
}

export interface ApplicationItem {
  id: string;
  reference_no: string;
  institution_id: string;
  route_type_id: string;
  route_version: number;
  current_stage_id?: string | null;
  status: string;
  submitted_at?: string | null;
  stage_entered_at?: string | null;
}
