export type UserRole = 'super_admin' | 'tenant_admin' | 'tenant_staff';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  tenant_id: string;
  created_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  subscription_plan: 'basic' | 'pro' | 'enterprise';
  created_at: string;
}

export type VekaletStatus =
  | 'not_uploaded'
  | 'pending'
  | 'approved'
  | 'rejected';

export interface Brand {
  id: string;
  name: string;
  official_domains?: string;
  keywords?: string;
  logo_url?: string;
  country_restrictions?: string;
  vekalet_status?: VekaletStatus;
  vekalet_uploaded_at?: string;
  vekalet_reviewed_at?: string;
  vekalet_reject_reason?: string;
  created_at: string;
}

export type IncidentStatus =
  | 'detected'
  | 'analyzing'
  | 'validated'
  | 'reported'
  | 'resolved'
  | 'false_positive';

export type ThreatType = 'phishing' | 'brand_impersonation' | 'typosquatting';

export type ScreenshotSource = 'playwright' | 'fallback' | 'playwright_blocked';

export interface Incident {
  id: string;
  brand_id: string;
  target_url: string;
  status: IncidentStatus;
  threat_type?: ThreatType;
  confidence_score?: number;
  screenshot_path?: string;
  screenshot_source?: ScreenshotSource | string;
  whois_raw?: string;
  discovered_at: string;
}

export type RecipientType =
  | 'cloudflare'
  | 'hosting'
  | 'registrar'
  | 'google_safebrowsing'
  | 'google_dmca';

export type ReportStatus =
  | 'pending'
  | 'sent'
  | 'form_only'
  | 'received'
  | 'actioned'
  | 'declined'
  | 'failed'
  | 'pending_review';

export interface Report {
  id: string;
  incident_id: string;
  recipient_type?: RecipientType;
  recipient_email?: string;
  recipient_form_url?: string;
  recipient_name?: string;
  subject?: string;
  message_id?: string;
  status?: ReportStatus;
  error_message?: string;
  sent_at?: string;
  raw_content?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
