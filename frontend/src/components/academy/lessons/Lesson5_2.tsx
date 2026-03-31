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
import { RealDataSection, TabSignals } from '@/components/academy/real-data';

/**
 * Lesson 5.2 — Optimization & Walk-Forward
 *
 * Interactive train/test split slider. Shows how grid search parameters
 * perform differently on in-sample vs out-of-sample data, and why
 * walk-forward validation matters.
 */
export function Lesson5_2() {
  // Train fraction: 0.5 to 0.9
  const [trainFraction, setTrainFraction] = useState(0.7);

  const n = 200;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.8 + Math.cos(i * 269.5 + seed * 0.3) * 0.4;

  const splitIndex = Math.round(trainFraction * n);

  // Simulate equity curve: "optimized" parameters work great on train, less so on test
  const { trainEquity, testEquity, trainSharpe, testSharpe } = useMemo(() => {
    const tEquity: number[] = [1000];
    // Train performance: consistent gains from optimized params
    for (let i = 1; i < splitIndex; i++) {
      const pnl = Math.sin(i * 0.12 + 1.5) * 2.5 + 2.0 + noise(i, 42.0) * 0.5;
      tEquity.push(tEquity[i - 1] + pnl);
    }

    const teEquity: number[] = [tEquity[tEquity.length - 1]];
    // Test performance depends on how much data was used for training:
    // More training data = slightly better out-of-sample, but diminishing returns.
    // Very high train fraction = overfit risk, test gets worse.
    const overfitPenalty = trainFraction > 0.8 ? (trainFraction - 0.8) * 15 : 0;
    const testDrift = 0.8 - overfitPenalty;
    const testLen = n - splitIndex;
    for (let i = 1; i < testLen; i++) {
      const pnl =
        Math.sin((i + splitIndex) * 0.12 + 1.5) * 2.5 * 0.6 +
        testDrift +
        noise(i + splitIndex, 42.0) * 1.2;
      teEquity.push(teEquity[i - 1] + pnl);
    }

    // Approximate Sharpe calculation
    const trainReturns = tEquity.slice(1).map((v, i) => v - tEquity[i]);
    const testReturns = teEquity.slice(1).map((v, i) => v - teEquity[i]);

    const calcSharpe = (returns: number[]): number => {
      if (returns.length < 2) return 0;
      const mean = returns.reduce((s, v) => s + v, 0) / returns.length;
      const std = Math.sqrt(
        returns.reduce((s, v) => s + (v - mean) ** 2, 0) / returns.length
      );
      return std > 0 ? (mean / std) * Math.sqrt(252) : 0;
    };

    return {
      trainEquity: tEquity,
      testEquity: teEquity,
      trainSharpe: calcSharpe(trainReturns),
      testSharpe: calcSharpe(testReturns),
    };
  }, [trainFraction, splitIndex]);

  // Walk-forward folds visualization
  const numFolds = 4;
  const foldData = useMemo(() => {
    const folds: Array<{
      fold: number;
      trainStart: number;
      trainEnd: number;
      testStart: number;
      testEnd: number;
      trainSharpe: number;
      testSharpe: number;
    }> = [];
    const foldSize = Math.floor(n / (numFolds + 1));
    for (let f = 0; f < numFolds; f++) {
      const tStart = 0;
      const tEnd = foldSize * (f + 1);
      const teStart = tEnd;
      const teEnd = Math.min(tEnd + foldSize, n);
      // Simulated Sharpe: train always looks good, test varies
      const tSharpe = 1.8 + Math.sin(f * 1.3 + 0.5) * 0.3;
      const teSharpe = 1.0 + Math.sin(f * 2.1 + 1.2) * 0.5 - f * 0.05;
      folds.push({
        fold: f + 1,
        trainStart: tStart,
        trainEnd: tEnd,
        testStart: teStart,
        testEnd: teEnd,
        trainSharpe: tSharpe,
        testSharpe: teSharpe,
      });
    }
    return folds;
  }, []);

  const avgTestSharpe =
    foldData.reduce((s, f) => s + f.testSharpe, 0) / foldData.length;

  const stabilityVerdict =
    avgTestSharpe > 1.0
      ? { label: 'Stable', color: '#51CF66', description: 'Parameters work consistently across folds.' }
      : avgTestSharpe > 0.5
        ? { label: 'Moderate', color: '#FF922B', description: 'Some degradation out-of-sample. Proceed with caution.' }
        : { label: 'Fragile', color: '#FF6B6B', description: 'Performance collapses out-of-sample. Likely overfit.' };

  const sharpeGap = trainSharpe - testSharpe;
  const splitLabel =
    sharpeGap < 2
      ? 'Healthy gap between train and test performance'
      : sharpeGap < 4
        ? 'Moderate overfitting — test performance drops noticeably'
        : 'Significant overfitting — the optimized parameters are too specialized';

  return (
    <Stack gap="xl">
      {/* Interactive element first */}
      <Text>
        {"Drag the slider to split data into training and testing. Watch the Sharpe ratio gap — that's the cost of "}
        <GlossaryLink term="Overfitting" />
        {"."}
      </Text>

      <Stack gap="sm">

        <Text size="sm" fw={600} c={sharpeGap < 3 ? 'blue.4' : 'red.4'}>
          {"Train: "}{Math.round(trainFraction * 100)}{"% | Test: "}{Math.round((1 - trainFraction) * 100)}{"% \u2014 "}{splitLabel}
        </Text>

        <Slider
          value={trainFraction}
          onChange={setTrainFraction}
          min={0.5}
          max={0.9}
          step={0.05}
          marks={[
            { value: 0.5, label: '50/50' },
            { value: 0.7, label: '70/30' },
            { value: 0.9, label: '90/10' },
          ]}
          label={(v) => `${Math.round(v * 100)}% train`}
          color={sharpeGap < 3 ? 'blue' : 'red'}
        />

        <PlotlyChart
          data={[
            {
              x: timestamps.slice(0, splitIndex),
              y: trainEquity,
              type: 'scatter',
              mode: 'lines',
              name: `Train (Sharpe: ${trainSharpe.toFixed(1)})`,
              line: { color: '#339AF0', width: 2 },
            },
            {
              x: timestamps.slice(splitIndex),
              y: testEquity,
              type: 'scatter',
              mode: 'lines',
              name: `Test (Sharpe: ${testSharpe.toFixed(1)})`,
              line: { color: '#FF922B', width: 2 },
            },
            {
              x: [splitIndex, splitIndex],
              y: [
                Math.min(...trainEquity, ...testEquity) - 20,
                Math.max(...trainEquity, ...testEquity) + 20,
              ],
              type: 'scatter',
              mode: 'lines',
              name: 'Split point',
              line: { color: '#909296', width: 2, dash: 'dash' },
            },
          ]}
          layout={{
            title: 'Equity Curve: Train vs. Test Performance',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Portfolio Value (\u20AC)' } },
            height: 350,
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />

        <Text size="sm">
          {"Notice how the blue (train) section almost always looks great — that's where the parameters were optimized. The orange (test) section shows what would "}
          <em>{"actually"}</em>
          {" happen with new data. The gap between them is the cost of overfitting."}
        </Text>
      </Stack>

      <RealDataSection intro="See real z-score signals on actual crypto data." showComparison={false}>
        {(data, isGoodPair) => (
          <Stack gap="md">
            <TabSignals data={data} />
          </Stack>
        )}
      </RealDataSection>

      {/* Explanation below the chart */}
      <Stack gap="sm">
        <Title order={4}>{"What you're seeing"}</Title>
        <Text>
          {"Grid search tries every parameter combination on historical data. The winning parameters are "}
          <em>{"perfectly tailored"}</em>
          {" to the data you tested on — like studying with the answer key. The train/test split reveals the truth: how do those parameters perform on unseen data?"}
        </Text>
      </Stack>

      {/* Walk-forward folds */}
      <Stack gap="sm">
        <Title order={4}>{"Walk-forward validation: the gold standard"}</Title>
        <Text>
          {"A single train/test split is better than nothing, but it only gives you one data point. Walk-forward goes further: it creates "}
          <strong>{`${numFolds} sequential folds`}</strong>
          {", each time training on past data and testing on the next unseen window. If performance is consistent across all folds, the strategy is robust."}
        </Text>

        <PlotlyChart
          data={[
            {
              x: foldData.map((f) => `Fold ${f.fold}`),
              y: foldData.map((f) => f.trainSharpe),
              type: 'bar',
              name: 'Train Sharpe',
              marker: { color: '#339AF0' },
            },
            {
              x: foldData.map((f) => `Fold ${f.fold}`),
              y: foldData.map((f) => f.testSharpe),
              type: 'bar',
              name: 'Test Sharpe',
              marker: { color: '#FF922B' },
            },
          ]}
          layout={{
            title: 'Walk-Forward Folds: Train vs. Test Sharpe',
            xaxis: { title: { text: 'Fold' } },
            yaxis: { title: { text: 'Sharpe Ratio' } },
            height: 300,
            barmode: 'group',
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />

        <Text size="sm">
          {"Average out-of-sample Sharpe: "}
          <strong style={{ color: stabilityVerdict.color }}>
            {avgTestSharpe.toFixed(2)}
          </strong>
          {" \u2014 Verdict: "}
          <strong style={{ color: stabilityVerdict.color }}>
            {stabilityVerdict.label}
          </strong>
        </Text>
        <Text size="sm" c="dimmed">
          {stabilityVerdict.description}
        </Text>
      </Stack>

      {/* Stability verdicts */}
      <Stack gap="sm">
        <Title order={4}>{"Stability verdicts"}</Title>
        <Text>
          <strong style={{ color: '#51CF66' }}>{"Stable"}</strong>
          {" \u2014 test performance is within 30% of training across all folds. These parameters are trustworthy."}
        </Text>
        <Text>
          <strong style={{ color: '#FF922B' }}>{"Moderate"}</strong>
          {" \u2014 some folds degrade significantly. The strategy may work, but consider smaller position sizes."}
        </Text>
        <Text>
          <strong style={{ color: '#FF6B6B' }}>{"Fragile"}</strong>
          {" \u2014 test performance is much worse than training. The parameters are overfit. Go back to research and re-evaluate the pair."}
        </Text>
      </Stack>

      {/* Naive vs walk-forward comparison */}
      <Stack gap="sm">
        <Title order={4}>{"Naive vs. walk-forward: the bottom line"}</Title>
        <Text>
          <strong>{"Naive optimization"}</strong>
          {" runs one big backtest on all data. Sharpe looks amazing. You deploy. It fails. Why? Because the parameters were fit to the past, not the future."}
        </Text>
        <Text>
          <strong>{"Walk-forward validation"}</strong>
          {" simulates what actually happens: optimize on past data, trade on new data, repeat. If the strategy holds across all folds, you have real evidence it works — not just a flattering backtest."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" you've learned the full pipeline. Time to put it all together and start your own research."}
      </Text>
    </Stack>
  );
}
