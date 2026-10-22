export type UserRole =
  | 'institution_user'
  | 'scrutiny_officer'
  | 'regional_officer'
  | 'bureau_officer'
  | 'committee_member'
  | 'senior_authority'
  | 'system_admin'
  | 'admin';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  region_id?: string | null;
  institution_id?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PermittedScope {
  scope_type: string;
  region_id?: string | null;
  institution_id?: string | null;
  assigned_committees: string[];
  all_regions: boolean;
  all_institutions: boolean;
}

export interface UserProfile {
  user: User;
  permissions: string[];
  permitted_scope: PermittedScope;
}

export interface LoginResponse {
  message: string;
  csrf_token: string;
  user: User;
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

export interface RouteStage {
  id: string;
  route_type_id: string;
  route_version: number;
  stage_code: string;
  stage_name: string;
  sequence: number;
  required_role: string;
  timeline_days: number;
  day_type: string;
  is_required: boolean;
}

export interface RouteType {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
  current_version: number;
  stages: RouteStage[];
}

export interface StageHistory {
  id: string;
  application_id: string;
  from_stage_id?: string | null;
  from_stage_name?: string | null;
  to_stage_id?: string | null;
  to_stage_name?: string | null;
  action: string;
  reason?: string | null;
  performed_by_user_id: string;
  performed_by_name?: string | null;
  performed_at: string;
  metadata?: Record<string, unknown> | null;
}

export interface ApplicationItem {
  id: string;
  reference_no: string;
  institution_id: string;
  institution_name?: string | null;
  institution_code?: string | null;
  route_type_id: string;
  route_name?: string | null;
  route_code?: string | null;
  route_version: number;
  current_stage_id?: string | null;
  current_stage_name?: string | null;
  current_stage_code?: string | null;
  current_stage_role?: string | null;
  current_stage_sequence?: number | null;
  total_stages?: number | null;
  status: string;
  assigned_to_user_id?: string | null;
  assigned_to_name?: string | null;
  submitted_at?: string | null;
  stage_entered_at?: string | null;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationDetail extends ApplicationItem {
  stages: RouteStage[];
  history: StageHistory[];
  available_actions: string[];
}
