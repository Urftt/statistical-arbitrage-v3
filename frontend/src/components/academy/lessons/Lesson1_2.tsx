'use client';

import { useState } from 'react';
import {
  Box,
  Group,
  Slider,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 1.2 — Pairs Trading Explained
 *
 * Deeper dive into pairs trading mechanics: the full trade lifecycle,
 * why both sides matter, and an interactive signal chart.
 */
export function Lesson1_2() {
  const [entryThreshold, setEntryThreshold] = useState(2.0);

  // Simulate a mean-reverting spread with clear signals
  const n = 200;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  const spread: number[] = [0];
  for (let i = 1; i < n; i++) {
    // More volatile noise to ensure clear ±2σ crossings
    const noise = Math.sin(i * 127.1 + 311.7) * 1.2 + Math.cos(i * 73.3) * 0.8
      + Math.sin(i * 0.15) * 2;
    spread.push(spread[i - 1] * 0.88 + noise);
  }

  // Calculate rolling stats for z-score
  const window = 30;
  const zscore: (number | null)[] = [];
  for (let i = 0; i < n; i++) {
    if (i < window) {
      zscore.push(null);
      continue;
    }
    const slice = spread.slice(i - window, i);
    const mean = slice.reduce((a, b) => a + b, 0) / window;
    const std = Math.sqrt(slice.reduce((a, b) => a + (b - mean) ** 2, 0) / window);
    zscore.push(std > 0 ? (spread[i] - mean) / std : 0);
  }

  // Find signal points for annotations
  const entryPoints: { x: number; y: number; type: 'long' | 'short' }[] = [];
  for (let i = window; i < n; i++) {
    const z = zscore[i] as number;
    const zPrev = zscore[i - 1] as number;
    if (z <= -entryThreshold && zPrev > -entryThreshold) {
      entryPoints.push({ x: i, y: z, type: 'long' });
    } else if (z >= entryThreshold && zPrev < entryThreshold) {
      entryPoints.push({ x: i, y: z, type: 'short' });
    }
  }

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          <GlossaryLink term="Pairs Trading" />{" is the most common form of stat arb. You find two assets that move together, wait for them to diverge, then bet on them converging again. The key insight: you always hold "}
          <strong>{"two opposing positions"}</strong>
          {" simultaneously."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>The anatomy of a pairs trade</Title>

        <Text>
          <strong>{"Step 1: Find a pair."}</strong>
          {" You need two assets with a stable long-run relationship. Not just \"they both go up\" \u2014 that\u2019s "}
          <GlossaryLink term="Correlation" />
          {" and it\u2019s not enough. You need the "}
          <em>{"gap"}</em>
          {" between them to be predictable. In crypto, ETH and ETC are a classic example \u2014 both Ethereum-based, influenced by similar forces."}
        </Text>

        <Text>
          <strong>{"Step 2: Measure the gap."}</strong>
          {" This gap is called the "}
          <GlossaryLink term="Spread" />
          {". We standardize it into a "}
          <GlossaryLink term="Z-Score" />
          {" \u2014 the number of standard deviations from its average. A z-score of +2 means the gap is unusually wide. A z-score of -2 means it\u2019s unusually narrow."}
        </Text>

        <Text>
          <strong>{"Step 3: Trade the extremes."}</strong>
          {" When the z-score hits +2\u03C3 (gap too wide), you "}
          <em>{"short"}</em>
          {" the outperformer and "}
          <em>{"long"}</em>
          {" the underperformer. You\u2019re betting the gap will narrow. When it does, you close both sides and pocket the difference."}
        </Text>

        <Text>
          <strong>{"Step 4: Stay market-neutral."}</strong>
          {" Because you\u2019re long one asset and short the other, a market crash affects both sides roughly equally. Your profit comes from the "}
          <em>{"relationship"}</em>
          {" normalizing, not from the market going up or down. That\u2019s the beauty of it."}
        </Text>
      </Stack>

      {/* Why both sides? */}
      <Stack gap="sm">
        <Title order={4}>Why you need both sides</Title>
        <Text>
          Say ETH is at €3,000 and ETC is at €25. Their spread is unusually wide —
          ETH has surged ahead. You could just buy ETC and hope it catches up. But
          what if the whole market crashes? ETC goes to €15 and you&apos;ve lost 40%.
        </Text>
        <Text>
          {"With pairs trading, you "}
          <em>{"also"}</em>
          {" short ETH. If the market crashes, your short on ETH makes money while your long on ETC loses \u2014 roughly a wash. But when the spread normalizes (ETH drops relative to ETC, or ETC rises relative to ETH, or both), "}
          <em>{"that"}</em>
          {" is where your profit comes from."}
        </Text>
        <Text c="dimmed" size="sm">
          This is what &quot;market-neutral&quot; means in practice. You remove the market
          direction risk and isolate the relationship risk.
        </Text>
      </Stack>

      {/* Interactive z-score chart */}
      <Stack gap="sm">
        <Title order={4}>Try it: spot the trade signals</Title>
        <Text size="sm" c="dimmed">
          This is a simulated z-score of a spread. Adjust the entry threshold to see
          how it affects when signals fire. More extreme thresholds = fewer but
          higher-conviction trades.
        </Text>

        <Box>
          <Text size="sm" mb="xs">
            {"Entry threshold: "}<strong>{"±"}{entryThreshold.toFixed(1)}{"σ"}</strong>
          </Text>
          <Slider
            value={entryThreshold}
            onChange={setEntryThreshold}
            min={1.0}
            max={3.0}
            step={0.1}
            marks={[
              { value: 1.0, label: '1σ' },
              { value: 1.5, label: '1.5σ' },
              { value: 2.0, label: '2σ' },
              { value: 2.5, label: '2.5σ' },
              { value: 3.0, label: '3σ' },
            ]}
            label={(v) => `±${v.toFixed(1)}σ`}
          />
        </Box>

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: zscore,
              type: 'scatter',
              mode: 'lines',
              name: 'Z-Score',
              line: { color: '#339AF0', width: 1.5 },
              connectgaps: false,
            },
            // Upper threshold
            {
              x: [0, n - 1],
              y: [entryThreshold, entryThreshold],
              type: 'scatter',
              mode: 'lines',
              name: `+${entryThreshold.toFixed(1)}σ (Short entry)`,
              line: { color: '#FF6B6B', width: 1, dash: 'dash' },
            },
            // Lower threshold
            {
              x: [0, n - 1],
              y: [-entryThreshold, -entryThreshold],
              type: 'scatter',
              mode: 'lines',
              name: `−${entryThreshold.toFixed(1)}σ (Long entry)`,
              line: { color: '#51CF66', width: 1, dash: 'dash' },
            },
            // Zero line
            {
              x: [0, n - 1],
              y: [0, 0],
              type: 'scatter',
              mode: 'lines',
              line: { color: '#909296', width: 0.5, dash: 'dot' },
              showlegend: false,
            },
            // Entry markers
            ...(entryPoints.length > 0
              ? [
                  {
                    x: entryPoints.map((p) => p.x),
                    y: entryPoints.map((p) => p.y),
                    type: 'scatter' as const,
                    mode: 'markers' as const,
                    name: 'Trade signals',
                    marker: {
                      size: 8,
                      color: entryPoints.map((p) =>
                        p.type === 'long' ? '#51CF66' : '#FF6B6B'
                      ),
                      symbol: entryPoints.map((p) =>
                        p.type === 'long' ? 'triangle-up' : 'triangle-down'
                      ),
                    },
                  },
                ]
              : []),
          ]}
          layout={{
            title: `Z-Score with ±${entryThreshold.toFixed(1)}σ Entry — ${entryPoints.length} signals`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Z-Score (σ)' } },
            height: 400,
            showlegend: true,
            legend: { x: 0, y: -0.2, orientation: 'h' },
          }}
        />

        <Text size="sm" c="dimmed">
          <strong>{entryPoints.length}{" signals"}</strong>{" at \u00B1"}{entryThreshold.toFixed(1)}{"\u03C3. "}
          {entryThreshold < 1.5
            ? 'Very sensitive — lots of signals, but many may be false alarms.'
            : entryThreshold > 2.5
            ? 'Very conservative — few signals, but each one is high-conviction.'
            : 'A balanced threshold — reasonable trade frequency with decent conviction.'}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" we\u2019ve been using simulated data. Let\u2019s see what real crypto prices actually look like."}
      </Text>
    </Stack>
  );
}
