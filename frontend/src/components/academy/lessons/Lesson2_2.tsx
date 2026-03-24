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
 * Lesson 2.2 — Cointegration: The Real Test
 *
 * Interactive slider controls the "leash tightness" — how strongly the spread
 * is pulled back. Users can feel the spectrum from cointegrated to merely correlated.
 */
export function Lesson2_2() {
  // 0 = no leash (drifting, only correlated), 1 = tight leash (strongly cointegrated)
  const [tightness, setTightness] = useState(0.8);

  const n = 150;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 1.5;

  const { pricesA, pricesB, spread } = useMemo(() => {
    // Common random walk (shared trend)
    const walk: number[] = [100];
    for (let i = 1; i < n; i++) {
      walk.push(walk[i - 1] + noise(i, 311.7));
    }

    // Asset A follows the walk with some wobble
    const a = walk.map((v, i) => v + Math.sin(i * 0.2) * 3);

    // Asset B: tightness controls how much it's pulled toward A's level
    // At tightness=1: B = 0.8*A + 20 + small noise (tight cointegration)
    // At tightness=0: B follows its own random walk with similar trend (just correlated)
    const b: number[] = [0.8 * a[0] + 20];
    for (let i = 1; i < n; i++) {
      const targetB = 0.8 * a[i] + 20; // where B "should" be if cointegrated
      const independentStep = b[i - 1] + noise(i, 73.3) * 0.6 + 0.05; // independent drift
      // Blend between cointegrated target and independent random walk
      const pullBack = tightness * 0.15; // how fast it snaps back
      const blended = b[i - 1] + pullBack * (targetB - b[i - 1]) + noise(i, 73.3) * (1.2 - tightness * 0.5);
      b.push(tightness > 0.1 ? blended : independentStep);
    }

    const s = a.map((aVal, i) => aVal - 1.25 * b[i]);
    return { pricesA: a, pricesB: b, spread: s };
  }, [tightness]);

  const isCointegrated = tightness > 0.4;
  const label =
    tightness < 0.15
      ? 'No leash — assets drift apart freely (only correlated)'
      : tightness < 0.4
        ? 'Loose leash — some pull-back, but spread still drifts'
        : tightness < 0.7
          ? 'Moderate leash — spread is mostly bounded'
          : 'Tight leash — spread snaps back reliably (cointegrated)';

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

      {/* Interactive slider */}
      <Stack gap="sm">
        <Title order={4}>{"Tighten the leash"}</Title>
        <Text size="sm" c="dimmed">
          {"Drag the slider to control how tightly the two assets are bound together. Watch the spread chart below — does it stay flat, or drift away?"}
        </Text>

        <Text size="sm" fw={600} c={isCointegrated ? 'blue.4' : 'red.4'}>
          {label}
        </Text>

        <Slider
          value={tightness}
          onChange={setTightness}
          min={0}
          max={1}
          step={0.05}
          marks={[
            { value: 0, label: 'No leash' },
            { value: 0.5, label: '' },
            { value: 1, label: 'Tight leash' },
          ]}
          label={(v) => `${Math.round(v * 100)}%`}
          color={isCointegrated ? 'blue' : 'red'}
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
            title: isCointegrated
              ? 'Prices: Wandering Together (Leash Holds)'
              : 'Prices: Drifting Apart (No Leash)',
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
                color: isCointegrated ? '#339AF0' : '#FF6B6B',
                width: 2,
              },
            },
            {
              x: [0, n - 1],
              y: [0, 0],
              type: 'scatter',
              mode: 'lines',
              line: { color: '#909296', width: 1, dash: 'dash' },
              showlegend: false,
            },
          ]}
          layout={{
            title: isCointegrated
              ? 'Spread: Bounded and Mean-Reverting'
              : 'Spread: Drifting — NOT Mean-Reverting',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Spread Value' } },
            height: 250,
            showlegend: false,
          }}
        />

        <Text size="sm">
          {isCointegrated
            ? "The spread oscillates around a level — it's stationary. Every time it deviates, the leash pulls it back. This is tradeable."
            : "The spread trends with no pull-back. Despite the assets moving in similar directions, the gap keeps growing. This is NOT tradeable."}
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
          {"A pair can be highly correlated but not cointegrated (slide the leash to zero to see it). A pair can even be uncorrelated in the short term but cointegrated in the long run. "}
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
