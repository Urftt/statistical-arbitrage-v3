'use client';

import { useMemo, useState } from 'react';
import {
  Button,
  SegmentedControl,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import Link from 'next/link';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 5.3 — Graduation: Ready for Research
 *
 * Summary of all 5 chapters. Interactive concept navigator and a complete
 * pipeline diagram. Call-to-action to start real research.
 */

const CONCEPTS = [
  {
    label: 'Ch 1: The Big Idea',
    title: 'Statistical Arbitrage',
    color: '#339AF0',
    summary:
      'Profit from temporary mispricings between related assets. Mean reversion is the core bet — when the gap widens, trade it back to normal.',
    term: 'Statistical Arbitrage' as const,
  },
  {
    label: 'Ch 2: Finding Pairs',
    title: 'Cointegration > Correlation',
    color: '#CC5DE8',
    summary:
      'Correlation measures co-movement direction. Cointegration measures whether the gap stays bounded. Only cointegration gives you a tradeable spread.',
    term: 'Cointegration' as const,
  },
  {
    label: 'Ch 3: Signals',
    title: 'Z-Score Trading Signals',
    color: '#FF922B',
    summary:
      'Convert the spread to z-scores. Enter at +/-2\u03C3, exit near zero. The z-score tells you how extreme the current deviation is — your buy/sell trigger.',
    term: 'Z-Score' as const,
  },
  {
    label: 'Ch 4: Backtesting',
    title: 'Validate Before You Trade',
    color: '#51CF66',
    summary:
      'Run the strategy on historical data to measure performance. Track Sharpe ratio, max drawdown, and trade count. If it doesn\'t work in backtesting, it won\'t work live.',
    term: 'Half-Life' as const,
  },
  {
    label: 'Ch 5: Pipeline',
    title: 'The Systematic Workflow',
    color: '#20C997',
    summary:
      'Scan \u2192 Analyze \u2192 Research \u2192 Backtest \u2192 Optimize. Walk-forward validation ensures your parameters aren\'t overfit. Stable verdicts mean real edge.',
    term: 'Pairs Trading' as const,
  },
] as const;

const PIPELINE_STEPS = [
  { label: 'Scan', color: '#339AF0', x: 0 },
  { label: 'Analyze', color: '#CC5DE8', x: 1 },
  { label: 'Research', color: '#FF922B', x: 2 },
  { label: 'Backtest', color: '#51CF66', x: 3 },
  { label: 'Optimize', color: '#20C997', x: 4 },
] as const;

export function Lesson5_3() {
  const [conceptIndex, setConceptIndex] = useState(0);
  const concept = CONCEPTS[conceptIndex];

  // Pipeline diagram: a Sankey-like flow using scatter + annotations
  const pipelineChartData = useMemo(() => {
    // Draw connected nodes as a flow
    const xValues = PIPELINE_STEPS.map((s) => s.x);
    const yValues = PIPELINE_STEPS.map(() => 1);
    const colors = PIPELINE_STEPS.map((s) => s.color);
    const labels = PIPELINE_STEPS.map((s) => s.label);

    return { xValues, yValues, colors, labels };
  }, []);

  // Simulated "graduation" spread + equity to show the full picture
  const n = 120;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.8 + Math.cos(i * 269.5 + seed * 0.3) * 0.4;

  const { zScores, equity } = useMemo(() => {
    // Mean-reverting spread
    const s: number[] = [0];
    for (let i = 1; i < n; i++) {
      s.push(s[i - 1] * 0.88 + noise(i, 311.7) * 1.2);
    }

    // Z-scores from spread
    const mean = s.reduce((sum, v) => sum + v, 0) / s.length;
    const std = Math.sqrt(s.reduce((sum, v) => sum + (v - mean) ** 2, 0) / s.length);
    const z = s.map((v) => (std > 0 ? (v - mean) / std : 0));

    // Equity curve from z-score signals
    const eq: number[] = [1000];
    let position = 0; // 1 = long spread, -1 = short, 0 = flat
    for (let i = 1; i < n; i++) {
      if (position === 0 && z[i] > 2) position = -1;
      else if (position === 0 && z[i] < -2) position = 1;
      else if (position !== 0 && Math.abs(z[i]) < 0.5) position = 0;

      const pnl = position * (s[i] - s[i - 1]) * 3;
      eq.push(eq[i - 1] + pnl);
    }

    return { zScores: z, equity: eq };
  }, []);

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Title order={3} c="teal.4">
          {"Congratulations \u2014 you've completed the Academy"}
        </Title>
        <Text>
          {"You now understand the complete statistical arbitrage workflow, from the underlying theory to practical validation. Here's what you've learned across 5 chapters."}
        </Text>
      </Stack>

      {/* Concept navigator */}
      <Stack gap="sm">
        <Title order={4}>{"What you now know"}</Title>

        <SegmentedControl
          value={String(conceptIndex)}
          onChange={(v) => setConceptIndex(Number(v))}
          data={CONCEPTS.map((c, i) => ({
            label: c.label,
            value: String(i),
          }))}
          fullWidth
        />

        <Stack
          gap="xs"
          p="md"
          style={{
            borderRadius: 8,
            border: `1px solid ${concept.color}40`,
            backgroundColor: `${concept.color}08`,
          }}
        >
          <Title order={5} c={concept.color}>
            {concept.title}
          </Title>
          <Text>{concept.summary}</Text>
          <Text size="sm" c="dimmed">
            {"Key concept: "}
            <GlossaryLink term={concept.term} />
          </Text>
        </Stack>
      </Stack>

      {/* Complete pipeline diagram */}
      <Stack gap="sm">
        <Title order={4}>{"The complete pipeline"}</Title>

        <PlotlyChart
          data={[
            {
              x: pipelineChartData.xValues,
              y: pipelineChartData.yValues,
              type: 'scatter',
              mode: 'text+markers',
              text: pipelineChartData.labels,
              textposition: 'top center',
              textfont: { size: 14, color: '#C1C2C5' },
              marker: {
                size: 40,
                color: pipelineChartData.colors,
                line: { width: 2, color: '#1A1B1E' },
              },
              showlegend: false,
            },
            // Connecting arrows as lines
            {
              x: [0, 1, 1, 2, 2, 3, 3, 4],
              y: [1, 1, 1, 1, 1, 1, 1, 1],
              type: 'scatter',
              mode: 'lines',
              line: { color: '#4a4b50', width: 3 },
              showlegend: false,
              hoverinfo: 'skip',
            },
          ]}
          layout={{
            title: 'Your Research Workflow',
            height: 180,
            xaxis: {
              showgrid: false,
              zeroline: false,
              showticklabels: false,
              range: [-0.5, 4.5],
            },
            yaxis: {
              showgrid: false,
              zeroline: false,
              showticklabels: false,
              range: [0.5, 1.6],
            },
            annotations: [
              { x: 0.5, y: 0.75, text: '\u2192', showarrow: false, font: { size: 20, color: '#4a4b50' } },
              { x: 1.5, y: 0.75, text: '\u2192', showarrow: false, font: { size: 20, color: '#4a4b50' } },
              { x: 2.5, y: 0.75, text: '\u2192', showarrow: false, font: { size: 20, color: '#4a4b50' } },
              { x: 3.5, y: 0.75, text: '\u2192', showarrow: false, font: { size: 20, color: '#4a4b50' } },
            ],
            margin: { t: 40, b: 20, l: 20, r: 20 },
          }}
        />
      </Stack>

      {/* Summary chart: spread + z-score + equity */}
      <Stack gap="sm">
        <Title order={4}>{"The full picture: from spread to profit"}</Title>
        <Text size="sm" c="dimmed">
          {"A cointegrated spread, converted to z-scores for signals, generating a rising equity curve. This is what the entire pipeline produces."}
        </Text>

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: zScores,
              type: 'scatter',
              mode: 'lines',
              name: 'Z-Score',
              line: { color: '#FF922B', width: 1.5 },
              yaxis: 'y',
            },
            {
              x: [0, n - 1],
              y: [2, 2],
              type: 'scatter',
              mode: 'lines',
              name: 'Short entry',
              line: { color: '#FF6B6B', width: 1, dash: 'dot' },
              yaxis: 'y',
            },
            {
              x: [0, n - 1],
              y: [-2, -2],
              type: 'scatter',
              mode: 'lines',
              name: 'Long entry',
              line: { color: '#51CF66', width: 1, dash: 'dot' },
              yaxis: 'y',
            },
          ]}
          layout={{
            title: 'Z-Score Signals',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Z-Score (\u03C3)' } },
            height: 250,
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: equity,
              type: 'scatter',
              mode: 'lines',
              name: 'Equity',
              line: { color: '#20C997', width: 2 },
              fill: 'tozeroy',
              fillcolor: 'rgba(32, 201, 151, 0.08)',
            },
          ]}
          layout={{
            title: 'Resulting Equity Curve',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Portfolio Value (\u20AC)' } },
            height: 250,
            showlegend: false,
          }}
        />
      </Stack>

      {/* What you've earned */}
      <Stack gap="sm">
        <Title order={4}>{"Your toolkit"}</Title>
        <Text>
          <strong style={{ color: '#339AF0' }}>{"Mean reversion"}</strong>
          {" \u2014 you understand the core mechanism behind every trade."}
        </Text>
        <Text>
          <strong style={{ color: '#CC5DE8' }}>{"Cointegration testing"}</strong>
          {" \u2014 you know how to identify pairs with a genuine statistical relationship."}
        </Text>
        <Text>
          <strong style={{ color: '#FF922B' }}>{"Z-score signals"}</strong>
          {" \u2014 you can read entry and exit signals from standardized spreads."}
        </Text>
        <Text>
          <strong style={{ color: '#51CF66' }}>{"Backtesting"}</strong>
          {" \u2014 you can validate strategies on historical data before risking capital."}
        </Text>
        <Text>
          <strong style={{ color: '#20C997' }}>{"Walk-forward validation"}</strong>
          {" \u2014 you know the difference between a flattering backtest and real evidence."}
        </Text>
      </Stack>

      {/* Call to action */}
      <Stack
        gap="md"
        p="lg"
        style={{
          borderRadius: 8,
          border: '1px solid rgba(32, 201, 151, 0.3)',
          backgroundColor: 'rgba(32, 201, 151, 0.05)',
        }}
      >
        <Title order={4} c="teal.4">
          {"Ready to find your first pair"}
        </Title>
        <Text>
          {"The Scanner will test every pair in the market for cointegration. Pick one that passes, run the 8 research modules, backtest it, and validate with walk-forward. You have the tools. The data is waiting."}
        </Text>
        <Button
          component={Link}
          href="/scanner"
          size="lg"
          color="teal"
          variant="filled"
          style={{ alignSelf: 'flex-start' }}
        >
          {"Go to Pair Scanner"}
        </Button>
      </Stack>

      <Text c="dimmed" size="sm" ta="center">
        {"You can revisit any lesson at any time from the Academy sidebar. Good luck with your research."}
      </Text>
    </Stack>
  );
}
