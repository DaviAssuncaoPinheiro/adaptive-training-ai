'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { apiFetch } from '@/lib/api/client';

const POLL_INTERVAL_MS = 3000;

export function useMicrocycleGeneration({ onDone } = {}) {
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const timerRef = useRef(null);
  const onDoneRef = useRef(onDone);

  useEffect(() => {
    onDoneRef.current = onDone;
  }, [onDone]);

  const clearTimer = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const poll = useCallback(async (jobId) => {
    try {
      const job = await apiFetch(`/microcycle/job/${jobId}`);
      if (job?.status === 'done') {
        setStatus('done');
        if (onDoneRef.current) onDoneRef.current(job);
        return;
      }
      if (job?.status === 'failed') {
        setStatus('failed');
        setError(job.error || 'A IA não conseguiu gerar o microciclo.');
        return;
      }
      timerRef.current = setTimeout(() => poll(jobId), POLL_INTERVAL_MS);
    } catch (err) {
      setStatus('failed');
      setError(err.message);
    }
  }, []);

  const generate = useCallback(async () => {
    clearTimer();
    setStatus('generating');
    setError(null);
    try {
      const { job_id: jobId } = await apiFetch('/microcycle/generate', {
        method: 'POST',
      });
      timerRef.current = setTimeout(() => poll(jobId), POLL_INTERVAL_MS);
    } catch (err) {
      setStatus('failed');
      setError(err.message);
    }
  }, [poll]);

  useEffect(() => () => clearTimer(), []);

  return { status, error, generate };
}
