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
 * Lesson 2.2 — Cointegration: The Real Test
 *
 * Explains what cointegration actually means and why it's different from
 * correlation. Interactive: compare correlated-not-cointegrated vs
 * cointegrated pairs.
 */
export function Lesson2_2() {
  const [example, setExample] = useState<string>('cointegrated');

  const n = 150;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  // Cointegrated pair: shared random walk + stationary spread
  const randomWalk: number[] = [100];
  for (let i = 1; i < n; i++) {
    randomWalk.push(
      randomWalk[i - 1] + Math.sin(i * 127.1 + 311.7) * 1.5
    );
  }

  const cointA = randomWalk.map(
    (v, i) => v + Math.sin(i * 0.2) * 3
  );
  const cointB = randomWalk.map(
    (v, i) => v * 0.8 + 20 + Math.sin(i * 0.25 + 1) * 2.5
  );
  const cointSpread = cointA.map((a, i) => a - 1.25 * cointB[i]);

  // Correlated but NOT cointegrated: two independent random walks with similar trend
  const walkA: number[] = [100];
  const walkB: number[] = [80];
  for (let i = 1; i < n; i++) {
    const commonShock = Math.sin(i * 73.3) * 0.8;
    walkA.push(walkA[i - 1] + commonShock + Math.sin(i * 127.1) * 0.6 + 0.1);
    walkB.push(walkB[i - 1] + commonShock + Math.cos(i * 269.5) * 0.6 + 0.15);
  }
  const notCointSpread = walkA.map((a, i) => a - walkB[i]);

  const pricesA = example === 'cointegrated' ? cointA : walkA;
  const pricesB = example === 'cointegrated' ? cointB : walkB;
  const spread = example === 'cointegrated' ? cointSpread : notCointSpread;

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          <GlossaryLink term="Cointegration" />
          {" answers a different question than correlation. Instead of asking \"do these assets move in the same direction?\" it asks: "}
          <strong>{"\"does the gap between them stay bounded?\""}</strong>
        </Text>
        <Text>
          {"Two series are cointegrated when some linear combination of them produces a "}
          <GlossaryLink term="Stationarity">{"stationary"}</GlossaryLink>
          {" series — one that oscillates around a constant mean. That stationary series is the "}
          <GlossaryLink term="Spread" />
          {", and it's what we trade."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"The key intuition"}</Title>
        <Text>
          {"Think of it like two dogs on a leash. Each dog wanders randomly (non-stationary), but the leash constrains the distance between them. The "}
          <em>{"dogs"}</em>
          {" are the asset prices. The "}
          <em>{"leash length"}</em>
          {" is the spread. If the leash exists (cointegration), the spread is bounded and mean-reverting. If there's no leash, the dogs can wander apart forever."}
        </Text>
      </Stack>

      {/* Interactive comparison */}
      <Stack gap="sm">
        <Title order={4}>{"See the difference"}</Title>
        <Text size="sm" c="dimmed">
          {"Toggle between a cointegrated pair (spread is bounded) and a merely correlated pair (spread drifts). The prices might look similar, but the spread tells the truth."}
        </Text>

        <SegmentedControl
          value={example}
          onChange={setExample}
          data={[
            { label: 'Cointegrated', value: 'cointegrated' },
            { label: 'Only Correlated', value: 'correlated' },
          ]}
          fullWidth
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
            title: example === 'cointegrated'
              ? 'Cointegrated: Prices Wander, But Together'
              : 'Only Correlated: Prices Trend Similarly, But Drift Apart',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Price' } },
            height: 300,
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
                color: example === 'cointegrated' ? '#339AF0' : '#FF6B6B',
                width: 2,
              },
            },
            ...(example === 'cointegrated'
              ? [
                  {
                    x: [0, n - 1],
                    y: [0, 0] as number[],
                    type: 'scatter' as const,
                    mode: 'lines' as const,
                    line: { color: '#909296', width: 1, dash: 'dash' as const },
                    showlegend: false,
                  },
                ]
              : []),
          ]}
          layout={{
            title: example === 'cointegrated'
              ? 'Spread: Bounded and Mean-Reverting ✓'
              : 'Spread: Drifting — NOT Mean-Reverting ✗',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Spread Value' } },
            height: 250,
            showlegend: false,
          }}
        />

        <Text size="sm">
          {example === 'cointegrated'
            ? "The spread oscillates around zero — it's stationary. Every time it deviates, it reverts. This is tradeable."
            : "The spread trends upward with no pull-back. Despite the assets being correlated, the gap keeps growing. This is NOT tradeable."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"Correlation vs. cointegration — the cheat sheet"}</Title>
        <Text>
          <strong>{"Correlation"}</strong>
          {" measures co-movement in "}
          <em>{"direction"}</em>
          {". High correlation means both tend to go up or down together. But they can drift apart over time."}
        </Text>
        <Text>
          <strong>{"Cointegration"}</strong>
          {" measures stability of the "}
          <em>{"gap"}</em>
          {". It tells you whether the spread between two assets is bounded and mean-reverting — which is exactly what pairs trading needs."}
        </Text>
        <Text>
          {"A pair can be highly correlated but not cointegrated (our trap example). A pair can even be uncorrelated in the short term but cointegrated in the long run. "}
          <strong>{"For pairs trading, cointegration is what matters."}</strong>
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" how do we actually test for cointegration? We'll walk through the "}
        <GlossaryLink term="Engle-Granger Test" />
        {" step by step."}
      </Text>
    </Stack>
  );
}
