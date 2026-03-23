'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { fetchPairs, type PairInfo } from '@/lib/api';

export interface PairContextValue {
  asset1: string;
  asset2: string;
  timeframe: string;
  setAsset1: (v: string) => void;
  setAsset2: (v: string) => void;
  setTimeframe: (v: string) => void;
  pairs: PairInfo[];
  coins: string[];
  loading: boolean;
  error: string | null;
}

const PairContext = createContext<PairContextValue | null>(null);

export function PairProvider({ children }: { children: ReactNode }) {
  const [asset1, setAsset1] = useState<string>('');
  const [asset2, setAsset2] = useState<string>('');
  const [timeframe, setTimeframe] = useState<string>('1h');

  const [pairs, setPairs] = useState<PairInfo[]>([]);
  const [coins, setCoins] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetchPairs();
        if (cancelled) return;
        setPairs(res.pairs);
        const uniqueCoins = [...new Set(res.pairs.map((p) => p.base))].sort();
        setCoins(uniqueCoins);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : 'Failed to fetch pairs';
        setError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const handleSetAsset1 = useCallback((v: string) => setAsset1(v), []);
  const handleSetAsset2 = useCallback((v: string) => setAsset2(v), []);
  const handleSetTimeframe = useCallback((v: string) => setTimeframe(v), []);

  const value: PairContextValue = {
    asset1,
    asset2,
    timeframe,
    setAsset1: handleSetAsset1,
    setAsset2: handleSetAsset2,
    setTimeframe: handleSetTimeframe,
    pairs,
    coins,
    loading,
    error,
  };

  return <PairContext.Provider value={value}>{children}</PairContext.Provider>;
}

export function usePairContext(): PairContextValue {
  const ctx = useContext(PairContext);
  if (!ctx) {
    throw new Error(
      'usePairContext must be used within a <PairProvider>.'
    );
  }
  return ctx;
}
