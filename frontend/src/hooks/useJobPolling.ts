import { useEffect, useState } from 'react';
import { getJob } from '../lib/api';
import type { JobState } from '../types/api';

export function useJobPolling(jobId: string | null) {
  const [job, setJob] = useState<JobState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let timer: number | null = null;
    let active = true;

    const tick = async () => {
      try {
        const next = await getJob(jobId);
        if (!active) return;
        setJob(next);
        if (next.status === 'completed' || next.status === 'failed') return;
        timer = window.setTimeout(tick, 1500);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Unknown polling error');
      }
    };

    tick();
    return () => {
      active = false;
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  return { job, error };
}
