'use client';

import { useState } from 'react';
import {
  Box,
  SegmentedControl,
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
 * chart comparing mean reversion vs random walk.
 */
export function Lesson1_1() {
  const [scenario, setScenario] = useState<string>('revert');

  // Generate spread simulations
  const n = 150;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  const revertingSpread: number[] = [0];
  const randomSpread: number[] = [0];

  // Deterministic pseudo-random for reproducibility
  const noise = (i: number) => Math.sin(i * 127.1 + 311.7) * 0.8 + Math.cos(i * 269.5) * 0.4;

  for (let i = 1; i < n; i++) {
    const n_i = noise(i);
    // Mean-reverting: strong pull-back toward 0
    revertingSpread.push(revertingSpread[i - 1] * 0.85 + n_i);
    // Random walk: accumulates with upward drift — clearly drifts away from zero
    randomSpread.push(randomSpread[i - 1] + n_i * 0.3 + 0.06);
  }

  const spread = scenario === 'revert' ? revertingSpread : randomSpread;

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
        <Title order={4}>See it in action</Title>
        <Text size="sm" c="dimmed">
          {"Toggle between the two scenarios. A "}
          <strong>mean-reverting</strong>
          {" spread keeps returning to zero — that's tradeable. A "}
          <strong>random walk</strong>
          {" just wanders off — not tradeable."}
        </Text>

        <SegmentedControl
          value={scenario}
          onChange={setScenario}
          data={[
            { label: 'Mean-Reverting', value: 'revert' },
            { label: 'Random Walk', value: 'random' },
          ]}
          size="sm"
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: spread,
              type: 'scatter',
              mode: 'lines',
              name: scenario === 'revert' ? 'Mean-reverting spread' : 'Random walk',
              line: {
                color: scenario === 'revert' ? '#339AF0' : '#FF6B6B',
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
            title: scenario === 'revert'
              ? 'Mean-Reverting: Always Pulled Back to Zero'
              : 'Random Walk: Wanders Freely, No Pull-Back',
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
