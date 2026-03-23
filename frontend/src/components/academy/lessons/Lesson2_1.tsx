'use client';

import { useState } from 'react';
import {
  Box,
  Slider,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 2.1 — Correlation: The Familiar Friend
 *
 * Teaches what correlation measures, shows it interactively,
 * then demonstrates why high correlation isn't enough for pairs trading.
 */
export function Lesson2_1() {
  const [corrLevel, setCorrLevel] = useState(0.9);

  const n = 100;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  // Generate two correlated series with controllable correlation
  // Base series
  const base = timestamps.map(
    (i) => Math.sin(i * 0.1) * 10 + Math.sin(i * 127.1 + 311.7) * 3 + i * 0.5
  );

  // Correlated series: blend of base and independent noise
  const independent = timestamps.map(
    (i) => Math.sin(i * 269.5 + 183.3) * 8 + Math.cos(i * 0.08) * 10 + i * 0.3
  );

  const seriesB = timestamps.map((_, i) => {
    return corrLevel * base[i] + (1 - corrLevel) * independent[i];
  });

  // Calculate actual correlation
  const meanA = base.reduce((s, v) => s + v, 0) / n;
  const meanB = seriesB.reduce((s, v) => s + v, 0) / n;
  const covAB =
    base.reduce((s, v, i) => s + (v - meanA) * (seriesB[i] - meanB), 0) / n;
  const stdA = Math.sqrt(base.reduce((s, v) => s + (v - meanA) ** 2, 0) / n);
  const stdB = Math.sqrt(
    seriesB.reduce((s, v) => s + (v - meanB) ** 2, 0) / n
  );
  const correlation = stdA > 0 && stdB > 0 ? covAB / (stdA * stdB) : 0;

  // The trap: two trending series that are correlated but NOT cointegrated
  const trendA = timestamps.map((i) => 100 + i * 0.8 + Math.sin(i * 0.05) * 5);
  const trendB = timestamps.map(
    (i) => 50 + i * 1.2 + Math.cos(i * 0.07) * 4
  );
  const trendSpread = trendA.map((a, i) => a - trendB[i]);

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"When people think about assets \"moving together,\" they usually think of "}
          <GlossaryLink term="Correlation" />
          {". It's the first tool most people reach for — and it's not wrong, it's just not enough."}
        </Text>
        <Text>
          {"Correlation measures whether two series tend to go up and down "}
          <em>{"at the same time"}</em>
          {". A correlation of +1 means they move in perfect lockstep. Zero means no relationship. The "}
          <GlossaryLink term="p-value" />
          {" tells you if the relationship is statistically significant."}
        </Text>
      </Stack>

      {/* Interactive correlation */}
      <Stack gap="sm">
        <Title order={4}>{"Try it: adjusting correlation"}</Title>
        <Text size="sm" c="dimmed">
          {"Drag the slider to see how two series look at different correlation levels. Watch how the lines track each other more tightly as correlation increases."}
        </Text>

        <Box>
          <Text size="sm" mb="xs">
            {"Correlation blend: "}
            <strong>{corrLevel.toFixed(1)}</strong>
            {" → actual r = "}
            <strong>{correlation.toFixed(3)}</strong>
          </Text>
          <Slider
            value={corrLevel}
            onChange={setCorrLevel}
            min={0}
            max={1}
            step={0.05}
            marks={[
              { value: 0, label: 'r ≈ 0' },
              { value: 0.5, label: 'r ≈ 0.5' },
              { value: 1, label: 'r ≈ 1' },
            ]}
            label={(v) => v.toFixed(2)}
          />
        </Box>

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: base,
              type: 'scatter',
              mode: 'lines',
              name: 'Asset A',
              line: { color: '#339AF0', width: 2 },
            },
            {
              x: timestamps,
              y: seriesB,
              type: 'scatter',
              mode: 'lines',
              name: 'Asset B',
              line: { color: '#51CF66', width: 2 },
            },
          ]}
          layout={{
            title: `Correlation: r = ${correlation.toFixed(3)}`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Price' } },
            height: 350,
            showlegend: true,
            legend: { x: 0, y: 1.12, orientation: 'h' },
          }}
        />
      </Stack>

      {/* The trap */}
      <Stack gap="sm">
        <Title order={4}>{"The correlation trap"}</Title>
        <Text>
          {"Here's the problem. These two assets are highly correlated (they both trend upward). But look at their spread — it keeps "}
          <em>{"growing"}</em>
          {". There's no mean reversion. A pairs trade on these would lose money as the gap widens forever."}
        </Text>

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: trendA,
              type: 'scatter',
              mode: 'lines',
              name: 'Asset A (slow trend)',
              line: { color: '#339AF0', width: 2 },
            },
            {
              x: timestamps,
              y: trendB,
              type: 'scatter',
              mode: 'lines',
              name: 'Asset B (fast trend)',
              line: { color: '#51CF66', width: 2 },
            },
          ]}
          layout={{
            title: 'Highly Correlated — But the Gap Grows',
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
              y: trendSpread,
              type: 'scatter',
              mode: 'lines',
              name: 'Spread (A − B)',
              line: { color: '#FF6B6B', width: 2 },
            },
          ]}
          layout={{
            title: 'Their Spread — Trending, Not Reverting',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Spread' } },
            height: 250,
            showlegend: false,
          }}
        />

        <Text>
          {"Both assets go up, so correlation is high. But Asset B trends "}
          <em>{"faster"}</em>
          {" than Asset A, so the spread keeps widening. Correlation tells you they move in the same "}
          <em>{"direction"}</em>
          {" — it says nothing about whether the "}
          <em>{"gap"}</em>
          {" between them is stable."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" we need a test that specifically measures whether the gap is stable and mean-reverting. That test is called "}
        <GlossaryLink term="Cointegration" />
        {"."}
      </Text>
    </Stack>
  );
}
