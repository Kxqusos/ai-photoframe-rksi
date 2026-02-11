import React, { useEffect, useMemo, useState } from "react";

import { getJobStatus } from "../lib/api";
import type { JobStatus } from "../types";

type Props = {
  jobId?: number;
};

function resolveJobId(provided?: number): number | null {
  if (typeof provided === "number" && Number.isFinite(provided)) {
    return provided;
  }

  const fromQuery = new URLSearchParams(window.location.search).get("jobId");
  if (!fromQuery) {
    return null;
  }

  const value = Number(fromQuery);
  return Number.isFinite(value) ? value : null;
}

export function ResultPage({ jobId: providedJobId }: Props) {
  const jobId = useMemo(() => resolveJobId(providedJobId), [providedJobId]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (jobId === null) {
      setError("jobId is required");
      return;
    }

    let cancelled = false;

    async function poll() {
      try {
        const status = await getJobStatus(jobId);
        if (cancelled) {
          return;
        }
        setJob(status);
      } catch (cause) {
        if (cancelled) {
          return;
        }
        setError(cause instanceof Error ? cause.message : "Failed to get job status");
      }
    }

    poll();
    const timer = window.setInterval(poll, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [jobId]);

  if (error) {
    return <p role="alert">{error}</p>;
  }

  if (job?.status === "completed" && job.result_url && job.qr_url && job.download_url) {
    return (
      <main>
        <h1>Result</h1>
        <img src={job.result_url} alt="generated photo" width={480} />
        <img src={job.qr_url} alt="download qr" width={220} />
        <a href={job.download_url}>Скачать</a>
      </main>
    );
  }

  if (job?.status === "error") {
    return <p role="alert">{job.error_message || "Generation failed"}</p>;
  }

  return (
    <main>
      <h1>Result</h1>
      <p>Обработка изображения...</p>
    </main>
  );
}
