'use client';

import { useMemo, useState } from 'react';
import {
  SegmentedControl,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 5.1 — The Research Pipeline
 *
 * Visual flow through the 5 pipeline stages: Scan, Analyze, Research,
 * Backtest, Optimize. Each phase shows a mini interactive example.
 */

const PHASES = [
  {
    label: '1. Scan',
    title: 'Scan: Find Candidate Pairs',
    color: '#339AF0',
    description:
      'The scanner tests every possible pair in your market for cointegration. Out of hundreds of combinations, only a handful pass the statistical tests. The result is a shortlist of pairs worth investigating.',
    modules: 'Pair Scanner — tests all combinations, ranks by p-value and half-life.',
  },
  {
    label: '2. Analyze',
    title: 'Analyze: Study the Spread',
    color: '#CC5DE8',
    description:
      'For each candidate pair, you study the spread in detail. Is it truly stationary? How fast does it revert? Are the z-score signals clean and consistent? This is where you go from "statistically significant" to "actually tradeable."',
    modules: 'Deep Dive — spread chart, z-score overlay, rolling statistics, hedge ratio stability.',
  },
  {
    label: '3. Research',
    title: 'Research: Run the 8 Modules',
    color: '#FF922B',
    description:
      'The 8 research modules give you a complete picture. Correlation & cointegration stability, half-life estimation, spread distribution, regime detection, variance ratio tests, and more. Each module answers a specific question about the pair.',
    modules:
      '8 modules: Cointegration, Correlation, Spread Analysis, Half-Life, Hurst Exponent, Variance Ratio, Regime Detection, Stability.',
  },
  {
    label: '4. Backtest',
    title: 'Backtest: Simulate Trading',
    color: '#51CF66',
    description:
      'Now you run the strategy on historical data. Entry at z = +/-2, exit at z = +/-0.5, with your chosen lookback and hedge ratio. The backtest engine generates a full equity curve, trade log, and performance metrics like Sharpe ratio and max drawdown.',
    modules: 'Backtest Engine — generates equity curve, trade log, Sharpe ratio, drawdown analysis.',
  },
  {
    label: '5. Optimize',
    title: 'Optimize: Validate with Walk-Forward',
    color: '#20C997',
    description:
      'Grid search tries many parameter combinations. Walk-forward validation splits data into train/test folds to check that performance is real, not curve-fitted. The result is a stability verdict: stable, moderate, or fragile.',
    modules:
      'Grid Search + Walk-Forward — parameter sweep, out-of-sample validation, stability verdicts.',
  },
] as const;

export function Lesson5_1() {
  const [phaseIndex, setPhaseIndex] = useState(0);
  const phase = PHASES[phaseIndex];

  const n = 100;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.8 + Math.cos(i * 269.5 + seed * 0.3) * 0.4;

  // Phase 0: Scan — bar chart of p-values for candidate pairs
  const scanData = useMemo(() => {
    const pairs = ['ETH/ETC', 'BTC/LTC', 'SOL/AVAX', 'ADA/DOT', 'XRP/XLM', 'LINK/UNI', 'MATIC/ARB', 'DOGE/SHIB'];
    const pValues = pairs.map((_, i) => Math.abs(Math.sin(i * 3.7 + 1.2) * 0.08 + Math.cos(i * 2.1) * 0.04));
    return { pairs, pValues };
  }, []);

  // Phase 1: Analyze — spread chart
  const spreadData = useMemo(() => {
    const values: number[] = [0];
    for (let i = 1; i < n; i++) {
      values.push(values[i - 1] * 0.92 + noise(i, 311.7));
    }
    return values;
  }, []);

  // Phase 2: Research — z-score series
  const zScoreData = useMemo(() => {
    const mean = spreadData.reduce((s, v) => s + v, 0) / spreadData.length;
    const std = Math.sqrt(spreadData.reduce((s, v) => s + (v - mean) ** 2, 0) / spreadData.length);
    return spreadData.map((v) => (std > 0 ? (v - mean) / std : 0));
  }, [spreadData]);

  // Phase 3: Backtest — equity curve
  const equityCurve = useMemo(() => {
    const equity: number[] = [1000];
    for (let i = 1; i < n; i++) {
      const pnl = Math.sin(i * 0.15 + 2.3) * 3 + 1.5;
      equity.push(equity[i - 1] + pnl);
    }
    return equity;
  }, []);

  // Phase 4: Optimize — heatmap data
  const heatmapData = useMemo(() => {
    const lookbacks = [15, 20, 25, 30, 35, 40];
    const entryThresholds = [1.5, 1.75, 2.0, 2.25, 2.5];
    const z: number[][] = [];
    for (let r = 0; r < entryThresholds.length; r++) {
      const row: number[] = [];
      for (let c = 0; c < lookbacks.length; c++) {
        row.push(
          Math.sin(r * 1.3 + c * 0.9 + 0.7) * 0.4 + 1.2 +
            Math.cos(r * 0.8 + c * 1.7) * 0.3
        );
      }
      z.push(row);
    }
    return { lookbacks, entryThresholds, z };
  }, []);

  const renderChart = () => {
    switch (phaseIndex) {
      case 0:
        return (
          <PlotlyChart
            data={[
              {
                x: scanData.pairs,
                y: scanData.pValues,
                type: 'bar',
                marker: {
                  color: scanData.pValues.map((p) => (p < 0.05 ? '#51CF66' : '#FF6B6B')),
                },
              },
            ]}
            layout={{
              title: 'Scan Results: Cointegration p-values',
              xaxis: { title: { text: 'Pair' } },
              yaxis: { title: { text: 'p-value' } },
              height: 300,
              showlegend: false,
              shapes: [
                {
                  type: 'line',
                  x0: -0.5,
                  x1: scanData.pairs.length - 0.5,
                  y0: 0.05,
                  y1: 0.05,
                  line: { color: '#FF922B', width: 2, dash: 'dash' },
                },
              ],
              annotations: [
                {
                  x: scanData.pairs.length - 1,
                  y: 0.05,
                  text: 'p = 0.05 threshold',
                  showarrow: false,
                  yshift: 12,
                  font: { color: '#FF922B', size: 11 },
                },
              ],
            }}
          />
        );
      case 1:
        return (
          <PlotlyChart
            data={[
              {
                x: timestamps,
                y: spreadData,
                type: 'scatter',
                mode: 'lines',
                name: 'Spread',
                line: { color: '#CC5DE8', width: 2 },
                fill: 'tozeroy',
                fillcolor: 'rgba(204, 93, 232, 0.1)',
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
              title: 'Spread Analysis: Mean-Reverting Behavior',
              xaxis: { title: { text: 'Time' } },
              yaxis: { title: { text: 'Spread Value' } },
              height: 300,
              showlegend: false,
            }}
          />
        );
      case 2:
        return (
          <PlotlyChart
            data={[
              {
                x: timestamps,
                y: zScoreData,
                type: 'scatter',
                mode: 'lines',
                name: 'Z-Score',
                line: { color: '#FF922B', width: 2 },
              },
              {
                x: [0, n - 1],
                y: [2, 2],
                type: 'scatter',
                mode: 'lines',
                name: 'Entry (+2\u03C3)',
                line: { color: '#FF6B6B', width: 1, dash: 'dot' },
              },
              {
                x: [0, n - 1],
                y: [-2, -2],
                type: 'scatter',
                mode: 'lines',
                name: 'Entry (-2\u03C3)',
                line: { color: '#51CF66', width: 1, dash: 'dot' },
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
              title: 'Research: Z-Score with Signal Thresholds',
              xaxis: { title: { text: 'Time' } },
              yaxis: { title: { text: 'Z-Score (\u03C3)' } },
              height: 300,
              showlegend: true,
              legend: { x: 0, y: 1.15, orientation: 'h' },
            }}
          />
        );
      case 3:
        return (
          <PlotlyChart
            data={[
              {
                x: timestamps,
                y: equityCurve,
                type: 'scatter',
                mode: 'lines',
                name: 'Equity Curve',
                line: { color: '#51CF66', width: 2 },
                fill: 'tozeroy',
                fillcolor: 'rgba(81, 207, 102, 0.08)',
              },
            ]}
            layout={{
              title: 'Backtest: Simulated Equity Curve',
              xaxis: { title: { text: 'Time' } },
              yaxis: { title: { text: 'Portfolio Value (\u20AC)' } },
              height: 300,
              showlegend: false,
            }}
          />
        );
      case 4:
        return (
          <PlotlyChart
            data={[
              {
                x: heatmapData.lookbacks,
                y: heatmapData.entryThresholds.map((t) => `${t}\u03C3`),
                z: heatmapData.z,
                type: 'heatmap',
                colorscale: [
                  [0, '#FF6B6B'],
                  [0.5, '#FF922B'],
                  [1, '#51CF66'],
                ],
                colorbar: { title: { text: 'Sharpe', side: 'right' } },
              },
            ]}
            layout={{
              title: 'Optimization: Sharpe Ratio Heatmap',
              xaxis: { title: { text: 'Lookback Period' } },
              yaxis: { title: { text: 'Entry Threshold' } },
              height: 300,
            }}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"Statistical arbitrage isn't about gut feelings or single indicators. It's a "}
          <strong>{"systematic pipeline"}</strong>
          {" — each stage filters, validates, and builds on the last. If a pair fails at any stage, you move on. No exceptions."}
        </Text>
        <Text>
          {"Step through the five phases below to see the full workflow you'll use in the "}
          <GlossaryLink term="Pairs Trading">{"Research"}</GlossaryLink>
          {" section of this platform."}
        </Text>
      </Stack>

      <SegmentedControl
        value={String(phaseIndex)}
        onChange={(v) => setPhaseIndex(Number(v))}
        data={PHASES.map((p, i) => ({
          label: p.label,
          value: String(i),
        }))}
        fullWidth
      />

      <Stack gap="sm">
        <Title order={4} c={phase.color}>
          {phase.title}
        </Title>
        <Text>{phase.description}</Text>
        <Text size="sm" c="dimmed" fs="italic">
          {phase.modules}
        </Text>

        {renderChart()}
      </Stack>

      {/* Pipeline overview */}
      <Stack gap="sm">
        <Title order={4}>{"The 8 research modules"}</Title>
        <Text>
          {"Between scanning and backtesting, you have access to 8 research modules that each answer a specific question about your pair:"}
        </Text>
        <Text>
          <strong>{"1. Cointegration"}</strong>
          {" — is the pair still cointegrated? ("}
          <GlossaryLink term="Engle-Granger Test" />
          {")"}
        </Text>
        <Text>
          <strong>{"2. Correlation"}</strong>
          {" — does "}
          <GlossaryLink term="Correlation" />
          {" remain strong and consistent?"}
        </Text>
        <Text>
          <strong>{"3. Spread Analysis"}</strong>
          {" — is the "}
          <GlossaryLink term="Spread" />
          {" distribution normal and symmetric?"}
        </Text>
        <Text>
          <strong>{"4. Half-Life"}</strong>
          {" — how fast does the spread revert? ("}
          <GlossaryLink term="Half-Life" />
          {")"}
        </Text>
        <Text>
          <strong>{"5. Hurst Exponent"}</strong>
          {" — is this truly mean-reverting, or a random walk?"}
        </Text>
        <Text>
          <strong>{"6. Variance Ratio"}</strong>
          {" — does variance grow linearly (random) or sub-linearly (mean-reverting)?"}
        </Text>
        <Text>
          <strong>{"7. Regime Detection"}</strong>
          {" — has the relationship changed over time?"}
        </Text>
        <Text>
          <strong>{"8. Stability"}</strong>
          {" — is the "}
          <GlossaryLink term="Hedge Ratio" />
          {" stable, or does it drift?"}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" once you have a validated pair, how do you find the best parameters? That's where optimization and walk-forward testing come in."}
      </Text>
    </Stack>
  );
}
