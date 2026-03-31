'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import {
  fetchAcademyScan,
  postCointegration,
  fetchOHLCV,
  type AcademyScanPair,
  type CointegrationResponse,
  type OHLCVResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AcademyPair {
  label: string;
  asset1: string;
  asset2: string;
  scanResult: AcademyScanPair;
}

export interface AcademyPairData {
  pair: AcademyPair;
  coint: CointegrationResponse;
  ohlcv1: OHLCVResponse;
  ohlcv2: OHLCVResponse;
}

export interface AcademyDataContextValue {
  /** The "good" pair — lowest p-value cointegrated pair */
  goodPair: AcademyPairData | null;
  /** The "bad" pair — not cointegrated, p ~0.3-0.5 (educational contrast) */
  badPair: AcademyPairData | null;
  /** All scanned pairs for the override picker */
  allPairs: AcademyScanPair[];
  /** Loading state */
  loading: boolean;
  /** Error message */
  error: string | null;
  /** Whether the initial scan + load has completed */
  ready: boolean;
  /** Override the good pair */
  setGoodPairOverride: (asset1: string, asset2: string) => void;
  /** Override the bad pair */
  setBadPairOverride: (asset1: string, asset2: string) => void;
  /** Trigger a fresh scan + load */
  refresh: () => void;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AcademyDataContext = createContext<AcademyDataContextValue | null>(null);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function baseFromSymbol(symbol: string): string {
  return symbol.split('/')[0] ?? symbol;
}

function pairToLabel(p: AcademyScanPair): string {
  return `${baseFromSymbol(p.asset1)} / ${baseFromSymbol(p.asset2)}`;
}

/**
 * Pick the best "bad" pair — not the absolute worst (boring),
 * but one with p ~0.15-0.5 for educational contrast.
 */
function pickBadPair(notCointegrated: AcademyScanPair[]): AcademyScanPair | null {
  if (notCointegrated.length === 0) return null;

  // Find one with p between 0.15 and 0.5 (sorted by p ascending)
  const decent = notCointegrated.find((p) => p.p_value >= 0.15 && p.p_value <= 0.5);
  if (decent) return decent;

  // Fallback: take one from the middle
  const mid = Math.floor(notCointegrated.length / 2);
  return notCointegrated[mid];
}

async function loadPairData(scanPair: AcademyScanPair): Promise<AcademyPairData> {
  const [coint, ohlcv1, ohlcv2] = await Promise.all([
    postCointegration({
      asset1: scanPair.asset1,
      asset2: scanPair.asset2,
      timeframe: '1h',
      days_back: 90,
    }),
    fetchOHLCV(scanPair.asset1, '1h', 90),
    fetchOHLCV(scanPair.asset2, '1h', 90),
  ]);

  return {
    pair: {
      label: pairToLabel(scanPair),
      asset1: scanPair.asset1,
      asset2: scanPair.asset2,
      scanResult: scanPair,
    },
    coint,
    ohlcv1,
    ohlcv2,
  };
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AcademyDataProvider({ children }: { children: ReactNode }) {
  const [goodPair, setGoodPair] = useState<AcademyPairData | null>(null);
  const [badPair, setBadPair] = useState<AcademyPairData | null>(null);
  const [allPairs, setAllPairs] = useState<AcademyScanPair[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const loadData = useCallback(async (
    goodOverride?: { asset1: string; asset2: string },
    badOverride?: { asset1: string; asset2: string },
  ) => {
    setLoading(true);
    setError(null);
    try {
      const scan = await fetchAcademyScan('1h', 90, true);
      const all = [...scan.cointegrated, ...scan.not_cointegrated];
      setAllPairs(all);

      // Pick good pair: override or best cointegrated
      let goodScanPair: AcademyScanPair | null = null;
      if (goodOverride) {
        goodScanPair = all.find(
          (p) => p.asset1 === goodOverride.asset1 && p.asset2 === goodOverride.asset2
        ) ?? null;
      }
      if (!goodScanPair && scan.cointegrated.length > 0) {
        goodScanPair = scan.cointegrated[0]; // Already sorted by p-value
      }

      // Pick bad pair: override or educational pick
      let badScanPair: AcademyScanPair | null = null;
      if (badOverride) {
        badScanPair = all.find(
          (p) => p.asset1 === badOverride.asset1 && p.asset2 === badOverride.asset2
        ) ?? null;
      }
      if (!badScanPair) {
        badScanPair = pickBadPair(scan.not_cointegrated);
      }

      // Load detailed data in parallel
      const promises: Promise<AcademyPairData | null>[] = [];
      promises.push(goodScanPair ? loadPairData(goodScanPair) : Promise.resolve(null));
      promises.push(badScanPair ? loadPairData(badScanPair) : Promise.resolve(null));

      const [goodData, badData] = await Promise.all(promises);
      setGoodPair(goodData);
      setBadPair(badData);
      setReady(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Academy data.');
    } finally {
      setLoading(false);
    }
  }, []);

  const setGoodPairOverride = useCallback((asset1: string, asset2: string) => {
    loadData({ asset1, asset2 }, badPair ? { asset1: badPair.pair.asset1, asset2: badPair.pair.asset2 } : undefined);
  }, [loadData, badPair]);

  const setBadPairOverride = useCallback((asset1: string, asset2: string) => {
    loadData(goodPair ? { asset1: goodPair.pair.asset1, asset2: goodPair.pair.asset2 } : undefined, { asset1, asset2 });
  }, [loadData, goodPair]);

  const refresh = useCallback(() => {
    loadData();
  }, [loadData]);

  const value: AcademyDataContextValue = {
    goodPair,
    badPair,
    allPairs,
    loading,
    error,
    ready,
    setGoodPairOverride,
    setBadPairOverride,
    refresh,
  };

  return (
    <AcademyDataContext.Provider value={value}>
      {children}
    </AcademyDataContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAcademyData(): AcademyDataContextValue {
  const ctx = useContext(AcademyDataContext);
  if (!ctx) {
    throw new Error('useAcademyData must be used within <AcademyDataProvider>.');
  }
  return ctx;
}
