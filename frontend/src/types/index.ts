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

export interface Brand {
  id: string;
  name: string;
  official_domains?: string;
  keywords?: string;
  logo_url?: string;
  created_at: string;
}

export interface Incident {
  id: string;
  brand_id: string;
  target_url: string;
  status: 'NEW' | 'ANALYZING' | 'VALIDATED' | 'REPORTED' | 'RESOLVED' | 'FALSE_POSITIVE';
  threat_type?: 'PHISHING' | 'BRAND_IMPERSONATION' | 'TYPOSQUATTING';
  confidence_score?: number;
  screenshot_path?: string;
  whois_raw?: string;
  discovered_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
