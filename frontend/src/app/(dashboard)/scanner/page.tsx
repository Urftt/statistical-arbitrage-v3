'use client';

import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import {
  Alert,
  Button,
  Container,
  Group,
  Loader,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Title,
  UnstyledButton,
} from '@mantine/core';
import {
  IconAlertCircle,
  IconArrowsSort,
  IconCheck,
  IconChevronDown,
  IconChevronUp,
  IconDownload,
  IconSearch,
} from '@tabler/icons-react';
import {
  fetchPairs,
  fetchScan,
  fetchLiveData,
  type FetchLiveDataResponse,
  type PairInfo,
  type ScanPair,
  type ScanResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Constants (D-10, D-28)
// ---------------------------------------------------------------------------

// D-28: Smart per-timeframe days_back defaults. 1h → 90 (~2160 candles),
// 4h → 180 (~1080 candles), 1d → 365 (365 candles). All clear the
// 100-candle cointegration minimum with comfortable margin.
const DAYS_BACK_BY_TIMEFRAME: Record<string, number> = {
  '1h': 90,
  '4h': 180,
  '1d': 365,
};

function daysBackForTimeframe(tf: string): number {
  return DAYS_BACK_BY_TIMEFRAME[tf] ?? 90;
}

// D-10: Natural sort direction per column on first click. Same map per section.
type SortDirection = 'asc' | 'desc' | null;
type SortableColumn =
  | 'p_value'
  | 'cointegration_score'
  | 'hedge_ratio'
  | 'half_life'
  | 'correlation'
  | 'observations';

interface SortState {
  column: SortableColumn | null;
  direction: SortDirection;
}

const NATURAL_DIRECTION: Record<SortableColumn, Exclude<SortDirection, null>> = {
  p_value: 'asc',
  cointegration_score: 'desc',
  hedge_ratio: 'asc',
  half_life: 'asc',
  correlation: 'desc',
  observations: 'desc',
};

const NO_SORT: SortState = { column: null, direction: null };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// D-02: Three-state cycle. Same column clicked twice flips to opposite of natural;
// third click resets to NO_SORT (default order = whatever the backend returned,
// which is p-value asc per backend sort).
function nextSortState(current: SortState, column: SortableColumn): SortState {
  if (current.column !== column) {
    return { column, direction: NATURAL_DIRECTION[column] };
  }
  if (current.direction === NATURAL_DIRECTION[column]) {
    const opposite: SortDirection = current.direction === 'asc' ? 'desc' : 'asc';
    return { column, direction: opposite };
  }
  return NO_SORT;
}

// D-11: Null half_life always sorts last regardless of direction.
function sortPairs(pairs: ScanPair[], sort: SortState): ScanPair[] {
  if (!sort.column || !sort.direction) return pairs;
  const col = sort.column;
  const dir = sort.direction;
  return [...pairs].sort((a, b) => {
    const av = a[col] as number | null;
    const bv = b[col] as number | null;
    if (av == null && bv == null) return 0;
    if (av == null) return 1;   // nulls last
    if (bv == null) return -1;  // nulls last
    return dir === 'asc' ? av - bv : bv - av;
  });
}

// Half-life formatter (D-15): "X bars (Yh)" / "X bars (Yd)" or "N/A" dimmed
function formatHalfLife(half_life: number | null, timeframe: string): string {
  if (half_life == null || half_life <= 0) return 'N/A';
  const bars = half_life.toFixed(1);
  // Convert bars to time using the selected timeframe
  if (timeframe === '1d') {
    return `${bars} bars (${half_life.toFixed(1)}d)`;
  }
  const hours = timeframe === '4h' ? half_life * 4 : half_life; // 1h or 4h
  if (hours >= 24) {
    return `${bars} bars (${(hours / 24).toFixed(1)}d)`;
  }
  return `${bars} bars (${hours.toFixed(1)}h)`;
}

// Cache status: "32 coins cached for 1h, last updated 2h ago"
function formatRelativeTime(ms: number): string {
  if (!ms) return 'never';
  const diff = Date.now() - ms;
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ---------------------------------------------------------------------------
// Sortable header cell (D-01, D-09, D-12)
// ---------------------------------------------------------------------------

interface SortableHeaderProps {
  label: string;
  column: SortableColumn;
  sort: SortState;
  onSort: (column: SortableColumn) => void;
}

function SortableHeader({ label, column, sort, onSort }: SortableHeaderProps) {
  const isActive = sort.column === column;
  const ascActive = isActive && sort.direction === 'asc';
  const descActive = isActive && sort.direction === 'desc';
  return (
    <Table.Th>
      <UnstyledButton
        onClick={() => onSort(column)}
        style={{ display: 'inline-flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}
      >
        <Text size="sm" fw={600}>{label}</Text>
        {ascActive && <IconChevronUp size={14} />}
        {descActive && <IconChevronDown size={14} />}
        {!isActive && <IconArrowsSort size={14} style={{ opacity: 0.4 }} />}
      </UnstyledButton>
    </Table.Th>
  );
}

// ---------------------------------------------------------------------------
// ScannerSection (D-05, D-06, D-08, D-13, D-14, D-15) — used twice
// ---------------------------------------------------------------------------

interface ScannerSectionProps {
  title: string;          // "Cointegrated (4)" / "Not cointegrated (12)"
  accent: 'teal' | 'dimmed';
  pairs: ScanPair[];
  timeframe: string;
  onRowClick: (pair: ScanPair) => void;
}

function ScannerSection({ title, accent, pairs, timeframe, onRowClick }: ScannerSectionProps) {
  // D-06: Independent sort state per section
  const [sort, setSort] = useState<SortState>(NO_SORT);

  const handleSort = useCallback((column: SortableColumn) => {
    setSort((prev) => nextSortState(prev, column));
  }, []);

  // Reset sort when the underlying pairs array changes (new scan results)
  useEffect(() => {
    setSort(NO_SORT); // eslint-disable-line react-hooks/set-state-in-effect
  }, [pairs]);

  const sorted = useMemo(() => sortPairs(pairs, sort), [pairs, sort]);

  return (
    <Stack gap="xs">
      <Title order={3} c={accent === 'teal' ? 'teal.4' : 'dimmed'}>
        {title}
      </Title>
      <Paper radius="sm" withBorder>
        {sorted.length === 0 ? (
          // D-08: Always render empty section frame for layout stability
          <Text ta="center" c="dimmed" py="lg">
            No pairs in this category
          </Text>
        ) : (
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                {/* D-09: Pair label is NOT sortable */}
                <Table.Th>
                  <Text size="sm" fw={600}>Pair</Text>
                </Table.Th>
                <SortableHeader label="p-value" column="p_value" sort={sort} onSort={handleSort} />
                {/* D-14: Renamed Score → Coint. Score */}
                <SortableHeader label="Coint. Score" column="cointegration_score" sort={sort} onSort={handleSort} />
                <SortableHeader label="Hedge Ratio" column="hedge_ratio" sort={sort} onSort={handleSort} />
                <SortableHeader label="Half-Life" column="half_life" sort={sort} onSort={handleSort} />
                <SortableHeader label="Correlation" column="correlation" sort={sort} onSort={handleSort} />
                <SortableHeader label="Observations" column="observations" sort={sort} onSort={handleSort} />
              </Table.Tr>
            </Table.Thead>
            {/* D-04: Row click target lives in Tbody — separate DOM subtree from Thead */}
            <Table.Tbody>
              {sorted.map((pair) => {
                return (
                  <Table.Tr
                    key={`${pair.asset1}-${pair.asset2}`}
                    onClick={() => onRowClick(pair)}
                    style={{
                      cursor: 'pointer',
                      backgroundColor: pair.is_cointegrated
                        ? 'rgba(32, 201, 151, 0.06)'
                        : undefined,
                    }}
                  >
                    <Table.Td>
                      <Text fw={600} size="sm">
                        {pair.asset1.split('/')[0]} / {pair.asset2.split('/')[0]}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text
                        size="sm"
                        fw={700}
                        c={pair.p_value < 0.05 ? 'teal.4' : pair.p_value < 0.1 ? 'yellow.4' : 'red.4'}
                      >
                        {pair.p_value.toFixed(4)}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{pair.cointegration_score.toFixed(3)}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{pair.hedge_ratio.toFixed(3)}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c={pair.half_life != null && pair.half_life > 0 ? undefined : 'dimmed'}>
                        {formatHalfLife(pair.half_life, timeframe)}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{pair.correlation.toFixed(3)}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" c="dimmed">{pair.observations}</Text>
                    </Table.Td>
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>
        )}
      </Paper>
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// ScannerContent — main client component (wrapped in Suspense by ScannerPage)
// ---------------------------------------------------------------------------

function ScannerContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // D-27: timeframe persisted in URL query param
  const timeframe = searchParams.get('timeframe') ?? '1h';

  const handleTimeframeChange = useCallback(
    (value: string | null) => {
      if (!value) return;
      const params = new URLSearchParams(searchParams.toString());
      params.set('timeframe', value);
      router.replace(pathname + '?' + params.toString());
    },
    [router, pathname, searchParams]
  );

  // Cache state (D-22, D-26)
  const [cachedCoinCount, setCachedCoinCount] = useState<number>(0);
  const [cacheLastUpdatedMs, setCacheLastUpdatedMs] = useState<number>(0);
  const [cacheLoading, setCacheLoading] = useState(true);

  // Fetch state
  const [fetching, setFetching] = useState(false);
  const [fetchResult, setFetchResult] = useState<FetchLiveDataResponse | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Scan state
  const [scanning, setScanning] = useState(false);
  const [scanResponse, setScanResponse] = useState<ScanResponse | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [droppedDismissed, setDroppedDismissed] = useState(false);

  // Refresh cache state from /api/pairs
  const refreshCacheState = useCallback(async (): Promise<number> => {
    setCacheLoading(true);
    try {
      const res = await fetchPairs();
      const filtered = res.pairs.filter((p: PairInfo) => p.timeframe === timeframe);
      const bases = new Set(filtered.map((p) => p.base));
      const lastEnd = filtered
        .map((p) => new Date(p.end).getTime())
        .reduce((max, t) => Math.max(max, t), 0);
      setCachedCoinCount(bases.size);
      setCacheLastUpdatedMs(lastEnd);
      return bases.size;
    } catch {
      setCachedCoinCount(0);
      setCacheLastUpdatedMs(0);
      return 0;
    } finally {
      setCacheLoading(false);
    }
  }, [timeframe]);

  // D-19, D-28: Fetch fresh data using current timeframe and smart days_back
  const handleFetchData = useCallback(async () => {
    setFetching(true);
    setFetchResult(null);
    setFetchError(null);
    try {
      const result = await fetchLiveData(timeframe, daysBackForTimeframe(timeframe), 20);
      setFetchResult(result);
      // Refresh cache state to pick up newly fetched data
      await refreshCacheState();
    } catch (err) {
      setFetchError(
        err instanceof Error ? err.message : 'Failed to fetch data from Bitvavo'
      );
    } finally {
      setFetching(false);
    }
  }, [timeframe, refreshCacheState]);

  // D-20: Auto-fetch on mount/timeframe-change when cache is empty.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const count = await refreshCacheState();
      if (cancelled) return;
      if (count === 0 && !fetching) {
        // Empty cache for this timeframe → auto-fetch
        await handleFetchData();
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeframe]);

  // D-26: "Scan N pairs" math = C(cachedCoinCount, 2)
  const possibleCombinations = (cachedCoinCount * (cachedCoinCount - 1)) / 2;

  // D-03: First-scan default = p-value asc, which is what the backend returns
  const runScan = useCallback(async () => {
    if (cachedCoinCount < 2) return;
    setScanning(true);
    setScanError(null);
    setScanResponse(null);
    setDroppedDismissed(false);
    try {
      const res = await fetchScan(timeframe, daysBackForTimeframe(timeframe), 20);
      setScanResponse(res);
      // Refresh cache status (last_updated may have changed if scan triggered any fetches)
      await refreshCacheState();
    } catch (err) {
      setScanError(
        err instanceof Error ? err.message : 'Scan failed. Is the API running?'
      );
    } finally {
      setScanning(false);
    }
  }, [cachedCoinCount, timeframe, refreshCacheState]);

  // Row click handler — Phase 1 D-04 contract preserved
  const handleRowClick = useCallback(
    (pair: ScanPair) => {
      const base1 = pair.asset1.split('/')[0];
      const base2 = pair.asset2.split('/')[0];
      router.push(`/pair-analysis?asset1=${base1}&asset2=${base2}&timeframe=${timeframe}`);
    },
    [router, timeframe]
  );

  const cointegrated = scanResponse?.cointegrated ?? [];
  const notCointegrated = scanResponse?.not_cointegrated ?? [];
  const dropped = scanResponse?.dropped_for_completeness ?? [];
  const cachedCount = scanResponse?.cached_coin_count ?? cachedCoinCount;

  return (
    <Container size="xl" py="md">
      <Stack gap="lg">
        {/* Page header */}
        <Stack gap="xs">
          <Title order={1}>Pair Scanner</Title>
          <Text c="dimmed">
            Scan all pair combinations for cointegration. Pick a timeframe and hit Scan to find
            pairs to dive deeper into.
          </Text>
        </Stack>

        {/* D-25: Final control surface */}
        <Paper p="md" radius="sm" withBorder>
          <Stack gap="md">
            <Group gap="md" align="end">
              <Select
                label="Timeframe"
                data={[
                  { label: '1 hour', value: '1h' },
                  { label: '4 hours', value: '4h' },
                  { label: '1 day', value: '1d' },
                ]}
                value={timeframe}
                onChange={handleTimeframeChange}
                w={140}
                size="sm"
              />
              <Button
                leftSection={
                  fetching ? <Loader size={14} color="white" /> : <IconDownload size={16} />
                }
                onClick={handleFetchData}
                disabled={fetching}
                variant="light"
                size="sm"
              >
                {fetching ? 'Fetching from Bitvavo...' : 'Fetch top 20 from Bitvavo'}
              </Button>
              <Button
                leftSection={
                  scanning ? <Loader size={14} color="white" /> : <IconSearch size={16} />
                }
                onClick={runScan}
                disabled={cachedCoinCount < 2 || scanning}
                size="sm"
              >
                {scanning
                  ? 'Scanning...'
                  : `Scan ${possibleCombinations} pairs`}
              </Button>
            </Group>

            {/* D-22: Cache status line */}
            <Text size="xs" c="dimmed">
              {cacheLoading
                ? 'Loading cache state...'
                : cachedCoinCount === 0
                ? `No coins cached for ${timeframe}. Fetch from Bitvavo to populate.`
                : `${cachedCoinCount} coins cached for ${timeframe}, last updated ${formatRelativeTime(cacheLastUpdatedMs)}`}
            </Text>

            {/* Fetch result/error inline alerts (kept from existing pattern) */}
            {fetchResult && (
              <Alert
                icon={<IconCheck size={16} />}
                color="teal"
                variant="light"
                title="Fetch complete"
                withCloseButton
                onClose={() => setFetchResult(null)}
              >
                Fetched {fetchResult.fetched} coins, {fetchResult.failed} failed (out of{' '}
                {fetchResult.total} total) for {fetchResult.timeframe}.
              </Alert>
            )}
            {fetchError && (
              <Alert
                color="red"
                variant="light"
                title="Fetch failed"
                withCloseButton
                onClose={() => setFetchError(null)}
              >
                {fetchError}
              </Alert>
            )}
          </Stack>
        </Paper>

        {/* SCAN-04: Scan error */}
        {scanError && (
          <Alert color="red" variant="light" title="Scan failed">
            <Text>{scanError}</Text>
            <Text size="xs" c="dimmed" mt="xs">
              Make sure the API is running: <code>uv run python run_api.py</code>
            </Text>
          </Alert>
        )}

        {/* D-24: Dropped-for-completeness Alert (only when dropped.length > 0) */}
        {scanResponse && dropped.length > 0 && !droppedDismissed && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="gray"
            variant="light"
            title="Some coins were excluded from the scan"
            withCloseButton
            onClose={() => setDroppedDismissed(true)}
          >
            <Text size="sm">
              Scanned {scanResponse.scanned} pairs from {cachedCount} cached coins. Excluded{' '}
              {dropped.length} coins for incomplete data:
            </Text>
            <Text size="xs" c="dimmed" mt="xs">
              {dropped.join(', ')}
            </Text>
          </Alert>
        )}

        {/* D-07: Stats Paper cards above tables, keeps section headings as orientation */}
        {scanResponse && (
          <Group gap="lg">
            <Paper p="sm" px="md" radius="sm" withBorder>
              <Text size="xs" c="dimmed">Pairs scanned</Text>
              <Text size="lg" fw={700}>{scanResponse.scanned}</Text>
            </Paper>
            <Paper p="sm" px="md" radius="sm" withBorder>
              <Text size="xs" c="dimmed">Cointegrated</Text>
              <Text size="lg" fw={700} c="teal.4">{cointegrated.length}</Text>
            </Paper>
            <Paper p="sm" px="md" radius="sm" withBorder>
              <Text size="xs" c="dimmed">Not cointegrated</Text>
              <Text size="lg" fw={700} c="red.4">{notCointegrated.length}</Text>
            </Paper>
          </Group>
        )}

        {/* D-05: Two stacked sections */}
        {scanResponse && (
          <>
            <ScannerSection
              title={`Cointegrated (${cointegrated.length})`}
              accent="teal"
              pairs={cointegrated}
              timeframe={timeframe}
              onRowClick={handleRowClick}
            />
            <ScannerSection
              title={`Not cointegrated (${notCointegrated.length})`}
              accent="dimmed"
              pairs={notCointegrated}
              timeframe={timeframe}
              onRowClick={handleRowClick}
            />
          </>
        )}
      </Stack>
    </Container>
  );
}

// ---------------------------------------------------------------------------
// Suspense wrapper (Next.js 16 useSearchParams requirement)
// ---------------------------------------------------------------------------

export default function ScannerPage() {
  return (
    <Suspense fallback={null}>
      <ScannerContent />
    </Suspense>
  );
}
