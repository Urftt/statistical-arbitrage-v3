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
 * Lesson 3.2 — Z-Scores: Standardizing the Spread
 *
 * Interactive slider controls the rolling window size. Users watch how
 * window size affects the smoothness and responsiveness of z-scores.
 */
export function Lesson3_2() {
  const [window, setWindow] = useState(40);

  const n = 300;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.7 + Math.cos(i * 269.5 + seed * 0.7) * 0.5;

  // Generate a mean-reverting spread with varying volatility regimes
  const rawSpread = useMemo(() => {
    const values: number[] = [0];
    for (let i = 1; i < n; i++) {
      // Volatility regime shifts for visual interest
      const volMultiplier = i > 100 && i < 180 ? 1.8 : i > 220 ? 1.4 : 1.0;
      const meanLevel = i > 150 ? 0.5 : 0; // slight mean shift
      const decay = 0.93;
      values.push(
        (values[i - 1] - meanLevel) * decay + meanLevel + noise(i, 311.7) * 1.2 * volMultiplier
      );
    }
    return values;
  }, []);

  // Compute rolling mean, rolling std, and z-score
  const { rollingMean, rollingStd, zScore } = useMemo(() => {
    const mean: (number | null)[] = [];
    const std: (number | null)[] = [];
    const z: (number | null)[] = [];

    for (let i = 0; i < n; i++) {
      if (i < window - 1) {
        mean.push(null);
        std.push(null);
        z.push(null);
        continue;
      }
      const slice = rawSpread.slice(i - window + 1, i + 1);
      const m = slice.reduce((a, b) => a + b, 0) / slice.length;
      const s = Math.sqrt(
        slice.reduce((a, b) => a + (b - m) ** 2, 0) / slice.length
      );
      mean.push(m);
      std.push(s);
      z.push(s > 0.001 ? (rawSpread[i] - m) / s : 0);
    }

    return { rollingMean: mean, rollingStd: std, zScore: z };
  }, [rawSpread, window]);

  const windowLabel =
    window < 30
      ? 'Short window — responsive but noisy z-scores'
      : window < 60
        ? 'Medium window — good balance of smoothness and responsiveness'
        : window < 90
          ? 'Long window — smoother but slower to adapt'
          : 'Very long window — very smooth but may miss regime changes';

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"A raw spread value like \"3.2\" tells you nothing on its own. Is that a big deviation? Small? It depends on how much the spread normally moves. The "}
          <GlossaryLink term="Z-Score" />
          {" solves this by measuring deviations in units of "}
          <GlossaryLink term="Standard Deviation" />
          {"."}
        </Text>
        <Text>
          {"The transformation has three steps:"}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"Step-by-step transformation"}</Title>
        <Text>
          <strong>{"1. Start with the raw spread."}</strong>
          {" This is price_A - \u03B2 \u00D7 price_B from the previous lesson. It oscillates around some mean, but the scale varies over time."}
        </Text>
        <Text>
          <strong>{"2. Subtract the rolling mean."}</strong>
          {" This centers the spread around zero. We use a rolling window (not the global mean) because the spread's equilibrium can shift over time."}
        </Text>
        <Text>
          <strong>{"3. Divide by the rolling standard deviation."}</strong>
          {" This normalizes the scale. Now a value of +2.0 always means \"two standard deviations above the rolling mean\" — regardless of whether the spread normally moves \u00B10.5 or \u00B15.0."}
        </Text>
        <Text>
          {"The formula: "}
          <Text component="span" ff="monospace" fw={600} c="blue.4">
            {"z = (spread - rolling_mean) / rolling_std"}
          </Text>
        </Text>
      </Stack>

      {/* Interactive slider */}
      <Stack gap="sm">
        <Title order={4}>{"Choose the lookback window"}</Title>
        <Text size="sm" c="dimmed">
          {"The rolling window determines how many past bars to use for the mean and standard deviation. A short window reacts fast but is noisy. A long window is smoother but adapts slowly."}
        </Text>

        <Text size="sm" fw={600} c="blue.4">
          {windowLabel}
        </Text>

        <Slider
          value={window}
          onChange={setWindow}
          min={20}
          max={120}
          step={5}
          marks={[
            { value: 20, label: '20' },
            { value: 40, label: '40' },
            { value: 60, label: '60' },
            { value: 80, label: '80' },
            { value: 100, label: '100' },
            { value: 120, label: '120' },
          ]}
          label={(v) => `${v} bars`}
          color="blue"
        />

        {/* Raw spread chart */}
        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: rawSpread,
              type: 'scatter',
              mode: 'lines',
              name: 'Raw Spread',
              line: { color: '#CC5DE8', width: 1.5 },
            },
            {
              x: timestamps,
              y: rollingMean,
              type: 'scatter',
              mode: 'lines',
              name: `Rolling Mean (${window})`,
              line: { color: '#FF922B', width: 2, dash: 'dash' },
            },
          ]}
          layout={{
            title: `Raw Spread with Rolling Mean (window = ${window})`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Spread' } },
            height: 260,
            showlegend: true,
            legend: { x: 0, y: 1.12, orientation: 'h' },
          }}
        />

        {/* Z-score chart */}
        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: zScore,
              type: 'scatter',
              mode: 'lines',
              name: 'Z-Score',
              line: { color: '#339AF0', width: 2 },
            },
            // +2 sigma
            {
              x: [0, n - 1],
              y: [2, 2],
              type: 'scatter',
              mode: 'lines',
              name: '+2\u03C3',
              line: { color: '#FF6B6B', width: 1, dash: 'dot' },
            },
            // +1 sigma
            {
              x: [0, n - 1],
              y: [1, 1],
              type: 'scatter',
              mode: 'lines',
              name: '+1\u03C3',
              line: { color: '#FF922B', width: 1, dash: 'dot' },
            },
            // zero
            {
              x: [0, n - 1],
              y: [0, 0],
              type: 'scatter',
              mode: 'lines',
              name: 'Mean',
              line: { color: '#909296', width: 1, dash: 'dash' },
              showlegend: false,
            },
            // -1 sigma
            {
              x: [0, n - 1],
              y: [-1, -1],
              type: 'scatter',
              mode: 'lines',
              name: '-1\u03C3',
              line: { color: '#FF922B', width: 1, dash: 'dot' },
              showlegend: false,
            },
            // -2 sigma
            {
              x: [0, n - 1],
              y: [-2, -2],
              type: 'scatter',
              mode: 'lines',
              name: '-2\u03C3',
              line: { color: '#FF6B6B', width: 1, dash: 'dot' },
              showlegend: false,
            },
          ]}
          layout={{
            title: `Z-Score (window = ${window})`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Z-Score (\u03C3)' }, range: [-4, 4] },
            height: 300,
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"Why z-scores make thresholds universal"}</Title>
        <Text>
          {"Without normalization, you'd need different thresholds for every pair. One pair's spread might range from -0.5 to +0.5, while another ranges from -10 to +10. A threshold of \"2.0\" would be meaningless for the first pair and too tight for the second."}
        </Text>
        <Text>
          {"With z-scores, a threshold of 2.0 always means the same thing: "}
          <em>{"two standard deviations from the rolling mean"}</em>
          {". This makes your strategy parameters transferable across different pairs without re-tuning."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" now that we can measure when the spread is \"extreme,\" let's turn z-scores into actual trading signals with "}
        <GlossaryLink term="Entry Signal">{"entry"}</GlossaryLink>
        {" and "}
        <GlossaryLink term="Exit Signal">{"exit"}</GlossaryLink>
        {" thresholds."}
      </Text>
    </Stack>
  );
}
