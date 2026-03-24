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
 * Lesson 4.1 — From Signals to Strategy
 *
 * Interactive slider controls position size. Users see how bigger positions
 * amplify both gains and losses on the equity curve.
 */
export function Lesson4_1() {
  const [positionSize, setPositionSize] = useState(0.5);

  const n = 200;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.8 + Math.cos(i * 269.5 + seed * 0.3) * 0.4;

  // Generate a mean-reverting z-score series with enough volatility to trigger signals
  const zScore = useMemo(() => {
    const values: number[] = [0];
    for (let i = 1; i < n; i++) {
      const meanRevert = -0.12 * values[i - 1];
      // Stronger noise so z-score regularly crosses ±1.5
      const n_i = noise(i, 311.7) * 0.9 + Math.sin(i * 0.15) * 0.4;
      values.push(values[i - 1] + meanRevert + n_i);
    }
    return values;
  }, []);

  // Generate signals and PnL based on z-score thresholds
  const { equityCurve, peakDrawdown } = useMemo(() => {
    const entryThreshold = 1.5;
    const exitThreshold = 0.3;
    const feeRate = 0.001; // 0.1% per trade
    const capital = 1000;

    type Position = 'flat' | 'long_spread' | 'short_spread';
    const sig: Position[] = [];
    let pos: Position = 'flat';
    let equity = capital;
    const eqCurve: number[] = [];
    const tradeList: { entry: number; exit: number; pnl: number; type: Position }[] = [];
    let tradeEntry = 0;
    let tradeEntryZ = 0;

    for (let i = 0; i < n; i++) {
      const z = zScore[i];

      if (pos === 'flat') {
        if (z > entryThreshold) {
          pos = 'short_spread';
          tradeEntry = i;
          tradeEntryZ = z;
          equity -= capital * positionSize * feeRate; // entry fee
        } else if (z < -entryThreshold) {
          pos = 'long_spread';
          tradeEntry = i;
          tradeEntryZ = z;
          equity -= capital * positionSize * feeRate;
        }
      } else if (pos === 'long_spread') {
        // PnL from z-score moving up (spread narrowing)
        const dz = zScore[i] - zScore[i - 1];
        equity += dz * capital * positionSize * 0.05;
        if (z > -exitThreshold) {
          equity -= capital * positionSize * feeRate; // exit fee
          const pnl = (z - tradeEntryZ) * capital * positionSize * 0.05;
          tradeList.push({ entry: tradeEntry, exit: i, pnl, type: 'long_spread' });
          pos = 'flat';
        }
      } else if (pos === 'short_spread') {
        const dz = zScore[i] - zScore[i - 1];
        equity -= dz * capital * positionSize * 0.05;
        if (z < exitThreshold) {
          equity -= capital * positionSize * feeRate;
          const pnl = (tradeEntryZ - z) * capital * positionSize * 0.05;
          tradeList.push({ entry: tradeEntry, exit: i, pnl, type: 'short_spread' });
          pos = 'flat';
        }
      }

      sig.push(pos);
      eqCurve.push(equity);
    }

    // Peak drawdown
    let peak = eqCurve[0];
    let maxDd = 0;
    for (const eq of eqCurve) {
      if (eq > peak) peak = eq;
      const dd = (peak - eq) / peak;
      if (dd > maxDd) maxDd = dd;
    }

    return { signals: sig, equityCurve: eqCurve, trades: tradeList, peakDrawdown: maxDd };
  }, [positionSize, zScore]);

  const totalPnL = equityCurve[equityCurve.length - 1] - 1000;
  const isProfit = totalPnL > 0;
  const riskLevel =
    positionSize < 0.3
      ? 'Conservative — small gains, small losses'
      : positionSize < 0.6
        ? 'Moderate — balanced risk/reward'
        : positionSize < 0.85
          ? 'Aggressive — amplified swings'
          : 'Maximum risk — equity swings are extreme';

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"You know how to find pairs, test for cointegration, and generate "}
          <GlossaryLink term="Z-Score" />
          {" signals. But a signal alone isn't a strategy. To turn signals into actual trades, you need three more ingredients: "}
          <GlossaryLink term="Position Sizing" />
          {", capital allocation, and fees."}
        </Text>
        <Text>
          {"Every trade follows a simple state machine: "}
          <strong>{"flat \u2192 long_spread \u2192 flat"}</strong>
          {" or "}
          <strong>{"flat \u2192 short_spread \u2192 flat"}</strong>
          {". When the z-score crosses the "}
          <GlossaryLink term="Entry Signal" />
          {" threshold (\u00B11.5\u03C3), you open a position. When it returns near zero (the "}
          <GlossaryLink term="Exit Signal" />
          {"), you close it."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"The position size lever"}</Title>
        <Text>
          {"How much of your capital do you put into each trade? This single decision has a massive impact on both returns "}
          <em>{"and"}</em>
          {" risk. Drag the slider to see it for yourself."}
        </Text>

        <Text size="sm" fw={600} c={positionSize < 0.6 ? 'blue.4' : 'orange.4'}>
          {"Position size: "}{Math.round(positionSize * 100)}{"% of capital \u2014 "}{riskLevel}
        </Text>

        <Slider
          value={positionSize}
          onChange={setPositionSize}
          min={0.1}
          max={1.0}
          step={0.05}
          marks={[
            { value: 0.1, label: '10%' },
            { value: 0.5, label: '50%' },
            { value: 1.0, label: '100%' },
          ]}
          label={(v) => `${Math.round(v * 100)}%`}
          color={positionSize < 0.6 ? 'blue' : 'orange'}
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: zScore,
              type: 'scatter',
              mode: 'lines',
              name: 'Z-Score',
              line: { color: '#339AF0', width: 2 },
            },
            {
              x: [0, n - 1],
              y: [1.5, 1.5],
              type: 'scatter',
              mode: 'lines',
              name: 'Short entry (+1.5\u03C3)',
              line: { color: '#FF6B6B', width: 1, dash: 'dash' },
            },
            {
              x: [0, n - 1],
              y: [-1.5, -1.5],
              type: 'scatter',
              mode: 'lines',
              name: 'Long entry (-1.5\u03C3)',
              line: { color: '#51CF66', width: 1, dash: 'dash' },
            },
            {
              x: [0, n - 1],
              y: [0, 0],
              type: 'scatter',
              mode: 'lines',
              line: { color: '#909296', width: 1, dash: 'dot' },
              showlegend: false,
            },
          ]}
          layout={{
            title: 'Z-Score with Entry/Exit Thresholds',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Z-Score (\u03C3)' } },
            height: 300,
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: equityCurve,
              type: 'scatter',
              mode: 'lines',
              name: 'Equity',
              line: {
                color: isProfit ? '#339AF0' : '#FF6B6B',
                width: 2,
              },
              fill: 'tozeroy',
              fillcolor: isProfit
                ? 'rgba(51, 154, 240, 0.08)'
                : 'rgba(255, 107, 107, 0.08)',
            },
            {
              x: [0, n - 1],
              y: [1000, 1000],
              type: 'scatter',
              mode: 'lines',
              name: 'Starting capital',
              line: { color: '#909296', width: 1, dash: 'dash' },
            },
          ]}
          layout={{
            title: `Equity Curve \u2014 PnL: \u20AC${totalPnL.toFixed(2)} | Max Drawdown: ${(peakDrawdown * 100).toFixed(1)}%`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Portfolio Value (\u20AC)' } },
            height: 300,
            showlegend: false,
          }}
        />
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"The key takeaway"}</Title>
        <Text>
          <strong>{"Bigger positions = bigger wins AND bigger losses."}</strong>
          {" There's no free lunch. A 100% position size doubles your returns compared to 50%, but it also doubles your drawdowns. Professional traders typically risk 10\u201330% per trade."}
        </Text>
        <Text>
          {"Don't forget fees. Each trade costs ~0.1% (Bitvavo), which eats into small gains. With large position sizes, fees are a bigger absolute cost. Over hundreds of trades, fees compound significantly."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"The state machine"}</Title>
        <Text>
          {"Every strategy follows the same cycle. We start "}
          <strong>{"flat"}</strong>
          {" (no position). When the z-score crosses our entry threshold, we open a position: "}
          <strong>{"long_spread"}</strong>
          {" if z < -1.5\u03C3 (spread is unusually low, expect it to rise) or "}
          <strong>{"short_spread"}</strong>
          {" if z > +1.5\u03C3 (spread is unusually high, expect it to fall)."}
        </Text>
        <Text>
          {"When the z-score returns near zero, we close the position and go back to "}
          <strong>{"flat"}</strong>
          {". Then we wait for the next signal. This cycle repeats: flat \u2192 position \u2192 flat \u2192 position \u2192 flat."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" let's put it all together and run a full "}
        <GlossaryLink term="Backtesting">{"backtest"}</GlossaryLink>
        {" \u2014 watching each trade unfold step by step."}
      </Text>
    </Stack>
  );
}
