import { useEffect, useState } from "react";
import type { HistoryData, IndexData, SignalData } from "../types/signal";

const DATA_BASE_URL = import.meta.env.VITE_DATA_BASE_URL || "/data";

export function useIndex() {
  const [data, setData] = useState<IndexData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/index.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, error, loading };
}

export function useSignalData(pairId: string | null) {
  const [data, setData] = useState<SignalData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!pairId) return;
    setLoading(true);
    setError(null);
    fetch(`${DATA_BASE_URL}/${pairId}/latest.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [pairId]);

  return { data, error, loading };
}

export function useHistoryData(pairId: string | null) {
  const [data, setData] = useState<HistoryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!pairId) return;
    setLoading(true);
    setError(null);
    fetch(`${DATA_BASE_URL}/${pairId}/history.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [pairId]);

  return { data, error, loading };
}
