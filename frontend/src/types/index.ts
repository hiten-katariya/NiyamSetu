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


export interface NotificationItem {
  id: string;
  recipient_user_id: string;
  application_id?: string | null;
  target_type: string;
  target_id: string;
  channel: string;
  title: string;
  body: string;
  status: 'unread' | 'read' | 'acknowledged';
  sent_at: string;
  read_at?: string | null;
  created_at: string;
}

export interface EscalationItem {
  id: string;
  application_id?: string | null;
  target_type: string;
  target_id: string;
  level: number;
  assigned_to_user_id?: string | null;
  assigned_to_name?: string | null;
  status: 'open' | 'resolved';
  triggered_at: string;
  resolved_at?: string | null;
  resolution_notes?: string | null;
  application_number?: string | null;
  institution_name?: string | null;
}

export interface AttentionItem {
  id: string;
  application_number: string;
  institution_name: string;
  current_stage_name: string;
  status: 'overdue' | 'due_soon' | 'on_hold' | 'returned';
  reason: string;
  days_in_stage: number;
  due_date?: string | null;
  priority: 'critical' | 'high' | 'medium' | 'normal';
}

export interface PendencyMetrics {
  total_pending: number;
  by_stage: Record<string, number>;
  by_region: Record<string, number>;
  overdue_count: number;
  on_hold_count: number;
  due_soon_count: number;
}

export interface AgeingMetric {
  stage_name: string;
  under_7_days: number;
  between_7_14_days: number;
  over_14_days: number;
}

// ==========================================
// Phase 5: EVC, Undertakings & Documents
// ==========================================

export interface EVCMemberItem {
  id: string;
  evc_id: string;
  user_id?: string | null;
  role_in_committee: string;
  name: string;
  designation?: string | null;
  assigned_at: string;
}

export interface EVCReportItem {
  id: string;
  evc_id: string;
  report_number: string;
  recommendation: 'recommended' | 'recommended_with_conditions' | 'not_recommended';
  key_observations?: string | null;
  file_id: string;
  submitted_by_id: string;
  submitted_at: string;
  reviewed_by_id?: string | null;
  reviewed_at?: string | null;
  review_status: 'pending_review' | 'accepted' | 'returned_for_correction';
  review_notes?: string | null;
}

export interface EVCItem {
  id: string;
  application_id: string;
  status: 'queued' | 'scheduled' | 'rescheduled' | 'conducted' | 'report_submitted' | 'completed' | 'cancelled';
  scheduled_date?: string | null;
  rescheduled_date?: string | null;
  reschedule_reason?: string | null;
  visit_mode: 'physical' | 'hybrid' | 'virtual';
  conducted_date?: string | null;
  visit_summary?: string | null;
  created_at: string;
  updated_at: string;
  application_number?: string | null;
  institution_name?: string | null;
  members: EVCMemberItem[];
  reports: EVCReportItem[];
}

export interface UndertakingSubmissionItem {
  id: string;
  undertaking_id: string;
  submitted_by_id: string;
  file_id?: string | null;
  remarks?: string | null;
  status: 'submitted' | 'accepted' | 'rejected' | 'returned_for_correction';
  reviewed_by_id?: string | null;
  review_comments?: string | null;
  submitted_at: string;
  reviewed_at?: string | null;
}

export interface UndertakingItem {
  id: string;
  application_id?: string | null;
  institution_id: string;
  condition_title: string;
  condition_description?: string | null;
  status: 'pending' | 'submitted' | 'fulfilled' | 'overdue' | 'returned';
  due_date: string;
  fulfilled_date?: string | null;
  created_at: string;
  updated_at: string;
  institution_name?: string | null;
  application_number?: string | null;
  submissions: UndertakingSubmissionItem[];
}

export interface DocumentRenewalItem {
  id: string;
  document_id: string;
  renewal_status: 'initiated' | 'in_progress' | 'completed' | 'cancelled';
  initiated_at: string;
  completed_at?: string | null;
  replacement_document_id?: string | null;
  remarks?: string | null;
}

export interface DocumentItem {
  id: string;
  institution_id: string;
  application_id?: string | null;
  file_id: string;
  document_type: string;
  title: string;
  document_number?: string | null;
  issuing_authority?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  status: 'pending_verification' | 'verified' | 'rejected' | 'expired' | 'renewal_pending';
  verified_by_id?: string | null;
  verified_at?: string | null;
  verification_notes?: string | null;
  created_at: string;
  updated_at: string;
  institution_name?: string | null;
  application_number?: string | null;
  original_filename?: string | null;
  file_size_bytes?: number | null;
  is_expired: boolean;
  is_expiring_soon: boolean;
  renewals: DocumentRenewalItem[];
}

// ==========================================
// Phase 6: Analytics, Reporting & Administration
// ==========================================

export interface VolumeTrendPoint {
  date: string;
  submitted: number;
  completed: number;
}

export interface RegionalMetricItem {
  region_id?: string | null;
  region_name: string;
  total_applications: number;
  in_progress: number;
  overdue: number;
  completed: number;
}

export interface EVCAnalyticsResponse {
  scheduled_count: number;
  conducted_count: number;
  pending_reports: number;
  reviewed_reports: number;
  recommended_count: number;
  conditions_count: number;
  not_recommended_count: number;
}

export interface UndertakingAnalyticsResponse {
  total_conditions: number;
  pending_evidence: number;
  submitted_under_review: number;
  fulfilled: number;
  overdue: number;
  returned: number;
}

export interface DocumentAnalyticsResponse {
  valid_count: number;
  expiring_soon_count: number;
  expired_count: number;
  pending_verification_count: number;
  renewals_in_progress: number;
}

export interface OperationalSummaryResponse {
  open_escalations: number;
  resolved_escalations: number;
  unread_notifications: number;
  total_notifications: number;
  worker_status: string;
  last_scan_at?: string | null;
  failure_count: number;
}

export interface ReportColumn {
  key: string;
  label: string;
}

export interface ReportTypeInfo {
  code: string;
  name: string;
  description: string;
  supported_filters: string[];
}

export interface ReportPreviewResponse {
  report_type: string;
  report_title: string;
  generated_at: string;
  columns: ReportColumn[];
  rows: Array<Record<string, unknown>>;
  total_rows: number;
  page: number;
  page_size: number;
}

export interface ReminderRuleItem {
  id: string;
  name: string;
  target_type: string;
  days_before_due: number;
  recipient_roles: string[];
  is_active: boolean;
}

export interface EscalationRuleItem {
  id: string;
  name: string;
  target_type: string;
  level: number;
  days_after_due: number;
  recipient_roles: string[];
  is_active: boolean;
}

export interface HolidayItem {
  id: string;
  region_id?: string | null;
  holiday_date: string;
  name: string;
  created_at: string;
}

export interface MessageTemplateItem {
  id: string;
  code: string;
  channel: string;
  subject_template: string;
  body_template: string;
  is_active: boolean;
  updated_at: string;
}

export interface ConfigVersionItem {
  id: string;
  config_type: string;
  version: number;
  changed_by_user_id?: string | null;
  change_summary: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  actor_user_id?: string | null;
  actor_name?: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  occurred_at: string;
  ip_address?: string | null;
  metadata_?: Record<string, unknown> | null;
  entry_hash: string;
}

export interface AuditVerificationResponse {
  is_valid: boolean;
  verified_count: number;
  error_message?: string | null;
}

export interface SchedulerRunItem {
  id: string;
  job_name: string;
  started_at: string;
  finished_at?: string | null;
  status: string;
  items_scanned: number;
  items_processed: number;
  duration_seconds?: number | null;
  error_summary?: string | null;
}

export interface WorkerMonitoringResponse {
  status: string;
  last_run?: SchedulerRunItem | null;
  last_successful_run?: SchedulerRunItem | null;
  latest_failed_run?: SchedulerRunItem | null;
  recent_runs: SchedulerRunItem[];
  total_runs: number;
  success_runs: number;
  failed_runs: number;
}

export interface NotificationMonitoringResponse {
  unread_count: number;
  read_count: number;
  acknowledged_count: number;
  total_count: number;
}


