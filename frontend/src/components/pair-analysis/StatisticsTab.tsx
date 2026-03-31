import { useState, useEffect } from 'react';
import {
  Alert,
  Badge,
  Group,
  Paper,
  Select,
  SimpleGrid,
  Skeleton,
  Slider,
  Stack,
  Text,
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import PlotlyChart from '@/components/charts/PlotlyChart';
import {
  postCointegration,
  type CointegrationResponse,
} from '@/lib/api';
import { usePairContext } from '@/contexts/PairContext';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const LOOKBACK_OPTIONS = [
  { value: '90', label: '90 days' },
  { value: '180', label: '180 days' },
  { value: '365', label: '1 year' },
  { value: '730', label: '2 years' },
];

// ---------------------------------------------------------------------------
// Badge helpers
// ---------------------------------------------------------------------------

function pValueBadge(v: number): { color: string; label: string } {
  if (v < 0.01) return { color: 'green', label: 'Strong' };
  if (v <= 0.05) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Weak' };
}

function halfLifeBadge(v: number | null): { color: string; label: string } {
  if (v === null) return { color: 'gray', label: 'N/A' };
  if (v < 20) return { color: 'green', label: 'Fast' };
  if (v <= 50) return { color: 'yellow', label: 'Medium' };
  return { color: 'red', label: 'Slow' };
}

function hedgeRatioBadge(v: number): { color: string; label: string } {
  if (v >= 0.5 && v <= 2.0) return { color: 'green', label: 'Balanced' };
  return { color: 'yellow', label: 'Skewed' };
}

function correlationBadge(v: number): { color: string; label: string } {
  if (v > 0.7) return { color: 'green', label: 'High' };
  if (v >= 0.4) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Low' };
}

function cointScoreBadge(v: number): { color: string; label: string } {
  if (v > 70) return { color: 'green', label: 'Strong' };
  if (v >= 40) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Weak' };
}

// ---------------------------------------------------------------------------
// Z-score threshold shapes
// ---------------------------------------------------------------------------

function buildZScoreShapes(entry: number, exit: number) {
  return [
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: entry, y1: entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: -entry, y1: -entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: exit, y1: exit, line: { color: '#FCC419', width: 1, dash: 'dot' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: -exit, y1: -exit, line: { color: '#FCC419', width: 1, dash: 'dot' as const } },
  ];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function StatisticsTab() {
  const { asset1, asset2, timeframe } = usePairContext();

  const [daysBack, setDaysBack] = useState<string>('365');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CointegrationResponse | null>(null);
  const [entryThreshold, setEntryThreshold] = useState<number>(2.0);
  const [exitThreshold, setExitThreshold] = useState<number>(0.5);

  useEffect(() => {
    let cancelled = false;

    if (!asset1 || !asset2) return;

    setLoading(true);
    setError(null);

    postCointegration({ asset1, asset2, timeframe, days_back: Number(daysBack) })
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load statistics');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [asset1, asset2, timeframe, daysBack]);

  // Error state
  if (error && !loading) {
    return (
      <Alert
        color="red"
        variant="light"
        icon={<IconAlertCircle size={16} />}
        title="Could not load statistics"
      >
        Failed to fetch cointegration data for {asset1} / {asset2}. Check that
        data is cached for this pair, then try again.
      </Alert>
    );
  }

  const dates = data
    ? data.timestamps.map((ts) => new Date(ts).toISOString())
    : [];

  // Stat card definitions
  const cards = data
    ? [
        {
          label: 'P-Value',
          value: data.p_value.toFixed(4),
          badge: pValueBadge(data.p_value),
        },
        {
          label: 'Half-Life',
          value:
            data.half_life !== null
              ? data.half_life.toFixed(1) + ' bars'
              : 'N/A',
          badge: halfLifeBadge(data.half_life),
        },
        {
          label: 'Hedge Ratio',
          value: data.hedge_ratio.toFixed(4),
          badge: hedgeRatioBadge(data.hedge_ratio),
        },
        {
          label: 'Correlation',
          value: data.correlation.toFixed(2),
          badge: correlationBadge(data.correlation),
        },
        {
          label: 'Coint. Score',
          value: Math.round(data.cointegration_score) + '/100',
          badge: cointScoreBadge(data.cointegration_score),
        },
      ]
    : null;

  return (
    <Stack gap="lg">
      {/* Lookback row */}
      <Group justify="space-between" align="center">
        <Text size="sm" c="dimmed">
          Lookback period
        </Text>
        <Select
          size="sm"
          w={160}
          data={LOOKBACK_OPTIONS}
          value={daysBack}
          onChange={(v) => v && setDaysBack(v)}
        />
      </Group>

      {/* Stat cards */}
      {loading ? (
        <SimpleGrid cols={{ base: 2, sm: 3, lg: 5 }} spacing="md">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} height={80} />
          ))}
        </SimpleGrid>
      ) : cards ? (
        <SimpleGrid cols={{ base: 2, sm: 3, lg: 5 }} spacing="md">
          {cards.map((card) => (
            <Paper key={card.label} p="md" radius="sm">
              <Stack gap="xs">
                <Text size="xs" c="dimmed" tt="uppercase">
                  {card.label}
                </Text>
                <Text size="lg" fw={700}>
                  {card.value}
                </Text>
                <Badge size="sm" variant="light" color={card.badge.color}>
                  {card.badge.label}
                </Badge>
              </Stack>
            </Paper>
          ))}
        </SimpleGrid>
      ) : null}

      {/* Spread chart */}
      {loading ? (
        <Skeleton height={260} />
      ) : data ? (
        <Paper p="md">
          <PlotlyChart
            data={[
              {
                type: 'scatter',
                x: dates,
                y: data.spread,
                mode: 'lines',
                name: 'Spread',
              },
            ]}
            layout={{ title: 'Spread', height: 260 }}
            config={{ displayModeBar: false, scrollZoom: true }}
          />
        </Paper>
      ) : null}

      {/* Z-score chart */}
      {loading ? (
        <Skeleton height={240} />
      ) : data ? (
        <Paper p="md">
          <PlotlyChart
            data={[
              {
                type: 'scatter',
                x: dates,
                y: data.zscore,
                mode: 'lines',
                name: 'Z-Score',
              },
            ]}
            layout={{
              title: 'Z-Score',
              height: 240,
              shapes: buildZScoreShapes(entryThreshold, exitThreshold),
            }}
            config={{ displayModeBar: false, scrollZoom: true }}
          />
        </Paper>
      ) : null}

      {/* Threshold sliders */}
      <Stack gap="sm">
        <Group justify="space-between">
          <Text size="sm">Entry Threshold</Text>
          <Text size="sm" fw={700}>
            &plusmn; {entryThreshold.toFixed(1)}
          </Text>
        </Group>
        <Slider
          min={0.5}
          max={4.0}
          step={0.1}
          value={entryThreshold}
          onChange={setEntryThreshold}
          color="red"
        />

        <Group justify="space-between">
          <Text size="sm">Exit Threshold</Text>
          <Text size="sm" fw={700}>
            &plusmn; {exitThreshold.toFixed(1)}
          </Text>
        </Group>
        <Slider
          min={0.0}
          max={2.0}
          step={0.1}
          value={exitThreshold}
          onChange={setExitThreshold}
          color="yellow"
        />
      </Stack>
    </Stack>
  );
}
