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
 * Lesson 1.1 — What is Statistical Arbitrage?
 *
 * Teaches the core concept through a real-world analogy and an interactive
 * slider that lets users feel the pull-back strength of mean reversion.
 */
export function Lesson1_1() {
  // 0 = pure random walk, 1 = strong mean reversion
  const [strength, setStrength] = useState(0.7);

  const n = 150;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random for reproducibility
  const noise = (i: number) =>
    Math.sin(i * 127.1 + 311.7) * 0.8 + Math.cos(i * 269.5) * 0.4;

  const spread = useMemo(() => {
    const values: number[] = [0];
    for (let i = 1; i < n; i++) {
      const n_i = noise(i);
      // decay controls pull-back: 1.0 = no pull-back (random walk), 0.0 = instant snap-back
      const decay = 1 - strength * 0.25; // maps [0,1] → [1.0, 0.75]
      const drift = (1 - strength) * 0.04; // random walk gets upward drift
      values.push(values[i - 1] * decay + n_i + drift);
    }
    return values;
  }, [strength]);

  const isReverting = strength > 0.4;
  const label =
    strength < 0.2
      ? 'Random walk — no pull-back, wanders freely'
      : strength < 0.5
        ? 'Weak pull-back — drifts but occasionally returns'
        : strength < 0.8
          ? 'Mean-reverting — consistently pulled back to zero'
          : 'Strong mean reversion — snaps back quickly';

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"Imagine two coffee shops on the same street. Most days, a latte costs about the same at both — say €4. Sometimes Shop A charges €4.50 while Shop B drops to €3.80. The "}
          <em>gap</em>
          {" between their prices wobbles, but it always snaps back to roughly zero."}
        </Text>
        <Text>
          {"Now imagine you could "}
          <strong>sell</strong>
          {" at the expensive shop and "}
          <strong>buy</strong>
          {" at the cheap one whenever that gap gets unusually wide. When it snaps back, you pocket the difference. That's "}
          <GlossaryLink term="Statistical Arbitrage" />
          {" in a nutshell."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>Three things to remember</Title>
        <Text>
          <strong>{"1. Mean reversion is the core bet."}</strong>
          {" The price gap between related assets tends to return to its average. What goes out, comes back. That's "}
          <GlossaryLink term="Mean Reversion" />
          {"."}
        </Text>
        <Text>
          <strong>{"2. It's statistical, not guaranteed."}</strong>
          {" Unlike true arbitrage (risk-free profit), stat arb relies on historical patterns that "}
          <em>might</em>
          {" break. The word \"statistical\" means we're betting on probabilities."}
        </Text>
        <Text>
          <strong>{"3. It's market-neutral."}</strong>
          {" By going long one asset and short the other, you're hedged against the overall market. You profit from the "}
          <em>relationship</em>
          {", not the trend."}
        </Text>
      </Stack>

      {/* Interactive chart */}
      <Stack gap="sm">
        <Title order={4}>Feel the pull-back</Title>
        <Text size="sm" c="dimmed">
          {"Drag the slider to control how strongly the spread is pulled back toward zero. At zero pull-back, it's a random walk — untradeable. Crank it up and watch mean reversion kick in."}
        </Text>

        <Text size="sm" fw={600} c={isReverting ? 'blue.4' : 'red.4'}>
          {label}
        </Text>

        <Slider
          value={strength}
          onChange={setStrength}
          min={0}
          max={1}
          step={0.05}
          marks={[
            { value: 0, label: 'Random walk' },
            { value: 0.5, label: '' },
            { value: 1, label: 'Strong reversion' },
          ]}
          label={(v) => `${Math.round(v * 100)}%`}
          color={isReverting ? 'blue' : 'red'}
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
                color: isReverting ? '#339AF0' : '#FF6B6B',
                width: 2,
              },
            },
            {
              x: [0, n - 1],
              y: [0, 0],
              type: 'scatter',
              mode: 'lines',
              name: 'Mean (zero)',
              line: { color: '#909296', width: 1, dash: 'dash' },
              showlegend: false,
            },
          ]}
          layout={{
            title: isReverting
              ? 'Mean-Reverting: Pulled Back to Zero'
              : 'Random Walk: Wandering Away',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Spread Value' } },
            height: 350,
            showlegend: false,
          }}
        />
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>Up next:</strong>
        {" how do we actually trade this? That's where "}
        <GlossaryLink term="Pairs Trading" />
        {" comes in."}
      </Text>
    </Stack>
  );
}
