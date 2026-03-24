'use client';

import { useState, useEffect } from 'react';
import {
  Alert,
  Box,
  Loader,
  SegmentedControl,
  Stack,
  Text,
  Title,
  Center,
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { fetchOHLCV, type OHLCVResponse } from '@/lib/api';

const EXAMPLE_PAIRS = [
  {
    label: 'ETH × ETC',
    asset1: 'ETH/EUR',
    asset2: 'ETC/EUR',
    description: 'Both Ethereum-based — share technology and community overlap.',
    commentary:
      'Notice how the lines track each other? The gap opens and closes but stays bounded. This co-movement is exactly what we need.',
    commentaryColor: 'teal',
  },
  {
    label: 'BTC × LTC',
    asset1: 'BTC/EUR',
    asset2: 'LTC/EUR',
    description: 'Litecoin was forked from Bitcoin — historically correlated.',
    commentary:
      'These trend in the same direction, but the relationship is looser. The gap sometimes widens for extended periods.',
    commentaryColor: 'yellow',
  },
  {
    label: 'BTC × XRP',
    asset1: 'BTC/EUR',
    asset2: 'XRP/EUR',
    description: 'Fundamentally different — BTC (store of value) vs XRP (payments).',
    commentary:
      'See how their paths diverge with no clear pull-back? This pair would be risky for stat arb — the gap might just keep growing.',
    commentaryColor: 'orange',
  },
] as const;

function normalizeToPercent(prices: number[]): number[] {
  const first = prices[0];
  if (!first) return prices;
  return prices.map((p) => ((p - first) / first) * 100);
}

function epochToDate(ts: number): string {
  return new Date(ts).toISOString().split('T')[0];
}

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
    setData1(null);
    setData2(null);

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
            : 'Failed to load data'
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [pair.asset1, pair.asset2]);

  const hasData = data1 && data2 && !error;
  const dates = data1?.timestamps.map(epochToDate) ?? [];
  const norm1 = data1 ? normalizeToPercent(data1.close) : [];
  const norm2 = data2 ? normalizeToPercent(data2.close) : [];
  // Spread = difference in normalized % returns — shows gap opening/closing
  const spreadData = norm1.map((v, i) => v - (norm2[i] ?? 0));

  return (
    <Stack gap="xl">
      {/* 1-2 sentence intro + interactive element immediately */}
      <Text>
        {"Switch between three real crypto pairs — look for lines that "}
        <em>{"track each other"}</em>
        {". That co-movement is the raw material for "}
        <GlossaryLink term="Pairs Trading" />
        {"."}
      </Text>

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

      {/* Data loading states */}
      {loading && (
        <Center py="xl">
          <Loader size="sm" mr="sm" />
          <Text c="dimmed" size="sm">Loading price data...</Text>
        </Center>
      )}

      {error && (
        <Alert
          color="yellow"
          variant="light"
          icon={<IconAlertCircle size={18} />}
          title="Could not load live data"
        >
          <Text size="sm">
            The API server doesn&apos;t seem to be running, or no cached data is available
            for these pairs.
          </Text>
          <Text size="sm" mt="xs" c="dimmed">
            {"To fix: run "}<code>{"uv run python run_api.py"}</code>
            {" in a terminal. The API needs cached OHLCV data in the "}
            <code>{"data/"}</code>
            {" directory."}
          </Text>
          <Text size="sm" mt="xs" c="dimmed">
            Don&apos;t worry — you can continue to the next chapter. We&apos;ll use this
            data in later lessons.
          </Text>
        </Alert>
      )}

      {hasData && !loading && (
        <Stack gap="md">
          <PlotlyChart
            data={[
              {
                x: dates,
                y: norm1,
                type: 'scatter',
                mode: 'lines',
                name: pair.asset1.split('/')[0],
                line: { color: '#339AF0', width: 2 },
              },
              {
                x: dates.slice(0, norm2.length),
                y: norm2,
                type: 'scatter',
                mode: 'lines',
                name: pair.asset2.split('/')[0],
                line: { color: '#51CF66', width: 2 },
              },
            ]}
            layout={{
              title: `${pair.label} — % Change (Last 180 Days)`,
              xaxis: { title: { text: 'Date' } },
              yaxis: { title: { text: '% Change' } },
              height: 400,
              showlegend: true,
              legend: { x: 0, y: 1.12, orientation: 'h' },
            }}
          />

          <PlotlyChart
            data={[
              {
                x: dates.slice(0, spreadData.length),
                y: spreadData,
                type: 'scatter',
                mode: 'lines',
                name: 'Spread (% gap)',
                line: { color: '#CC5DE8', width: 2 },
                fill: 'tozeroy',
                fillcolor: 'rgba(204, 93, 232, 0.1)',
              },
              {
                x: [dates[0], dates[dates.length - 1]],
                y: [0, 0],
                type: 'scatter',
                mode: 'lines',
                line: { color: '#909296', width: 1, dash: 'dash' },
                showlegend: false,
              },
            ]}
            layout={{
              title: `Spread: ${pair.asset1.split('/')[0]} − ${pair.asset2.split('/')[0]} (% Gap)`,
              xaxis: { title: { text: 'Date' } },
              yaxis: { title: { text: '% Spread' } },
              height: 280,
              showlegend: false,
            }}
          />

          <Text size="sm" c={pair.commentaryColor}>
            {pair.commentary}
          </Text>
        </Stack>
      )}

      {/* Detailed explanation BELOW the charts */}
      <Stack gap="md">
        <Text>
          {"You've seen how stat arb works with simulated data. Now you're looking at "}
          <strong>{"real crypto prices"}</strong>
          {", normalized to percentage change so we can compare assets at completely different price levels (BTC at €50,000 vs. LTC at €80)."}
        </Text>
        <Text>
          {"The purple spread chart below the prices shows the "}
          <em>{"gap"}</em>
          {" between the two assets. When it bounces around zero and stays bounded, that's a tradeable pair. When it drifts away with no pull-back, that pair is risky for stat arb."}
        </Text>
      </Stack>

      {/* Chapter 1 wrap-up */}
      <Stack gap="sm" mt="md">
        <Title order={4}>Chapter 1 wrap-up</Title>
        <Text>
          You now have the big picture:
        </Text>
        <Text>
          <strong>{"1."}</strong>
          {" Stat arb profits from temporary mispricings between related assets."}
        </Text>
        <Text>
          <strong>{"2."}</strong>
          {" Pairs trading is market-neutral — long one, short the other."}
        </Text>
        <Text>
          <strong>{"3."}</strong>
          {" Real pairs show varying degrees of co-movement — some are tradeable, some aren't."}
        </Text>
        <Text c="dimmed" size="sm" mt="xs">
          {"But how do we "}
          <em>{"measure"}</em>
          {" whether two assets truly belong together? Eyeballing charts isn't rigorous enough. In Chapter 2, we'll learn the difference between "}
          <GlossaryLink term="Correlation" />
          {" and "}
          <GlossaryLink term="Cointegration" />
          {" — and why only one of them matters for pairs trading."}
        </Text>
      </Stack>
    </Stack>
  );
}
