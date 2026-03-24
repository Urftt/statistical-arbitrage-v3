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
 * Lesson 4.4 — Overfitting: The Silent Killer
 *
 * Interactive slider controls number of optimized parameters. Users see how
 * in-sample performance improves but out-of-sample degrades with more parameters.
 */
export function Lesson4_4() {
  const [numParams, setNumParams] = useState(2);

  const n = 150;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.6 + Math.cos(i * 269.5 + seed * 0.5) * 0.3;

  // Generate in-sample and out-of-sample equity curves
  // More parameters = better in-sample fit but worse out-of-sample
  const { inSample, outOfSample, inSampleSharpe, outOfSampleSharpe, inSampleDD, outOfSampleDD } = useMemo(() => {
    const isEq: number[] = [1000];
    const oosEq: number[] = [1000];

    // In-sample: gets better with more params (fitting to noise)
    // Trend improves, volatility decreases
    const isTrend = 0.15 + numParams * 0.12; // more params = steeper in-sample curve
    const isVol = Math.max(0.5, 3.5 - numParams * 0.3); // less volatile in-sample

    // Out-of-sample: degrades with more params (noise doesn't repeat)
    // Trend drops, volatility increases
    const oosTrend = 0.4 - numParams * 0.07; // more params = worse OOS trend
    const oosVol = 2.0 + numParams * 0.6; // more volatile OOS

    for (let i = 1; i < n; i++) {
      const isNoise = noise(i, 500.0) * isVol;
      isEq.push(isEq[i - 1] + isTrend + isNoise);

      const oosNoise = noise(i, 700.0) * oosVol;
      // Add regime breaks in OOS that don't exist in-sample
      const regimeShock = numParams > 5 && (i > 60 && i < 80) ? -2.5 : 0;
      const regimeShock2 = numParams > 7 && (i > 110 && i < 125) ? -3.0 : 0;
      oosEq.push(oosEq[i - 1] + oosTrend + oosNoise + regimeShock + regimeShock2);
    }

    // Compute Sharpe for both
    function computeSharpe(equity: number[]): number {
      const returns: number[] = [];
      for (let j = 1; j < equity.length; j++) {
        returns.push((equity[j] - equity[j - 1]) / equity[j - 1]);
      }
      const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
      const std = Math.sqrt(returns.reduce((s, r) => s + (r - mean) ** 2, 0) / returns.length);
      return std > 0 ? (mean / std) * Math.sqrt(252) : 0;
    }

    function computeMaxDD(equity: number[]): number {
      let peak = equity[0];
      let maxDd = 0;
      for (const eq of equity) {
        if (eq > peak) peak = eq;
        const dd = (peak - eq) / peak;
        if (dd > maxDd) maxDd = dd;
      }
      return maxDd;
    }

    return {
      inSample: isEq,
      outOfSample: oosEq,
      inSampleSharpe: computeSharpe(isEq),
      outOfSampleSharpe: computeSharpe(oosEq),
      inSampleDD: computeMaxDD(isEq),
      outOfSampleDD: computeMaxDD(oosEq),
    };
  }, [numParams]);

  // Sharpe gap as overfitting indicator
  const sharpeGap = inSampleSharpe - outOfSampleSharpe;
  const isOverfit = numParams > 4;
  const isSeverelyOverfit = numParams > 7;

  const overfitLabel =
    numParams <= 2
      ? 'Simple model — in-sample and out-of-sample perform similarly'
      : numParams <= 4
        ? 'Moderate complexity — slight gap appearing between IS and OOS'
        : numParams <= 7
          ? 'Overfitting risk — in-sample looks great but OOS is deteriorating'
          : 'Severely overfit — amazing in-sample, terrible out-of-sample';

  // Generate the Sharpe comparison across all parameter counts
  const sharpeComparison = useMemo(() => {
    const paramCounts = Array.from({ length: 10 }, (_, i) => i + 1);
    const isSharpes: number[] = [];
    const oosSharpes: number[] = [];

    for (const p of paramCounts) {
      const isEq: number[] = [1000];
      const oosEq: number[] = [1000];
      const isTr = 0.15 + p * 0.12;
      const isV = Math.max(0.5, 3.5 - p * 0.3);
      const oosTr = 0.4 - p * 0.07;
      const oosV = 2.0 + p * 0.6;

      for (let i = 1; i < n; i++) {
        isEq.push(isEq[i - 1] + isTr + noise(i, 500.0) * isV);
        const rs = p > 5 && (i > 60 && i < 80) ? -2.5 : 0;
        const rs2 = p > 7 && (i > 110 && i < 125) ? -3.0 : 0;
        oosEq.push(oosEq[i - 1] + oosTr + noise(i, 700.0) * oosV + rs + rs2);
      }

      function sh(eq: number[]): number {
        const ret: number[] = [];
        for (let j = 1; j < eq.length; j++) ret.push((eq[j] - eq[j - 1]) / eq[j - 1]);
        const m = ret.reduce((s, r) => s + r, 0) / ret.length;
        const sd = Math.sqrt(ret.reduce((s, r) => s + (r - m) ** 2, 0) / ret.length);
        return sd > 0 ? (m / sd) * Math.sqrt(252) : 0;
      }
      isSharpes.push(sh(isEq));
      oosSharpes.push(sh(oosEq));
    }
    return { paramCounts, isSharpes, oosSharpes };
  }, []);

  return (
    <Stack gap="xl">
      <Text>
        {"Drag the slider to add more optimized parameters and watch "}
        <GlossaryLink term="Overfitting" />
        {" in action — in-sample improves while out-of-sample collapses."}
      </Text>

      <Stack gap="sm">
        <Text size="sm" fw={600} c={isSeverelyOverfit ? 'red.4' : isOverfit ? 'orange.4' : 'teal.4'}>
          {numParams}{" parameter"}{numParams > 1 ? 's' : ''}{" — "}{overfitLabel}
        </Text>

        <Slider
          value={numParams}
          onChange={setNumParams}
          min={1}
          max={10}
          step={1}
          marks={[
            { value: 1, label: '1' },
            { value: 3, label: '3' },
            { value: 5, label: '5' },
            { value: 7, label: '7' },
            { value: 10, label: '10' },
          ]}
          label={(v) => `${v} params`}
          color={isSeverelyOverfit ? 'red' : isOverfit ? 'orange' : 'teal'}
        />

        {/* Side by side equity curves */}
        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: inSample,
              type: 'scatter',
              mode: 'lines',
              name: 'In-Sample',
              line: { color: '#339AF0', width: 2 },
            },
            {
              x: timestamps,
              y: outOfSample,
              type: 'scatter',
              mode: 'lines',
              name: 'Out-of-Sample',
              line: { color: '#CC5DE8', width: 2 },
            },
            {
              x: [0, n - 1],
              y: [1000, 1000],
              type: 'scatter',
              mode: 'lines',
              line: { color: '#909296', width: 1, dash: 'dash' },
              showlegend: false,
            },
          ]}
          layout={{
            title: `${numParams} Parameter${numParams > 1 ? 's' : ''}: In-Sample vs Out-of-Sample`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Portfolio Value (€)' } },
            height: 350,
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />

        {/* Metrics comparison */}
        <Stack gap={4}>
          <Text size="sm">
            <Text span c="#339AF0" fw={600}>
              <GlossaryLink term="In-Sample">{"In-Sample"}</GlossaryLink>
            </Text>
            {": Sharpe "}
            <Text span fw={600}>{inSampleSharpe.toFixed(2)}</Text>
            {" | Max DD "}
            <Text span fw={600}>{(inSampleDD * 100).toFixed(1)}%</Text>
          </Text>
          <Text size="sm">
            <Text span c="#CC5DE8" fw={600}>
              <GlossaryLink term="Out-of-Sample">{"Out-of-Sample"}</GlossaryLink>
            </Text>
            {": Sharpe "}
            <Text span fw={600}>{outOfSampleSharpe.toFixed(2)}</Text>
            {" | Max DD "}
            <Text span fw={600}>{(outOfSampleDD * 100).toFixed(1)}%</Text>
          </Text>
          <Text size="sm" c={isSeverelyOverfit ? 'red.4' : isOverfit ? 'orange.4' : 'teal.4'} fw={600}>
            {"Sharpe gap (IS − OOS): "}{sharpeGap.toFixed(2)}
            {sharpeGap > 2 ? ' — huge red flag!' : sharpeGap > 1 ? ' — concerning' : ' — acceptable'}
          </Text>
        </Stack>
      </Stack>

      {/* Sharpe across parameter counts */}
      <Stack gap="sm">
        <Title order={4}>{"The full picture: Sharpe vs. complexity"}</Title>
        <PlotlyChart
          data={[
            {
              x: sharpeComparison.paramCounts,
              y: sharpeComparison.isSharpes,
              type: 'scatter',
              mode: 'lines+markers',
              name: 'In-Sample Sharpe',
              line: { color: '#339AF0', width: 2 },
              marker: { size: 8 },
            },
            {
              x: sharpeComparison.paramCounts,
              y: sharpeComparison.oosSharpes,
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Out-of-Sample Sharpe',
              line: { color: '#CC5DE8', width: 2 },
              marker: { size: 8 },
            },
            // Highlight current selection
            {
              x: [numParams],
              y: [sharpeComparison.isSharpes[numParams - 1]],
              type: 'scatter',
              mode: 'markers',
              name: 'Current (IS)',
              marker: { color: '#339AF0', size: 14, symbol: 'diamond' },
              showlegend: false,
            },
            {
              x: [numParams],
              y: [sharpeComparison.oosSharpes[numParams - 1]],
              type: 'scatter',
              mode: 'markers',
              name: 'Current (OOS)',
              marker: { color: '#CC5DE8', size: 14, symbol: 'diamond' },
              showlegend: false,
            },
          ]}
          layout={{
            title: 'Sharpe Ratio vs. Number of Parameters',
            xaxis: { title: { text: 'Number of Optimized Parameters' }, dtick: 1 },
            yaxis: { title: { text: 'Sharpe Ratio' } },
            height: 350,
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />
        <Text size="sm" c="dimmed">
          {"The blue line keeps climbing — more parameters always improve the historical fit. But the purple line peaks early and then collapses. The growing gap between them is the hallmark of overfitting."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"Why this happens"}</Title>
        <Text>
          <GlossaryLink term="Overfitting" />
          {" occurs when your strategy is tuned so precisely to historical data that it captures "}
          <em>{"noise"}</em>
          {" instead of genuine patterns. The more parameters you optimize (entry threshold, exit threshold, lookback window, position size, stop-loss, etc.), the easier it is to fit the noise."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"The bias-variance tradeoff in trading"}</Title>
        <Text>
          {"In machine learning, this is called the "}
          <strong>{"bias-variance tradeoff"}</strong>
          {". A simple model (few parameters) has high bias — it might miss real patterns. A complex model (many parameters) has high variance — it fits noise that won't repeat."}
        </Text>
        <Text>
          {"In trading terms: "}
          <strong>{"bias"}</strong>
          {" means your strategy is too simple to capture the real edge. "}
          <strong>{"variance"}</strong>
          {" means your strategy is so complex that it's memorizing historical accidents. The sweet spot is 2–4 parameters for most pairs trading strategies."}
        </Text>
        <Text>
          {"Practical defenses against overfitting:"}
        </Text>
        <Text>
          <strong>{"1."}</strong>
          {" Keep it simple. Fewer parameters = less room to fit noise."}
        </Text>
        <Text>
          <strong>{"2."}</strong>
          {" Always validate "}
          <GlossaryLink term="Out-of-Sample" />
          {". If in-sample Sharpe is 3.0 but out-of-sample is 0.2, something is wrong."}
        </Text>
        <Text>
          <strong>{"3."}</strong>
          {" Use walk-forward analysis. Repeatedly train on a window, test on the next window, slide forward."}
        </Text>
        <Text>
          <strong>{"4."}</strong>
          {" Be skeptical of amazing backtests. If it looks too good to be true, it probably is."}
        </Text>
      </Stack>

      {/* Chapter wrap-up */}
      <Stack gap="sm" mt="md">
        <Title order={4}>{"Chapter 4 wrap-up"}</Title>
        <Text>
          {"You now have the complete toolkit for strategy development and evaluation:"}
        </Text>
        <Text>
          <strong>{"1."}</strong>
          {" "}
          <GlossaryLink term="Position Sizing" />
          {" controls your risk/reward ratio. Bigger isn't always better."}
        </Text>
        <Text>
          <strong>{"2."}</strong>
          {" "}
          <GlossaryLink term="Backtesting" />
          {" replays your strategy on historical data. Each trade follows the state machine: flat → position → flat."}
        </Text>
        <Text>
          <strong>{"3."}</strong>
          {" The "}
          <GlossaryLink term="Sharpe Ratio" />
          {", "}
          <GlossaryLink term="Maximum Drawdown" />
          {", "}
          <GlossaryLink term="Win Rate" />
          {", and "}
          <GlossaryLink term="Profit Factor" />
          {" tell you whether a strategy is worth trading."}
        </Text>
        <Text>
          <strong>{"4."}</strong>
          {" "}
          <GlossaryLink term="Overfitting" />
          {" is the silent killer. Always compare in-sample vs. out-of-sample performance, and keep your models simple."}
        </Text>
        <Text c="dimmed" size="sm" mt="xs">
          {"In the next chapter, we'll put it all together with walk-forward optimization and paper trading — the final steps before going live."}
        </Text>
      </Stack>
    </Stack>
  );
}
