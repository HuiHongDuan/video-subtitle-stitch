import React, { useEffect, useMemo, useState } from 'react';
import { Film, VolumeX, Volume2, FileText, Sun, Moon, Upload, Download } from 'lucide-react';
import { createJob, resolveDownloadUrl } from './lib/api';
import { useJobPolling } from './hooks/useJobPolling';
import { StatusBadge } from './components/StatusBadge';

const MODEL_OPTIONS = ['tiny', 'base', 'small', 'medium'] as const;

export default function App() {
  const [isDark, setIsDark] = useState(false);
  const [removeAudio, setRemoveAudio] = useState(true);
  const [modelSize, setModelSize] = useState<(typeof MODEL_OPTIONS)[number]>('small');
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { job, error: pollingError } = useJobPolling(jobId);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
  }, [isDark]);

  const combinedError = submitError ?? pollingError ?? job?.error ?? null;
  const progressText = useMemo(() => {
    if (!job) return '等待上传视频';
    if (job.status === 'completed') return '处理完成';
    if (job.status === 'failed') return '处理失败';
    return `处理中 · ${job.stage} · ${job.progress}%`;
  }, [job]);

  async function handleSubmit() {
    if (!file) return;
    try {
      setIsSubmitting(true);
      setSubmitError(null);
      const created = await createJob(file, removeAudio, modelSize);
      setJobId(created.job_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '提交失败');
    } finally {
      setIsSubmitting(false);
    }
  }

  const videoUrl = job?.result?.download_urls?.video ? resolveDownloadUrl(job.result.download_urls.video) : null;
  const srtUrl = job?.result?.download_urls?.srt ? resolveDownloadUrl(job.result.download_urls.srt) : null;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-gray-900 dark:text-gray-100">
      <div className="w-full max-w-2xl glass-panel rounded-3xl p-10 transition-colors duration-300 relative overflow-hidden">
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-primary opacity-20 blur-3xl rounded-full pointer-events-none"></div>
        <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-blue-500 opacity-20 blur-3xl rounded-full pointer-events-none"></div>

        <div className="relative z-10 flex flex-col items-center">
          <div className="mb-10 flex flex-col items-center">
            <div className="w-20 h-20 rounded-full glass-logo-button flex items-center justify-center mb-4">
              <span className="text-3xl font-extrabold text-gray-800 dark:text-white tracking-tighter">AI</span>
            </div>
            <h1 className="text-sm font-bold tracking-[0.3em] text-gray-600 dark:text-gray-300 uppercase">Subtitles</h1>
          </div>

          <div className="w-full mb-8">
            <label className="glass-input rounded-2xl border border-white/50 dark:border-white/10 relative overflow-hidden flex flex-col items-center justify-center text-center h-48 shadow-inner cursor-pointer px-6">
              <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1536240478700-b869070f9279?auto=format&fit=crop&q=80&w=1000')] bg-cover bg-center blur-md opacity-40 dark:opacity-50"></div>
              <div className="absolute inset-0 bg-white/30 dark:bg-black/40"></div>
              <div className="relative z-10 flex flex-col items-center">
                <Film className="w-10 h-10 mb-2 text-gray-800 dark:text-white drop-shadow-lg" />
                <p className="text-lg font-semibold text-gray-900 dark:text-white drop-shadow-md break-all">{file?.name ?? '选择一个视频文件'}</p>
                <p className="text-sm mt-2 text-gray-700 dark:text-gray-300 flex items-center gap-2"><Upload className="w-4 h-4" /> 点击上传</p>
              </div>
              <input
                type="file"
                accept="video/mp4,video/mov,video/mkv,video/avi,video/webm"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
          </div>

          <div className="w-full flex items-center justify-between mb-8 px-4 gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setRemoveAudio(!removeAudio)}
                className="w-12 h-12 rounded-full glass-input flex items-center justify-center hover:bg-white/60 dark:hover:bg-gray-700/60 transition-colors group"
                title="Toggle mute output"
              >
                {removeAudio ? (
                  <VolumeX className="w-6 h-6 text-gray-600 dark:text-gray-300 group-hover:text-primary transition-colors" />
                ) : (
                  <Volume2 className="w-6 h-6 text-gray-600 dark:text-gray-300 group-hover:text-primary transition-colors" />
                )}
              </button>
              <span className="text-sm text-gray-700 dark:text-gray-300">{removeAudio ? '输出静音' : '保留原音频'}</span>
            </div>

            <div className="flex items-center gap-2 bg-white/30 dark:bg-gray-800/30 p-1.5 rounded-full border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-sm flex-wrap">
              {MODEL_OPTIONS.map((option) => (
                <button
                  key={option}
                  onClick={() => setModelSize(option)}
                  className={`px-4 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${modelSize === option ? 'bg-primary text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:bg-white/50 dark:hover:bg-gray-700/50'}`}
                  title={`Model ${option}`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <button
            disabled={!file || isSubmitting}
            onClick={handleSubmit}
            className="w-full mb-8 py-4 rounded-2xl bg-black/80 text-white dark:bg-white/90 dark:text-black font-semibold disabled:opacity-50"
          >
            {isSubmitting ? '提交中...' : '开始生成'}
          </button>

          <div className="w-full pt-2 flex flex-col items-center gap-6">
            <StatusBadge job={job} />
            <div className="text-sm text-gray-700 dark:text-gray-300">{progressText}</div>
            {combinedError && <div className="text-sm text-rose-500 text-center">{combinedError}</div>}

            {job?.result && (
              <div className="text-xs text-center text-gray-600 dark:text-gray-400">
                分辨率：{job.result.resolution.width}×{job.result.resolution.height} · 字号：{job.result.fontsize} · MarginV：{job.result.margin_v} · 段数：{job.result.segments}
              </div>
            )}

            <div className="flex w-full gap-4">
              <a
                href={videoUrl ?? '#'}
                className={`flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl glass-input border border-white/50 dark:border-white/10 transition-all duration-300 group ${videoUrl ? 'hover:border-blue-400 hover:shadow-[0_0_15px_rgba(96,165,250,0.5)]' : 'pointer-events-none opacity-50'}`}
              >
                <Download className="w-6 h-6 text-blue-500" />
                <span className="font-semibold text-gray-800 dark:text-gray-100">下载视频</span>
              </a>
              <a
                href={srtUrl ?? '#'}
                className={`flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl glass-input border border-white/50 dark:border-white/10 transition-all duration-300 group ${srtUrl ? 'hover:border-fuchsia-400 hover:shadow-[0_0_15px_rgba(232,121,249,0.5)]' : 'pointer-events-none opacity-50'}`}
              >
                <FileText className="w-6 h-6 text-fuchsia-500" />
                <span className="font-semibold text-gray-800 dark:text-gray-100">下载字幕</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={() => setIsDark(!isDark)}
        className="fixed bottom-6 right-6 p-4 glass-panel rounded-full shadow-lg text-gray-800 dark:text-white flex items-center justify-center hover:scale-110 transition-transform"
      >
        {isDark ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
      </button>
    </div>
  );
}
