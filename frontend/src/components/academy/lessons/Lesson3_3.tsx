'use client';

import { useMemo, useState } from 'react';
import {
  Slider,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 3.3 — Entry & Exit Signals
 *
 * Two interactive sliders control entry and exit z-score thresholds.
 * The chart shows signal markers updating in real-time as users adjust thresholds.
 */
export function Lesson3_3() {
  const [entryThreshold, setEntryThreshold] = useState(2.0);
  const [exitThreshold, setExitThreshold] = useState(0.5);

  const n = 300;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.7 + Math.cos(i * 269.5 + seed * 0.7) * 0.5;

  // Generate a mean-reverting spread and compute z-scores with fixed window
  const zScore = useMemo(() => {
    const rawSpread: number[] = [0];
    for (let i = 1; i < n; i++) {
      const vol = i > 80 && i < 160 ? 1.6 : i > 200 && i < 260 ? 1.5 : 1.0;
      rawSpread.push(rawSpread[i - 1] * 0.92 + noise(i, 311.7) * 1.4 * vol);
    }

    const window = 40;
    const z: number[] = [];
    for (let i = 0; i < n; i++) {
      if (i < window - 1) {
        z.push(0);
        continue;
      }
      const slice = rawSpread.slice(i - window + 1, i + 1);
      const m = slice.reduce((a, b) => a + b, 0) / slice.length;
      const s = Math.sqrt(
        slice.reduce((a, b) => a + (b - m) ** 2, 0) / slice.length
      );
      z.push(s > 0.001 ? (rawSpread[i] - m) / s : 0);
    }
    return z;
  }, []);

  // Generate signals based on thresholds
  const { shortSignals, longSignals, closeSignals, tradeCount } = useMemo(() => {
    const shorts: { x: number[]; y: number[] } = { x: [], y: [] };
    const longs: { x: number[]; y: number[] } = { x: [], y: [] };
    const closes: { x: number[]; y: number[] } = { x: [], y: [] };

    let inPosition: 'long' | 'short' | null = null;
    let trades = 0;

    for (let i = 40; i < n; i++) {
      const z = zScore[i];

      if (inPosition === null) {
        // Look for entry signals
        if (z >= entryThreshold) {
          shorts.x.push(i);
          shorts.y.push(z);
          inPosition = 'short';
          trades++;
        } else if (z <= -entryThreshold) {
          longs.x.push(i);
          longs.y.push(z);
          inPosition = 'long';
          trades++;
        }
      } else {
        // Look for exit signals
        if (Math.abs(z) <= exitThreshold) {
          closes.x.push(i);
          closes.y.push(z);
          inPosition = null;
        }
      }
    }

    return {
      shortSignals: shorts,
      longSignals: longs,
      closeSignals: closes,
      tradeCount: trades,
    };
  }, [zScore, entryThreshold, exitThreshold]);

  const entryLabel =
    entryThreshold < 1.5
      ? 'Low entry threshold — many signals, but more false positives'
      : entryThreshold < 2.2
        ? 'Moderate entry threshold — balanced trade-off'
        : 'High entry threshold — fewer but higher-conviction signals';

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"Now we turn z-scores into actionable signals. The logic is simple: when the spread deviates far enough from its mean, we bet it will come back. This is the core of "}
          <GlossaryLink term="Pairs Trading" />
          {" — buy low, sell high, but for spreads."}
        </Text>
        <Text>
          {"We need two thresholds: an "}
          <GlossaryLink term="Entry Signal">{"entry threshold"}</GlossaryLink>
          {" that says \"the spread is extreme enough to trade,\" and an "}
          <GlossaryLink term="Exit Signal">{"exit threshold"}</GlossaryLink>
          {" that says \"the spread has reverted enough to close the position.\""}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"Signal logic"}</Title>
        <Text>
          <strong>{"Short the spread"}</strong>
          {" (red triangles) when z > entry threshold. The spread is unusually high — sell A, buy B, and wait for the spread to shrink."}
        </Text>
        <Text>
          <strong>{"Long the spread"}</strong>
          {" (green triangles) when z < -entry threshold. The spread is unusually low — buy A, sell B, and wait for the spread to grow."}
        </Text>
        <Text>
          <strong>{"Close position"}</strong>
          {" (gray dots) when |z| < exit threshold. The spread has reverted close enough to the mean — take your profit and step aside."}
        </Text>
      </Stack>

      {/* Interactive sliders */}
      <Stack gap="sm">
        <Title order={4}>{"Set your thresholds"}</Title>
        <Text size="sm" c="dimmed">
          {"Adjust both sliders and watch the signals update. Tighter entry means more trades; wider entry means fewer but more selective. The exit threshold controls when you take profit."}
        </Text>

        <Text size="sm" fw={600} c="blue.4">
          {entryLabel}
        </Text>

        <Text size="sm" fw={500}>{"Entry threshold (z-score)"}</Text>
        <Slider
          value={entryThreshold}
          onChange={setEntryThreshold}
          min={1.0}
          max={3.0}
          step={0.1}
          marks={[
            { value: 1.0, label: '1.0' },
            { value: 1.5, label: '1.5' },
            { value: 2.0, label: '2.0' },
            { value: 2.5, label: '2.5' },
            { value: 3.0, label: '3.0' },
          ]}
          label={(v) => `\u00B1${v.toFixed(1)}\u03C3`}
          color="blue"
        />

        <Text size="sm" fw={500} mt="sm">{"Exit threshold (z-score)"}</Text>
        <Slider
          value={exitThreshold}
          onChange={setExitThreshold}
          min={0.0}
          max={1.5}
          step={0.1}
          marks={[
            { value: 0.0, label: '0.0' },
            { value: 0.5, label: '0.5' },
            { value: 1.0, label: '1.0' },
            { value: 1.5, label: '1.5' },
          ]}
          label={(v) => `\u00B1${v.toFixed(1)}\u03C3`}
          color="gray"
        />

        <Text size="sm" fw={600} c="blue.4">
          {`Trades triggered: ${tradeCount} | Short entries: ${shortSignals.x.length} | Long entries: ${longSignals.x.length} | Closes: ${closeSignals.x.length}`}
        </Text>

        <PlotlyChart
          data={[
            // Z-score line
            {
              x: timestamps,
              y: zScore,
              type: 'scatter',
              mode: 'lines',
              name: 'Z-Score',
              line: { color: '#339AF0', width: 1.5 },
            },
            // Entry threshold lines
            {
              x: [0, n - 1],
              y: [entryThreshold, entryThreshold],
              type: 'scatter',
              mode: 'lines',
              name: `Entry (+${entryThreshold.toFixed(1)}\u03C3)`,
              line: { color: '#FF6B6B', width: 1.5, dash: 'dash' },
            },
            {
              x: [0, n - 1],
              y: [-entryThreshold, -entryThreshold],
              type: 'scatter',
              mode: 'lines',
              name: `Entry (-${entryThreshold.toFixed(1)}\u03C3)`,
              line: { color: '#20C997', width: 1.5, dash: 'dash' },
              showlegend: false,
            },
            // Exit threshold lines
            {
              x: [0, n - 1],
              y: [exitThreshold, exitThreshold],
              type: 'scatter',
              mode: 'lines',
              name: `Exit (\u00B1${exitThreshold.toFixed(1)}\u03C3)`,
              line: { color: '#909296', width: 1, dash: 'dot' },
            },
            {
              x: [0, n - 1],
              y: [-exitThreshold, -exitThreshold],
              type: 'scatter',
              mode: 'lines',
              line: { color: '#909296', width: 1, dash: 'dot' },
              showlegend: false,
            },
            // Zero line
            {
              x: [0, n - 1],
              y: [0, 0],
              type: 'scatter',
              mode: 'lines',
              line: { color: '#909296', width: 0.5 },
              showlegend: false,
            },
            // Short signals (red triangles)
            {
              x: shortSignals.x,
              y: shortSignals.y,
              type: 'scatter',
              mode: 'markers',
              name: 'Short Spread',
              marker: {
                color: '#FF6B6B',
                size: 10,
                symbol: 'triangle-down',
              },
            },
            // Long signals (green triangles)
            {
              x: longSignals.x,
              y: longSignals.y,
              type: 'scatter',
              mode: 'markers',
              name: 'Long Spread',
              marker: {
                color: '#20C997',
                size: 10,
                symbol: 'triangle-up',
              },
            },
            // Close signals (gray dots)
            {
              x: closeSignals.x,
              y: closeSignals.y,
              type: 'scatter',
              mode: 'markers',
              name: 'Close Position',
              marker: {
                color: '#909296',
                size: 7,
                symbol: 'circle',
              },
            },
          ]}
          layout={{
            title: `Entry & Exit Signals (entry=\u00B1${entryThreshold.toFixed(1)}\u03C3, exit=\u00B1${exitThreshold.toFixed(1)}\u03C3)`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Z-Score (\u03C3)' }, range: [-4.5, 4.5] },
            height: 380,
            showlegend: true,
            legend: { x: 0, y: 1.18, orientation: 'h' },
          }}
        />
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"The trade-off"}</Title>
        <Text>
          {"Tight entry thresholds (1.0\u03C3) give you lots of trades, but many will be false positives — the spread wasn't really extreme enough to revert. Wide entry thresholds (3.0\u03C3) are highly selective, but you might wait forever for a signal."}
        </Text>
        <Text>
          {"The exit threshold matters too. Exiting at 0.0\u03C3 (the mean) captures the full reversion, but the spread might bounce before getting there. Exiting at 0.5\u03C3 is more conservative — you leave some profit on the table but close more reliably."}
        </Text>
        <Text>
          {"There's no single \"right\" answer — the optimal thresholds depend on the pair, the time frame, and how much risk you can tolerate. That's why we "}
          <em>{"backtest"}</em>
          {" different parameter combinations later."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" how fast does the spread actually revert? That's the "}
        <GlossaryLink term="Half-Life" />
        {" — and it tells you whether a pair reverts fast enough to be worth trading."}
      </Text>
    </Stack>
  );
}
