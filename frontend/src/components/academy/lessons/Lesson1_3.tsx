'use client';

import { useState, useEffect } from 'react';
import {
  Alert,
  Card,
  Group,
  Loader,
  SegmentedControl,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Center,
} from '@mantine/core';
import { IconBulb, IconChartLine } from '@tabler/icons-react';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { fetchOHLCV, type OHLCVResponse } from '@/lib/api';

/** Pre-selected example pairs that show interesting behaviour. */
const EXAMPLE_PAIRS = [
  {
    label: 'ETH × ETC',
    asset1: 'ETH/EUR',
    asset2: 'ETC/EUR',
    description: 'Both Ethereum-based — share technology and community overlap',
  },
  {
    label: 'BTC × LTC',
    asset1: 'BTC/EUR',
    asset2: 'LTC/EUR',
    description: 'Litecoin was forked from Bitcoin — historically correlated',
  },
  {
    label: 'BTC × XRP',
    asset1: 'BTC/EUR',
    asset2: 'XRP/EUR',
    description: 'Very different assets — BTC (store of value) vs XRP (payments)',
  },
] as const;

function normalizeToPercent(prices: number[]): number[] {
  const first = prices[0];
  if (first === 0) return prices;
  return prices.map((p) => ((p - first) / first) * 100);
}

function epochToDate(ts: number): string {
  return new Date(ts).toISOString().split('T')[0];
}

/**
 * Lesson 1.3 — Your First Look at Real Data
 *
 * Loads real OHLCV data from the API and shows normalized price series
 * for pre-selected pairs. User can toggle between pairs to see which
 * ones "move together" and which don't.
 */
export function Lesson1_3() {
  const [pairIndex, setPairIndex] = useState(0);
  const [data1, setData1] = useState<OHLCVResponse | null>(null);
  const [data2, setData2] = useState<OHLCVResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pair = EXAMPLE_PAIRS[pairIndex];

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchOHLCV(pair.asset1, '1d', 180),
      fetchOHLCV(pair.asset2, '1d', 180),
    ])
      .then(([d1, d2]) => {
        if (cancelled) return;
        setData1(d1);
        setData2(d2);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load data. Is the API running?'
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [pair.asset1, pair.asset2]);

  const hasData = data1 && data2 && !error;

  // Normalize both to % change from first point
  const dates1 = data1?.timestamps.map(epochToDate) ?? [];
  const norm1 = data1 ? normalizeToPercent(data1.close) : [];
  const norm2 = data2 ? normalizeToPercent(data2.close) : [];

  return (
    <Stack gap="xl">
      {/* Context */}
      <Card padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Title order={4}>From Theory to Reality</Title>
          <Text>
            You&apos;ve seen how stat arb works in theory. Now let&apos;s look at{' '}
            <strong>real crypto prices</strong> and see which pairs actually move
            together. We&apos;ll normalize prices to percentage change so we can
            compare assets at different price levels (BTC at €50,000 vs. LTC at €80).
          </Text>
          <Text size="sm" c="dimmed">
            Switch between the three pairs below. Look for pairs where the lines
            track each other closely — that&apos;s the co-movement we need for{' '}
            <GlossaryLink term="Pairs Trading">pairs trading</GlossaryLink>.
          </Text>
        </Stack>
      </Card>

      {/* Pair selector */}
      <SegmentedControl
        value={String(pairIndex)}
        onChange={(v) => setPairIndex(Number(v))}
        data={EXAMPLE_PAIRS.map((p, i) => ({
          label: p.label,
          value: String(i),
        }))}
        fullWidth
      />

      <Text size="sm" c="dimmed" ta="center">
        {pair.description}
      </Text>

      {/* Chart */}
      <Card padding="lg" radius="md" withBorder>
        {loading && (
          <Center py="xl">
            <Loader size="md" />
            <Text ml="sm" c="dimmed">
              Loading price data...
            </Text>
          </Center>
        )}

        {error && (
          <Alert color="red" variant="light" title="Could not load data">
            <Text size="sm">{error}</Text>
            <Text size="xs" c="dimmed" mt="xs">
              Make sure the API server is running:{' '}
              <code>uv run python run_api.py</code>
            </Text>
          </Alert>
        )}

        {hasData && !loading && (
          <Stack gap="md">
            <PlotlyChart
              data={[
                {
                  x: dates1,
                  y: norm1,
                  type: 'scatter',
                  mode: 'lines',
                  name: pair.asset1.split('/')[0],
                  line: { color: '#339AF0', width: 2 },
                },
                {
                  x: dates1.slice(0, norm2.length),
                  y: norm2,
                  type: 'scatter',
                  mode: 'lines',
                  name: pair.asset2.split('/')[0],
                  line: { color: '#51CF66', width: 2 },
                },
              ]}
              layout={{
                title: `${pair.label} — Normalized Price Change (Last 180 Days)`,
                xaxis: { title: { text: 'Date' } },
                yaxis: { title: { text: '% Change from Start' } },
                height: 400,
                showlegend: true,
                legend: { x: 0, y: 1.15, orientation: 'h' },
              }}
            />

            {pairIndex === 0 && (
              <Alert variant="light" color="teal">
                <Text size="sm">
                  <strong>ETH & ETC</strong> share Ethereum DNA — notice how they
                  tend to move together? The gap opens and closes. This
                  co-movement is exactly what we need for pairs trading.
                </Text>
              </Alert>
            )}
            {pairIndex === 1 && (
              <Alert variant="light" color="teal">
                <Text size="sm">
                  <strong>BTC & LTC</strong> are historically linked — Litecoin was
                  forked from Bitcoin. They often trend in the same direction,
                  though the relationship has weakened over the years.
                </Text>
              </Alert>
            )}
            {pairIndex === 2 && (
              <Alert variant="light" color="orange">
                <Text size="sm">
                  <strong>BTC & XRP</strong> are fundamentally different assets.
                  Notice how their percentage changes often diverge with no clear
                  pull-back? This pair would be <em>risky</em> for stat arb — the
                  gap might keep widening.
                </Text>
              </Alert>
            )}
          </Stack>
        )}
      </Card>

      {/* What did we learn */}
      <Alert
        variant="light"
        color="blue"
        title="Key Takeaway"
        icon={<IconBulb size={20} />}
      >
        <Text size="sm">
          Not all pairs are created equal. Some assets genuinely move together (ETH & ETC),
          while others just happen to trend in the same direction sometimes (BTC & XRP).
          Visually comparing normalized prices gives you <strong>intuition</strong>, but
          we need a rigorous statistical test to tell them apart. That test is called{' '}
          <GlossaryLink term="Cointegration">cointegration</GlossaryLink> — and it&apos;s
          the topic of Chapter 2.
        </Text>
      </Alert>

      {/* Chapter 1 summary */}
      <Card padding="lg" radius="md" withBorder bg="dark.6">
        <Stack gap="sm">
          <Group gap="sm">
            <ThemeIcon size="lg" variant="light" color="green">
              <IconChartLine size={20} />
            </ThemeIcon>
            <Title order={4}>Chapter 1 Complete!</Title>
          </Group>
          <Text size="sm">
            You now understand the big picture:
          </Text>
          <Stack gap={4} ml="md">
            <Text size="sm">
              <strong>1.</strong> Stat arb profits from temporary mispricings between related assets
            </Text>
            <Text size="sm">
              <strong>2.</strong> Pairs trading is market-neutral — long one, short the other
            </Text>
            <Text size="sm">
              <strong>3.</strong> Real crypto pairs show varying degrees of co-movement
            </Text>
          </Stack>
          <Text size="sm" c="dimmed" mt="xs">
            Next chapter: we&apos;ll learn how to <em>measure</em> whether two assets
            truly belong together — correlation vs. cointegration.
          </Text>
        </Stack>
      </Card>
    </Stack>
  );
}
