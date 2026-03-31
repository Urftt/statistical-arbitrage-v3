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
 * Lesson 4.2 — Your First Backtest
 *
 * Simulates a complete backtest and lets users step through individual trades
 * using a SegmentedControl. Each trade is highlighted on the z-score chart.
 */
export function Lesson4_2() {
  const n = 250;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.7 + Math.cos(i * 269.5 + seed * 0.7) * 0.35;

  // Generate a mean-reverting z-score series with clear trades
  const zScore = useMemo(() => {
    const values: number[] = [0];
    for (let i = 1; i < n; i++) {
      const meanRevert = -0.06 * values[i - 1];
      const cyclical = Math.sin(i * 0.08) * 0.15;
      values.push(values[i - 1] + meanRevert + noise(i, 42.0) * 0.45 + cyclical);
    }
    return values;
  }, []);

  // Run the full backtest to identify trades
  interface Trade {
    entry: number;
    exit: number;
    entryZ: number;
    exitZ: number;
    type: 'long_spread' | 'short_spread';
    pnl: number;
  }

  const trades = useMemo(() => {
    const entryThreshold = 1.5;
    const exitThreshold = 0.3;
    const capitalPerTrade = 500;
    const feeRate = 0.001;

    const result: Trade[] = [];
    let pos: 'flat' | 'long_spread' | 'short_spread' = 'flat';
    let tradeEntry = 0;
    let tradeEntryZ = 0;

    for (let i = 0; i < n; i++) {
      const z = zScore[i];
      if (pos === 'flat') {
        if (z > entryThreshold) {
          pos = 'short_spread';
          tradeEntry = i;
          tradeEntryZ = z;
        } else if (z < -entryThreshold) {
          pos = 'long_spread';
          tradeEntry = i;
          tradeEntryZ = z;
        }
      } else if (pos === 'long_spread' && z > -exitThreshold) {
        const rawPnl = (z - tradeEntryZ) * capitalPerTrade * 0.05;
        const fees = capitalPerTrade * feeRate * 2;
        result.push({
          entry: tradeEntry,
          exit: i,
          entryZ: tradeEntryZ,
          exitZ: z,
          type: 'long_spread',
          pnl: rawPnl - fees,
        });
        pos = 'flat';
      } else if (pos === 'short_spread' && z < exitThreshold) {
        const rawPnl = (tradeEntryZ - z) * capitalPerTrade * 0.05;
        const fees = capitalPerTrade * feeRate * 2;
        result.push({
          entry: tradeEntry,
          exit: i,
          entryZ: tradeEntryZ,
          exitZ: z,
          type: 'short_spread',
          pnl: rawPnl - fees,
        });
        pos = 'flat';
      }
    }
    return result;
  }, [zScore]);

  // Limit display to first 8 trades for readability
  const displayTrades = useMemo(() => trades.slice(0, 8), [trades]);
  const [selectedTrade, setSelectedTrade] = useState('0');
  const tradeIdx = Math.min(Number(selectedTrade), displayTrades.length - 1);
  const currentTrade = displayTrades[tradeIdx];

  // Build cumulative equity curve up to selected trade
  const equityCurve = useMemo(() => {
    const startCapital = 1000;
    const curve: number[] = new Array(n).fill(startCapital);
    const tradesUpTo = displayTrades.slice(0, tradeIdx + 1);

    for (const trade of tradesUpTo) {
      for (let i = trade.exit; i < n; i++) {
        curve[i] += trade.pnl;
      }
    }
    return curve;
  }, [tradeIdx, displayTrades]);

  // Summary metrics for all displayed trades up to current
  const tradesUpToCurrent = displayTrades.slice(0, tradeIdx + 1);
  const totalPnL = tradesUpToCurrent.reduce((sum, t) => sum + t.pnl, 0);
  const wins = tradesUpToCurrent.filter((t) => t.pnl > 0).length;
  const winRate = tradesUpToCurrent.length > 0 ? (wins / tradesUpToCurrent.length) * 100 : 0;

  return (
    <Stack gap="xl">
      <Text>
        {"Step through each trade in this simulated "}
        <GlossaryLink term="Backtesting">{"backtest"}</GlossaryLink>
        {" and watch the "}
        <GlossaryLink term="Equity Curve" />
        {" build up trade by trade."}
      </Text>

      {displayTrades.length > 0 && (
        <>
          <Stack gap="sm">
            <SegmentedControl
              value={selectedTrade}
              onChange={setSelectedTrade}
              data={displayTrades.map((_, i) => ({
                label: `Trade ${i + 1}`,
                value: String(i),
              }))}
              fullWidth
            />

            {currentTrade && (
              <Text
                size="sm"
                fw={600}
                c={currentTrade.pnl > 0 ? 'green.4' : 'red.4'}
              >
                {"Trade "}{tradeIdx + 1}{": "}
                {currentTrade.type === 'long_spread' ? 'Long spread' : 'Short spread'}
                {" | Entry z = "}{currentTrade.entryZ.toFixed(2)}
                {" → Exit z = "}{currentTrade.exitZ.toFixed(2)}
                {" | PnL: €"}{currentTrade.pnl.toFixed(2)}
              </Text>
            )}

            <PlotlyChart
              data={[
                {
                  x: timestamps,
                  y: zScore,
                  type: 'scatter',
                  mode: 'lines',
                  name: 'Z-Score',
                  line: { color: '#339AF0', width: 1.5 },
                },
                // Entry/exit thresholds
                {
                  x: [0, n - 1],
                  y: [1.5, 1.5],
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#FF6B6B', width: 1, dash: 'dash' },
                  showlegend: false,
                },
                {
                  x: [0, n - 1],
                  y: [-1.5, -1.5],
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#51CF66', width: 1, dash: 'dash' },
                  showlegend: false,
                },
                {
                  x: [0, n - 1],
                  y: [0, 0],
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#909296', width: 1, dash: 'dot' },
                  showlegend: false,
                },
                // Highlight the selected trade region
                ...(currentTrade
                  ? [
                      {
                        x: timestamps.slice(currentTrade.entry, currentTrade.exit + 1),
                        y: zScore.slice(currentTrade.entry, currentTrade.exit + 1),
                        type: 'scatter' as const,
                        mode: 'lines' as const,
                        name: `Trade ${tradeIdx + 1}`,
                        line: {
                          color: currentTrade.pnl > 0 ? '#51CF66' : '#FF6B6B',
                          width: 4,
                        },
                      },
                      // Entry marker
                      {
                        x: [currentTrade.entry],
                        y: [currentTrade.entryZ],
                        type: 'scatter' as const,
                        mode: 'markers' as const,
                        name: 'Entry',
                        marker: {
                          color: '#FF922B',
                          size: 12,
                          symbol: 'triangle-up',
                        },
                      },
                      // Exit marker
                      {
                        x: [currentTrade.exit],
                        y: [currentTrade.exitZ],
                        type: 'scatter' as const,
                        mode: 'markers' as const,
                        name: 'Exit',
                        marker: {
                          color: '#CC5DE8',
                          size: 12,
                          symbol: 'triangle-down',
                        },
                      },
                    ]
                  : []),
              ]}
              layout={{
                title: `Z-Score with Trade ${tradeIdx + 1} Highlighted`,
                xaxis: { title: { text: 'Time' } },
                yaxis: { title: { text: 'Z-Score (σ)' } },
                height: 350,
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
                  line: { color: '#339AF0', width: 2 },
                  fill: 'tozeroy',
                  fillcolor: 'rgba(51, 154, 240, 0.08)',
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
                title: `Equity Curve (After ${tradeIdx + 1} Trade${tradeIdx > 0 ? 's' : ''})`,
                xaxis: { title: { text: 'Time' } },
                yaxis: { title: { text: 'Portfolio Value (€)' } },
                height: 280,
                showlegend: false,
              }}
            />
          </Stack>

          {/* Summary metrics */}
          <Stack gap="sm">
            <Title order={4}>{"Running totals"}</Title>
            <Text>
              <strong>{"Total trades: "}</strong>
              {tradesUpToCurrent.length}
              {" of "}{displayTrades.length}
            </Text>
            <Text>
              <strong>{"Wins: "}</strong>
              <Text span c="green.4">{wins}</Text>
              {" | "}
              <strong>{"Losses: "}</strong>
              <Text span c="red.4">{tradesUpToCurrent.length - wins}</Text>
              {" | "}
              <strong>{<GlossaryLink term="Win Rate" />}{": "}</strong>
              {winRate.toFixed(0)}%
            </Text>
            <Text>
              <strong>{"Total PnL: "}</strong>
              <Text span c={totalPnL > 0 ? 'green.4' : 'red.4'} fw={600}>
                {"€"}{totalPnL.toFixed(2)}
              </Text>
            </Text>
          </Stack>
        </>
      )}

      <Stack gap="sm">
        <Title order={4}>{"What just happened?"}</Title>
        <Text>
          {"You just ran a full backtest. Each trade followed the same cycle: detect an extreme z-score, enter a position, wait for reversion, exit near zero. Some trades won, some lost — that's normal. What matters is the overall pattern."}
        </Text>
        <Text>
          {"For each trade, you saw where we entered (z-score crossed the threshold), where we exited (z-score returned near zero), and the profit or loss. Notice how winning trades tend to be the ones where the z-score made a clean round trip back to zero. Losing trades often happen when the z-score kept going further against us before reverting — or when fees ate up a small gain."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" how do you evaluate whether a backtest result is actually good? We'll learn to read the key metrics that separate promising strategies from dangerous ones."}
      </Text>
    </Stack>
  );
}
