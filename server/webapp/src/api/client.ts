/**
 * Dem1chVPN — API Client
 * Handles communication between Mini App and FastAPI backend.
 */

const BASE_URL = '';  // Same origin (served by Caddy)

/**
 * Get Telegram WebApp initData for authentication
 */
function getInitData(): string {
  try {
    return (window as any).Telegram?.WebApp?.initData || '';
  } catch {
    return '';
  }
}

/**
 * Make an authenticated API request
 */
async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const initData = getInitData();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(initData ? { 'X-Telegram-Init-Data': initData } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const response = await fetch(`${BASE_URL}/api${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `HTTP ${response.status}`,
    );
  }

  return response.json();
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// ── Auth ──

export async function checkAuth() {
  return apiRequest<{
    is_admin: boolean;
    valid: boolean;
    user_id?: number;
    first_name?: string;
  }>('/auth/check', {
    method: 'POST',
    body: JSON.stringify({ initData: getInitData() }),
  });
}

// ── Status ──

export interface ServerStatus {
  cpu: number;
  ram_used: number;
  ram_total: number;
  disk_used: number;
  disk_total: number;
  uptime: string;
  xray_running: boolean;
  xray_version: string;
  users_count: number;
  traffic_today_up: number;
  traffic_today_down: number;
}

export async function getServerStatus(): Promise<ServerStatus> {
  return apiRequest<ServerStatus>('/status');
}

// ── Users ──

export interface User {
  id: number;
  name: string;
  active: boolean;
  traffic_up: number;
  traffic_down: number;
  traffic_total: number;
  traffic_limit: number | null;
  expiry: string | null;
  created: string | null;
}

export async function getUsers(): Promise<{ users: User[] }> {
  return apiRequest<{ users: User[] }>('/users');
}

export async function toggleUser(userId: number) {
  return apiRequest<{ id: number; active: boolean; name: string }>(
    `/users/${userId}/toggle`,
    { method: 'POST' },
  );
}

export async function getUserLink(userId: number) {
  return apiRequest<{ vless_url: string; sub_url: string }>(
    `/users/${userId}/link`,
  );
}

// ── Routes ──

export interface RouteRule {
  id: number;
  domain: string;
  rule_type: 'proxy' | 'direct';
  added_by: string;
}

export async function getRoutes(): Promise<{ rules: RouteRule[] }> {
  return apiRequest<{ rules: RouteRule[] }>('/routes');
}

export async function addRoute(domain: string, type: 'proxy' | 'direct') {
  return apiRequest<{ success: boolean; domain: string; type: string }>(
    '/routes',
    {
      method: 'POST',
      body: JSON.stringify({ domain, type }),
    },
  );
}

export async function deleteRoute(domain: string) {
  return apiRequest<{ success: boolean }>(`/routes/${encodeURIComponent(domain)}`, {
    method: 'DELETE',
  });
}

// ── Settings ──

export interface Settings {
  warp_enabled: boolean;
  adguard_enabled: boolean;
  mtproto_enabled: boolean;
  server_ip: string;
  reality_sni: string;
}

export async function getSettings(): Promise<Settings> {
  return apiRequest<Settings>('/settings');
}

export async function toggleFeature(feature: 'warp' | 'adguard' | 'mtproto') {
  return apiRequest<{ enabled: boolean }>(`/settings/${feature}/toggle`, {
    method: 'POST',
  });
}

// ── Actions ──

export async function restartXray() {
  return apiRequest<{ success: boolean }>('/xray/restart', { method: 'POST' });
}

export async function updateGeo() {
  return apiRequest<{ success: boolean }>('/geo/update', { method: 'POST' });
}

export async function createBackup() {
  return apiRequest<{ success: boolean; message: string }>('/backup', {
    method: 'POST',
  });
}

// ── Helpers ──

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

/**
 * Format percentage
 */
export function formatPercent(used: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((used / total) * 100);
}

// ── Tickets ──

export interface Ticket {
  id: number;
  user_telegram_id?: number;
  user_name?: string;
  message: string;
  reply: string | null;
  is_resolved: boolean;
  created_at: string | null;
  resolved_at: string | null;
}

export async function getMyTickets(): Promise<{ tickets: Ticket[] }> {
  return apiRequest<{ tickets: Ticket[] }>('/tickets/my');
}

export async function createTicket(message: string): Promise<{ id: number }> {
  return apiRequest<{ id: number }>('/tickets', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function getAllTickets(status: string = 'all'): Promise<{ tickets: Ticket[] }> {
  return apiRequest<{ tickets: Ticket[] }>(`/tickets?status=${status}`);
}

export async function replyToTicket(ticketId: number, reply: string) {
  return apiRequest<{ success: boolean }>(`/tickets/${ticketId}/reply`, {
    method: 'POST',
    body: JSON.stringify({ reply }),
  });
}

export async function closeTicket(ticketId: number) {
  return apiRequest<{ success: boolean }>(`/tickets/${ticketId}/close`, {
    method: 'POST',
  });
}

