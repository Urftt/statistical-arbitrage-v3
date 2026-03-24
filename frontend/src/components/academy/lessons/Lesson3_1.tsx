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
 * Lesson 3.1 — Building the Spread
 *
 * Interactive slider lets users adjust the hedge ratio (beta) and watch
 * how the spread changes. Optimal beta produces a stationary spread;
 * wrong beta causes trending.
 */
export function Lesson3_1() {
  // Hedge ratio slider: true optimal is ~0.8
  const [beta, setBeta] = useState(0.8);

  const n = 200;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.6 + Math.cos(i * 269.5 + seed * 0.7) * 0.4;

  // Generate two cointegrated price series with true beta = 0.8
  const { pricesA, pricesB, spread } = useMemo(() => {
    const trueBeta = 0.8;

    // Shared random walk (common factor)
    const walk: number[] = [0];
    for (let i = 1; i < n; i++) {
      walk.push(walk[i - 1] + noise(i, 311.7) * 0.8);
    }

    // Asset A = walk + mean-reverting component + offset
    const a: number[] = [];
    let spreadState = 0;
    for (let i = 0; i < n; i++) {
      spreadState = spreadState * 0.92 + noise(i, 73.3) * 1.5;
      a.push(100 + walk[i] + spreadState);
    }

    // Asset B = (1/trueBeta) * walk + offset + small noise
    const b: number[] = [];
    for (let i = 0; i < n; i++) {
      b.push(80 + walk[i] / trueBeta + noise(i, 519.2) * 0.3);
    }

    // Spread with user-chosen beta
    const s = a.map((aVal, i) => aVal - beta * b[i]);

    return { pricesA: a, pricesB: b, spread: s };
  }, [beta]);

  // Compute spread stats for display
  const spreadMean = useMemo(
    () => spread.reduce((sum, v) => sum + v, 0) / spread.length,
    [spread]
  );
  const spreadStd = useMemo(() => {
    const mean = spreadMean;
    const variance = spread.reduce((sum, v) => sum + (v - mean) ** 2, 0) / spread.length;
    return Math.sqrt(variance);
  }, [spread, spreadMean]);

  const isOptimal = Math.abs(beta - 0.8) < 0.15;
  const label =
    beta < 0.5
      ? 'Beta too low — spread trends upward with residual exposure'
      : beta > 1.1
        ? 'Beta too high — spread trends downward (over-hedged)'
        : isOptimal
          ? 'Near optimal — spread oscillates around a stable mean'
          : Math.abs(beta - 0.8) < 0.25
            ? 'Getting close — spread has some drift but mostly bounded'
            : 'Off target — spread is drifting';

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"The "}
          <GlossaryLink term="Spread" />
          {" is the core signal in pairs trading. It measures the pricing gap between two assets after accounting for their relationship. When the spread deviates from its average, we have a potential trade."}
        </Text>
        <Text>
          {"The formula is simple: "}
          <Text component="span" ff="monospace" fw={600} c="blue.4">
            {"spread = price_A - \u03B2 \u00D7 price_B"}
          </Text>
          {" where \u03B2 (beta) is the "}
          <GlossaryLink term="Hedge Ratio" />
          {". Getting \u03B2 right is everything. Too high or too low and the spread trends instead of mean-reverting."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"How OLS finds the optimal \u03B2"}</Title>
        <Text>
          <GlossaryLink term="OLS Regression" />
          {" fits a line through the scatter of price_A vs. price_B. The slope of that line is \u03B2 — the number of units of B that \"explains\" one unit of A. When we subtract \u03B2 \u00D7 B from A, the leftover (the residual) is our spread."}
        </Text>
        <Text>
          {"If \u03B2 is correct, the residual is "}
          <GlossaryLink term="Stationarity">{"stationary"}</GlossaryLink>
          {" — it wobbles around a constant mean. If \u03B2 is wrong, the residual inherits a trend from the prices themselves."}
        </Text>
      </Stack>

      {/* Interactive chart */}
      <Stack gap="sm">
        <Title order={4}>{"Tune the hedge ratio"}</Title>
        <Text size="sm" c="dimmed">
          {"Drag the slider to adjust \u03B2. The optimal value is around 0.80 — at that point the spread is flat and mean-reverting. Move it away and watch the spread start to trend."}
        </Text>

        <Text size="sm" fw={600} c={isOptimal ? 'blue.4' : 'red.4'}>
          {label}
        </Text>

        <Slider
          value={beta}
          onChange={setBeta}
          min={0.2}
          max={1.5}
          step={0.01}
          marks={[
            { value: 0.2, label: '0.2' },
            { value: 0.8, label: '0.8 (optimal)' },
            { value: 1.5, label: '1.5' },
          ]}
          label={(v) => `\u03B2 = ${v.toFixed(2)}`}
          color={isOptimal ? 'blue' : 'red'}
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: pricesA,
              type: 'scatter',
              mode: 'lines',
              name: 'Asset A',
              line: { color: '#339AF0', width: 2 },
            },
            {
              x: timestamps,
              y: pricesB,
              type: 'scatter',
              mode: 'lines',
              name: 'Asset B',
              line: { color: '#51CF66', width: 2 },
            },
          ]}
          layout={{
            title: 'Price Series: Asset A and Asset B',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Price' } },
            height: 280,
            showlegend: true,
            legend: { x: 0, y: 1.12, orientation: 'h' },
          }}
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: spread,
              type: 'scatter',
              mode: 'lines',
              name: 'Spread',
              line: {
                color: isOptimal ? '#CC5DE8' : '#FF6B6B',
                width: 2,
              },
            },
            {
              x: [0, n - 1],
              y: [spreadMean, spreadMean],
              type: 'scatter',
              mode: 'lines',
              name: 'Mean',
              line: { color: '#909296', width: 1, dash: 'dash' },
              showlegend: false,
            },
          ]}
          layout={{
            title: isOptimal
              ? `Spread (\u03B2=${beta.toFixed(2)}): Stationary \u2014 Mean-Reverting`
              : `Spread (\u03B2=${beta.toFixed(2)}): Trending \u2014 Not Tradeable`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Spread Value' } },
            height: 280,
            showlegend: false,
          }}
        />

        <Text size="sm" c="dimmed">
          {`Spread mean: ${spreadMean.toFixed(2)} | Spread std: ${spreadStd.toFixed(2)}`}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"Why the hedge ratio matters"}</Title>
        <Text>
          {"The hedge ratio tells you how many units of B to trade per unit of A. If \u03B2 = 0.8, you'd go long 1 unit of A and short 0.8 units of B (or vice versa). This makes the combined position "}
          <GlossaryLink term="Pairs Trading">{"market-neutral"}</GlossaryLink>
          {" — profit comes from the spread reverting, not from the market going up or down."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" the raw spread is hard to interpret on its own. We need to standardize it into a "}
        <GlossaryLink term="Z-Score" />
        {" so we know when deviations are truly extreme."}
      </Text>
    </Stack>
  );
}
