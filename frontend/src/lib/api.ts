import type { CreateJobResponse, JobState } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function createJob(file: File, removeAudio: boolean, modelSize: string): Promise<CreateJobResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('remove_audio', String(removeAudio));
  form.append('model_size', modelSize);

  const resp = await fetch(`${API_BASE_URL}/api/v1/jobs`, { method: 'POST', body: form });
  if (!resp.ok) {
    throw new Error(`Create job failed: ${resp.status}`);
  }
  return resp.json();
}

export async function getJob(jobId: string): Promise<JobState> {
  const resp = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`);
  if (!resp.ok) {
    throw new Error(`Get job failed: ${resp.status}`);
  }
  return resp.json();
}

export function resolveDownloadUrl(path: string): string {
  return path.startsWith('http') ? path : `${API_BASE_URL}${path}`;
}
