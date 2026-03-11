export type JobStatus = 'queued' | 'processing' | 'completed' | 'failed';
export type JobStage = 'queued' | 'probe' | 'clip' | 'extract_audio' | 'asr' | 'render' | 'export_silent' | 'done' | 'failed';

export interface ErrorResponse {
  error: string;
  code: string;
}

export interface CreateJobResponse {
  job_id: string;
  status: JobStatus;
}

export interface UploadResponse {
  upload_id: string;
  filename: string;
  size_bytes: number;
}

export interface ModelsResponse {
  default: string;
  options: Array<{ key: string }>;
}

export interface JobResult {
  resolution: { width: number; height: number };
  fontsize: number;
  margin_v: number;
  segments: number;
  model_path: string;
  model_size: string;
  input_duration: number;
  output_duration: number;
  silent_duration: number;
  clip_range_sec: [number, number];
  download_urls: { srt: string; video: string; silent: string };
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
