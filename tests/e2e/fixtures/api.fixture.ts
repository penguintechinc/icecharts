/**
 * API seeding helpers for Playwright E2E tests.
 *
 * These functions talk directly to the Flask backend API so tests can create
 * the data they need without navigating through the UI.  All helpers accept an
 * auth token obtained from getAuthToken().
 */

import type { APIRequestContext } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:5000';

// ---------------------------------------------------------------------------
// Type definitions
// ---------------------------------------------------------------------------

export interface ApiResponse<T = Record<string, unknown>> {
  status: number;
  ok: boolean;
  body: T;
}

// Minimal data shapes — expand as the API schema evolves
export interface DrawingData {
  name: string;
  description?: string;
  is_public?: boolean;
  tags?: string[];
}

export interface PlaybookData {
  name: string;
  description?: string;
  connector_id?: string;
  is_enabled?: boolean;
}

export interface CollectionData {
  name: string;
  description?: string;
  is_public?: boolean;
}

export interface GroupData {
  name: string;
  description?: string;
}

export interface IceRunData {
  name: string;
  description?: string;
  runtime?: string;
  code?: string;
  memory?: number;
  timeout?: number;
}

export interface IceFlowData {
  name: string;
  description?: string;
  stages?: unknown[];
}

// ---------------------------------------------------------------------------
// Internal helper
// ---------------------------------------------------------------------------

async function apiPost<T = Record<string, unknown>>(
  request: APIRequestContext,
  path: string,
  authToken: string,
  data: unknown
): Promise<ApiResponse<T>> {
  const response = await request.post(`${API_URL}${path}`, {
    data,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authToken}`,
    },
  });

  const body = (await response.json().catch(() => ({}))) as T;
  return { status: response.status(), ok: response.ok(), body };
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

/**
 * Authenticate via the API and return the access token.
 */
export async function getAuthToken(
  request: APIRequestContext,
  email: string,
  password: string
): Promise<string> {
  const response = await request.post(`${API_URL}/api/v1/auth/login`, {
    data: { email, password },
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok()) {
    const text = await response.text();
    throw new Error(`getAuthToken failed (${response.status()}): ${text}`);
  }

  const { access_token } = await response.json();
  return access_token as string;
}

// ---------------------------------------------------------------------------
// Drawings
// ---------------------------------------------------------------------------

/**
 * Create a drawing via POST /api/v1/drawings.
 */
export async function createDrawing(
  request: APIRequestContext,
  authToken: string,
  data: DrawingData
): Promise<ApiResponse> {
  return apiPost(request, '/api/v1/drawings', authToken, data);
}

// ---------------------------------------------------------------------------
// Playbooks
// ---------------------------------------------------------------------------

/**
 * Create a playbook via POST /api/v1/playbooks.
 */
export async function createPlaybook(
  request: APIRequestContext,
  authToken: string,
  data: PlaybookData
): Promise<ApiResponse> {
  return apiPost(request, '/api/v1/playbooks', authToken, data);
}

// ---------------------------------------------------------------------------
// Collections
// ---------------------------------------------------------------------------

/**
 * Create a collection via POST /api/v1/collections.
 */
export async function createCollection(
  request: APIRequestContext,
  authToken: string,
  data: CollectionData
): Promise<ApiResponse> {
  return apiPost(request, '/api/v1/collections', authToken, data);
}

// ---------------------------------------------------------------------------
// Groups
// ---------------------------------------------------------------------------

/**
 * Create a group via POST /api/v1/groups.
 */
export async function createGroup(
  request: APIRequestContext,
  authToken: string,
  data: GroupData
): Promise<ApiResponse> {
  return apiPost(request, '/api/v1/groups', authToken, data);
}

// ---------------------------------------------------------------------------
// IceRuns (Serverless Functions)
// ---------------------------------------------------------------------------

/**
 * Create an IceRun function via POST /api/v1/iceruns.
 */
export async function createIceRun(
  request: APIRequestContext,
  authToken: string,
  data: IceRunData
): Promise<ApiResponse> {
  return apiPost(request, '/api/v1/iceruns', authToken, data);
}

// ---------------------------------------------------------------------------
// IceFlows (CI/CD Pipelines)
// ---------------------------------------------------------------------------

/**
 * Create an IceFlow pipeline via POST /api/v1/iceflows.
 */
export async function createIceFlow(
  request: APIRequestContext,
  authToken: string,
  data: IceFlowData
): Promise<ApiResponse> {
  return apiPost(request, '/api/v1/iceflows', authToken, data);
}
