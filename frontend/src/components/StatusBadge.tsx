import { CheckCircle2, LoaderCircle, TriangleAlert } from 'lucide-react';
import type { JobState } from '../types/api';

export function StatusBadge({ job }: { job: JobState | null }) {
  if (!job) return <span className="text-xs font-semibold tracking-widest uppercase text-gray-500">Idle</span>;
  if (job.status === 'completed') {
    return (
      <div className="flex flex-col items-center justify-center">
        <CheckCircle2 className="w-12 h-12 text-emerald-400" />
        <span className="text-xs mt-3 font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest">Success</span>
      </div>
    );
  }
  if (job.status === 'failed') {
    return (
      <div className="flex flex-col items-center justify-center">
        <TriangleAlert className="w-12 h-12 text-rose-400" />
        <span className="text-xs mt-3 font-semibold text-rose-600 dark:text-rose-400 uppercase tracking-widest">Failed</span>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-center justify-center">
      <LoaderCircle className="w-12 h-12 animate-spin text-blue-400" />
      <span className="text-xs mt-3 font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-widest">{job.stage}</span>
    </div>
  );
}
