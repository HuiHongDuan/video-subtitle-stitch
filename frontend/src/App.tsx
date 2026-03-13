import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Film, VolumeX, Volume2, FileText, Sun, Moon, Upload, Download } from 'lucide-react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import { createJob, listModels, resolveDownloadUrl, uploadFile } from './lib/api';
import { useJobPolling } from './hooks/useJobPolling';
import { StatusBadge } from './components/StatusBadge';

const ACCEPTED_VIDEO_TYPES = ['video/mp4', 'video/quicktime', 'video/x-matroska', 'video/x-msvideo', 'video/webm'];

export default function App() {
  const [isDark, setIsDark] = useState(false);
  const [removeAudio, setRemoveAudio] = useState(true);
  const [modelOptions, setModelOptions] = useState<string[]>(['tiny', 'base', 'small', 'medium', 'large']);
  const [modelSize, setModelSize] = useState('small');

  const [clipStartSec, setClipStartSec] = useState(0);
  const [clipEndSec, setClipEndSec] = useState(0);
  const [durationSec, setDurationSec] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [metadataReady, setMetadataReady] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const previewVideoRef = useRef<HTMLVideoElement | null>(null);

  const { job, error: pollingError } = useJobPolling(jobId);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
  }, [isDark]);

  useEffect(() => {
    listModels()
      .then((models) => {
        const options = models.options.map((item) => item.key);
        if (options.length > 0) {
          setModelOptions(options);
        }
        setModelSize(models.default);
      })
      .catch((err) => setSubmitError(err instanceof Error ? err.message : '加载模型配置失败'));
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const combinedError = submitError ?? pollingError ?? job?.error ?? null;
  const progressText = useMemo(() => {
    if (!job) return '等待上传视频';
    if (job.status === 'completed') return '处理完成';
    if (job.status === 'failed') return '处理失败';
    return `处理中 · ${job.stage} · ${job.progress}%`;
  }, [job]);

  function clampTime(value: number) {
    if (!Number.isFinite(value)) return 0;
    if (!durationSec || durationSec <= 0) return Math.max(0, value);
    return Math.max(0, Math.min(value, durationSec));
  }

  function seekPreview(targetSec: number) {
    const video = previewVideoRef.current;
    if (!video) return;
    video.currentTime = clampTime(targetSec);
  }

  function handleSelectFile(nextFile: File | null) {
    setFile(nextFile);
    setSubmitError(null);
    setJobId(null);

    setMetadataReady(false);
    setDurationSec(0);
    setClipStartSec(0);
    setClipEndSec(0);

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }

    if (nextFile) {
      setPreviewUrl(URL.createObjectURL(nextFile));
    }
  }

  function handlePreviewMetadataLoaded() {
    const video = previewVideoRef.current;
    if (!video || !Number.isFinite(video.duration) || video.duration <= 0) return;

    const duration = video.duration;
    setDurationSec(duration);
    setClipStartSec(0);
    setClipEndSec(duration);
    setMetadataReady(true);
  }

  function handleRangeSlider(next: number | number[]) {
    if (!Array.isArray(next) || next.length !== 2) return;
    const start = clampTime(Math.min(next[0], next[1]));
    const end = clampTime(Math.max(next[0], next[1]));
    setClipStartSec(start);
    setClipEndSec(end);
  }

  function handleRangeAfterChange(next: number | number[]) {
    if (!Array.isArray(next) || next.length !== 2) return;
    const start = clampTime(Math.min(next[0], next[1]));
    const end = clampTime(Math.max(next[0], next[1]));
    const current = previewVideoRef.current?.currentTime ?? start;
    const target = Math.abs(current - start) <= Math.abs(current - end) ? start : end;
    seekPreview(target);
  }

  async function handleSubmit() {
    if (!file) {
      setSubmitError('请先选择视频文件');
      return;
    }
    if (!metadataReady) {
      setSubmitError('视频元数据尚未加载完成，请稍后重试');
      return;
    }

    if (file.type && !ACCEPTED_VIDEO_TYPES.includes(file.type)) {
      setSubmitError('仅支持 mp4 / mov / mkv / avi / webm 视频格式');
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError(null);

      const upload = await uploadFile(file);
      const clipEndArg = clipEndSec >= durationSec - 0.05 ? null : clipEndSec;
      const created = await createJob(upload.upload_id, removeAudio, modelSize, clipStartSec, clipEndArg);
      setJobId(created.job_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '提交失败');
    } finally {
      setIsSubmitting(false);
    }
  }

  const videoUrl = job?.result?.download_urls?.video ? resolveDownloadUrl(job.result.download_urls.video) : null;
  const srtUrl = job?.result?.download_urls?.srt ? resolveDownloadUrl(job.result.download_urls.srt) : null;
  const silentUrl = job?.result?.download_urls?.silent ? resolveDownloadUrl(job.result.download_urls.silent) : null;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-gray-900 dark:text-gray-100">
      <div className="w-full max-w-2xl glass-panel rounded-3xl p-10 transition-colors duration-300 relative overflow-hidden">
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-primary opacity-20 blur-3xl rounded-full pointer-events-none"></div>
        <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-blue-500 opacity-20 blur-3xl rounded-full pointer-events-none"></div>

        <div className="relative z-10 flex flex-col items-center">
          <div className="mb-10 flex flex-col items-center">
            <div className="w-20 h-20 rounded-full glass-logo-button flex items-center justify-center mb-4">
              <span className="text-3xl font-extrabold tracking-tighter brand-ai-text">AI</span>
            </div>
            <h1 className="text-sm font-bold tracking-[0.3em] uppercase brand-subtitle">Subtitles</h1>
          </div>

          <div className="w-full mb-6">
            <div className="glass-input rounded-2xl border border-white/50 dark:border-white/10 relative overflow-hidden shadow-inner min-h-72">
              {!previewUrl && (
                <>
                  <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1536240478700-b869070f9279?auto=format&fit=crop&q=80&w=1000')] bg-cover bg-center blur-md opacity-40 dark:opacity-50"></div>
                  <div className="absolute inset-0 bg-white/30 dark:bg-black/40"></div>
                </>
              )}

              <div className="relative z-10 h-full flex flex-col items-center justify-center px-6 pt-6 pb-20">
                {!previewUrl ? (
                  <>
                    <Film className="w-12 h-12 mb-3 text-gray-800 dark:text-white drop-shadow-lg" />
                    <p className="text-xl font-semibold text-gray-900 dark:text-white drop-shadow-md break-all">选择一个视频文件</p>
                    <p className="text-sm mt-2 text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <Upload className="w-4 h-4" /> 点击上传
                    </p>
                  </>
                ) : (
                  <>
                    <video
                      ref={previewVideoRef}
                      src={previewUrl}
                      className="w-full h-48 md:h-56 rounded-xl object-cover border border-white/50 dark:border-white/10"
                      controls
                      preload="metadata"
                      onLoadedMetadata={handlePreviewMetadataLoaded}
                    />
                    <p className="mt-3 text-sm ui-label break-all">{file?.name}</p>
                  </>
                )}
              </div>

              <div className="absolute left-0 right-0 bottom-4 flex justify-center z-20">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-5 py-2.5 rounded-xl bg-black/70 text-white dark:bg-white/90 dark:text-black font-semibold flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  {file ? '重新上传视频' : '上传视频'}
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/mov,video/mkv,video/avi,video/webm"
                className="hidden"
                onChange={(e) => handleSelectFile(e.target.files?.[0] ?? null)}
              />
            </div>
          </div>

          <div className="w-full mb-6 glass-input rounded-2xl border border-white/50 dark:border-white/10 p-5">
            <div className="flex items-center justify-between text-sm ui-label mb-3">
              <span>时间剪辑滑条</span>
              <span>{durationSec > 0 ? `${clipStartSec.toFixed(1)}s - ${clipEndSec.toFixed(1)}s / ${durationSec.toFixed(1)}s` : '等待视频元数据'}</span>
            </div>
            <div className="clip-range px-1 py-2">
              <Slider
                range
                min={0}
                max={Math.max(0, durationSec)}
                step={0.1}
                value={[clipStartSec, clipEndSec]}
                onChange={handleRangeSlider}
                onChangeComplete={handleRangeAfterChange}
                disabled={!metadataReady}
              />
            </div>
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
              <span className="text-sm ui-label">{removeAudio ? '输出静音' : '保留原音频'}</span>
            </div>

            <div className="flex items-center gap-2 bg-white/30 dark:bg-gray-800/30 p-1.5 rounded-full border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-sm flex-wrap">
              {modelOptions.map((option) => (
                <button
                  key={option}
                  onClick={() => setModelSize(option)}
                  className={`px-4 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${modelSize === option ? 'bg-primary text-white shadow-sm' : 'text-slate-700 dark:text-gray-200 hover:bg-white/50 dark:hover:bg-gray-700/50'}`}
                  title={`Model ${option}`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <button
            disabled={!file || !metadataReady || isSubmitting}
            onClick={handleSubmit}
            className="w-full mb-8 py-4 rounded-2xl bg-black/80 text-white dark:bg-white/90 dark:text-black font-semibold disabled:opacity-50"
          >
            {isSubmitting ? '提交中...' : '开始生成'}
          </button>

          <div className="w-full pt-2 flex flex-col items-center gap-6">
            <StatusBadge job={job} />
            <div className="text-sm ui-label">{progressText}</div>
            {combinedError && <div className="text-sm text-rose-500 text-center">{combinedError}</div>}

            {job?.result && (
              <div className="text-xs text-center text-gray-600 dark:text-gray-400">
                分辨率：{job.result.resolution.width}×{job.result.resolution.height} · 字号：{job.result.fontsize} ·
                MarginV：{job.result.margin_v} · 段数：{job.result.segments} · 模型：{job.result.model_size}
              </div>
            )}

            <div className="flex w-full gap-4 flex-wrap">
              <a
                href={videoUrl ?? '#'}
                className={`flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl glass-input border border-white/50 dark:border-white/10 transition-all duration-300 group ${videoUrl ? 'hover:border-blue-400 hover:shadow-[0_0_15px_rgba(96,165,250,0.5)]' : 'pointer-events-none opacity-75'}`}
              >
                <Download className="w-6 h-6 text-blue-500" />
                <span className="font-semibold action-btn-label">下载视频</span>
              </a>
              <a
                href={srtUrl ?? '#'}
                className={`flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl glass-input border border-white/50 dark:border-white/10 transition-all duration-300 group ${srtUrl ? 'hover:border-fuchsia-400 hover:shadow-[0_0_15px_rgba(232,121,249,0.5)]' : 'pointer-events-none opacity-75'}`}
              >
                <FileText className="w-6 h-6 text-fuchsia-500" />
                <span className="font-semibold action-btn-label">下载字幕</span>
              </a>
              <a
                href={silentUrl ?? '#'}
                className={`flex-1 flex items-center justify-center gap-3 py-4 px-6 rounded-2xl glass-input border border-white/50 dark:border-white/10 transition-all duration-300 group ${silentUrl ? 'hover:border-emerald-400 hover:shadow-[0_0_15px_rgba(16,185,129,0.4)]' : 'pointer-events-none opacity-75'}`}
              >
                <Download className="w-6 h-6 text-emerald-500" />
                <span className="font-semibold action-btn-label">下载无声无字幕版</span>
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
