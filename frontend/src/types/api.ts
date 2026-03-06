export type JobStatus = 'queued' | 'processing' | 'completed' | 'failed';
export type JobStage = 'queued' | 'probe' | 'extract_audio' | 'asr' | 'render' | 'done' | 'failed';

export interface CreateJobResponse {
  job_id: string;
  status: JobStatus;
}

export interface JobResult {
  resolution: { width: number; height: number };
  fontsize: number;
  margin_v: number;
  segments: number;
  download_urls: { srt: string; video: string };
}

export interface JobState {
  job_id: string;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  filename?: string | null;
  error?: string | null;
  result?: JobResult | null;
}
