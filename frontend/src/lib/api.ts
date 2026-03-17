import type { CreateJobResponse, ErrorResponse, JobState, ModelsResponse, UploadResponse } from '../types/api';

const DEFAULT_API_BASE_URL = '/api';
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).trim();
const ABSOLUTE_URL_RE = /^https?:\/\//i;

function joinUrl(base: string, path: string): string {
  const normalizedBase = base.replace(/\/+$/, '');
  const normalizedPath = path.replace(/^\/+/, '');
  if (!normalizedPath) return normalizedBase || '/';
  if (!normalizedBase) return `/${normalizedPath}`;
  return `${normalizedBase}/${normalizedPath}`;
}

function resolveApiUrl(path: string): string {
  if (ABSOLUTE_URL_RE.test(path)) return path;
  return joinUrl(API_BASE_URL || DEFAULT_API_BASE_URL, path);
}

async function parseResponse<T>(resp: Response): Promise<T> {
  if (resp.ok) {
    return resp.json() as Promise<T>;
  }

  let payload: ErrorResponse | null = null;
  try {
    payload = (await resp.json()) as ErrorResponse;
  } catch {
    // ignore json parse issues and use fallback message
  }

  throw new Error(payload?.error ?? `Request failed: ${resp.status}`);
}

export async function listModels(): Promise<ModelsResponse> {
  const resp = await fetch(resolveApiUrl('/v1/models'));
  return parseResponse<ModelsResponse>(resp);
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const resp = await fetch(resolveApiUrl('/v1/uploads'), { method: 'POST', body: form });
  return parseResponse<UploadResponse>(resp);
}

export async function createJob(
  uploadId: string,
  removeAudio: boolean,
  modelSize: string,
  clipStartSec = 0,
  clipEndSec?: number | null,
): Promise<CreateJobResponse> {
  const form = new FormData();
  form.append('upload_id', uploadId);
  form.append('remove_audio', String(removeAudio));
  form.append('model_size', modelSize);
  form.append('clip_start_sec', String(clipStartSec));
  if (typeof clipEndSec === 'number' && Number.isFinite(clipEndSec)) {
    form.append('clip_end_sec', String(clipEndSec));
  }

  const resp = await fetch(resolveApiUrl('/v1/jobs'), { method: 'POST', body: form });
  return parseResponse<CreateJobResponse>(resp);
}

export async function getJob(jobId: string): Promise<JobState> {
  const resp = await fetch(resolveApiUrl(`/v1/jobs/${jobId}`));
  return parseResponse<JobState>(resp);
}

export function resolveDownloadUrl(path: string): string {
  if (ABSOLUTE_URL_RE.test(path)) return path;
  if (path.startsWith('/api/')) {
    return resolveApiUrl(path.slice('/api'.length));
  }
  return resolveApiUrl(path);
}
