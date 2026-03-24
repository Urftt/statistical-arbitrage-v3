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
 * Lesson 4.3 — Reading Backtest Results
 *
 * Simulated results dashboard with traffic-light metric coloring.
 * SegmentedControl toggles between different metric views.
 */
export function Lesson4_3() {
  const [view, setView] = useState('overview');

  // Simulate three strategies with different characteristics
  const strategies = useMemo(() => {
    const n = 200;

    // Deterministic noise
    const noise = (i: number, seed: number) =>
      Math.sin(i * 127.1 + seed) * 0.6 + Math.cos(i * 269.5 + seed * 0.5) * 0.3;

    // Strategy A: Good — steady upward equity, moderate drawdown
    const eqA: number[] = [1000];
    for (let i = 1; i < n; i++) {
      const trend = 0.35;
      const vol = noise(i, 100.0) * 4;
      eqA.push(Math.max(eqA[i - 1] + trend + vol, eqA[i - 1] * 0.97));
    }

    // Strategy B: Mediocre — choppy, small gains
    const eqB: number[] = [1000];
    for (let i = 1; i < n; i++) {
      const trend = 0.08;
      const vol = noise(i, 200.0) * 6;
      eqB.push(eqB[i - 1] + trend + vol);
    }

    // Strategy C: Bad — big drawdown, net loss
    const eqC: number[] = [1000];
    for (let i = 1; i < n; i++) {
      const trend = -0.15;
      const vol = noise(i, 300.0) * 8;
      const regime = i > 80 && i < 140 ? -1.2 : 0.3;
      eqC.push(eqC[i - 1] + trend + vol + regime);
    }

    // Compute metrics for each
    function computeMetrics(equity: number[]) {
      const returns: number[] = [];
      for (let i = 1; i < equity.length; i++) {
        returns.push((equity[i] - equity[i - 1]) / equity[i - 1]);
      }
      const meanRet = returns.reduce((s, r) => s + r, 0) / returns.length;
      const stdRet = Math.sqrt(
        returns.reduce((s, r) => s + (r - meanRet) ** 2, 0) / returns.length
      );
      const sharpe = stdRet > 0 ? (meanRet / stdRet) * Math.sqrt(252) : 0;

      // Max drawdown
      let peak = equity[0];
      let maxDd = 0;
      for (const eq of equity) {
        if (eq > peak) peak = eq;
        const dd = (peak - eq) / peak;
        if (dd > maxDd) maxDd = dd;
      }

      // Simulated trade-level stats
      const totalPnL = equity[equity.length - 1] - equity[0];
      const winRate = sharpe > 1 ? 62 : sharpe > 0.3 ? 51 : 38;
      const profitFactor = sharpe > 1 ? 1.85 : sharpe > 0.3 ? 1.12 : 0.72;

      return {
        equity,
        sharpe,
        maxDrawdown: maxDd,
        winRate,
        profitFactor,
        totalPnL,
        totalTrades: Math.round(40 + Math.abs(noise(1, equity.length)) * 20),
      };
    }

    return {
      timestamps: Array.from({ length: n }, (_, i) => i),
      good: computeMetrics(eqA),
      mediocre: computeMetrics(eqB),
      bad: computeMetrics(eqC),
    };
  }, []);

  // Traffic light colors for metrics
  function sharpeColor(v: number): string {
    if (v >= 1.5) return '#20C997';
    if (v >= 0.8) return '#51CF66';
    if (v >= 0.3) return '#FF922B';
    return '#FF6B6B';
  }
  function drawdownColor(v: number): string {
    if (v <= 0.10) return '#20C997';
    if (v <= 0.20) return '#51CF66';
    if (v <= 0.35) return '#FF922B';
    return '#FF6B6B';
  }
  function winRateColor(v: number): string {
    if (v >= 60) return '#20C997';
    if (v >= 50) return '#51CF66';
    if (v >= 40) return '#FF922B';
    return '#FF6B6B';
  }
  function profitFactorColor(v: number): string {
    if (v >= 1.5) return '#20C997';
    if (v >= 1.2) return '#51CF66';
    if (v >= 1.0) return '#FF922B';
    return '#FF6B6B';
  }

  type StrategyKey = 'good' | 'mediocre' | 'bad';
  const strategyLabels: Record<StrategyKey, string> = {
    good: 'Strategy A (Strong)',
    mediocre: 'Strategy B (Mediocre)',
    bad: 'Strategy C (Poor)',
  };
  const strategyColors: Record<StrategyKey, string> = {
    good: '#51CF66',
    mediocre: '#FF922B',
    bad: '#FF6B6B',
  };

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"A backtest produces numbers. Lots of numbers. But which ones matter? Let's look at three simulated strategies and learn to read the four metrics that tell you whether a strategy is worth pursuing \u2014 or whether it belongs in the trash."}
        </Text>
        <Text>
          {"Switch between views to focus on each metric. We'll use traffic-light colors: "}
          <Text span c="#20C997" fw={600}>{"green = good"}</Text>
          {", "}
          <Text span c="#FF922B" fw={600}>{"orange = caution"}</Text>
          {", "}
          <Text span c="#FF6B6B" fw={600}>{"red = danger"}</Text>
          {"."}
        </Text>
      </Stack>

      <SegmentedControl
        value={view}
        onChange={setView}
        data={[
          { label: 'Overview', value: 'overview' },
          { label: 'Sharpe Ratio', value: 'sharpe' },
          { label: 'Max Drawdown', value: 'drawdown' },
          { label: 'Win Rate & PF', value: 'winrate' },
        ]}
        fullWidth
      />

      {/* Overview: all three equity curves */}
      {view === 'overview' && (
        <Stack gap="sm">
          <Title order={4}>{"Three strategies, three stories"}</Title>
          <Text size="sm" c="dimmed">
            {"Each line is the equity curve of a different strategy. Before looking at any numbers, which one would you want to trade?"}
          </Text>
          <PlotlyChart
            data={(['good', 'mediocre', 'bad'] as StrategyKey[]).map((key) => ({
              x: strategies.timestamps,
              y: strategies[key].equity,
              type: 'scatter' as const,
              mode: 'lines' as const,
              name: strategyLabels[key],
              line: { color: strategyColors[key], width: 2 },
            }))}
            layout={{
              title: 'Equity Curves: Three Strategies Compared',
              xaxis: { title: { text: 'Time (days)' } },
              yaxis: { title: { text: 'Portfolio Value (\u20AC)' } },
              height: 380,
              showlegend: true,
              legend: { x: 0, y: 1.15, orientation: 'h' },
            }}
          />
          <Text size="sm">
            {"Strategy A climbs steadily. Strategy B chops around with tiny gains. Strategy C has a devastating drawdown mid-way. Now let's put numbers on these impressions."}
          </Text>
        </Stack>
      )}

      {/* Sharpe Ratio */}
      {view === 'sharpe' && (
        <Stack gap="sm">
          <Title order={4}>
            <GlossaryLink term="Sharpe Ratio" />
            {" \u2014 Return per unit of risk"}
          </Title>
          <Text>
            {"The Sharpe ratio measures how much return you earn for each unit of volatility. Formula: (mean return \u2212 risk-free rate) / standard deviation of returns. Higher is better."}
          </Text>
          <Text size="sm" c="dimmed">
            {"Below 0.5 \u2014 not worth the risk. 0.5\u20131.0 \u2014 decent. 1.0\u20132.0 \u2014 strong. Above 2.0 \u2014 excellent (or suspicious)."}
          </Text>
          <PlotlyChart
            data={[
              {
                x: Object.values(strategyLabels),
                y: [strategies.good.sharpe, strategies.mediocre.sharpe, strategies.bad.sharpe],
                type: 'bar',
                marker: {
                  color: [
                    sharpeColor(strategies.good.sharpe),
                    sharpeColor(strategies.mediocre.sharpe),
                    sharpeColor(strategies.bad.sharpe),
                  ],
                },
                text: [
                  strategies.good.sharpe.toFixed(2),
                  strategies.mediocre.sharpe.toFixed(2),
                  strategies.bad.sharpe.toFixed(2),
                ],
                textposition: 'outside' as const,
              },
            ]}
            layout={{
              title: 'Sharpe Ratio Comparison',
              yaxis: { title: { text: 'Sharpe Ratio' }, zeroline: true },
              height: 350,
              showlegend: false,
            }}
          />
          <Text size="sm">
            {"Strategy A has a healthy Sharpe \u2014 its gains are consistent relative to its volatility. Strategy C's negative Sharpe tells you it loses money on a risk-adjusted basis. You'd be better off holding cash."}
          </Text>
        </Stack>
      )}

      {/* Max Drawdown */}
      {view === 'drawdown' && (
        <Stack gap="sm">
          <Title order={4}>
            <GlossaryLink term="Maximum Drawdown" />
            {" \u2014 The worst drop"}
          </Title>
          <Text>
            {"Max drawdown is the largest peak-to-trough decline in your equity curve. It answers: \"what's the worst loss I would have experienced?\" Even profitable strategies have drawdowns \u2014 the question is whether they're survivable."}
          </Text>
          <PlotlyChart
            data={[
              {
                x: Object.values(strategyLabels),
                y: [
                  strategies.good.maxDrawdown * 100,
                  strategies.mediocre.maxDrawdown * 100,
                  strategies.bad.maxDrawdown * 100,
                ],
                type: 'bar',
                marker: {
                  color: [
                    drawdownColor(strategies.good.maxDrawdown),
                    drawdownColor(strategies.mediocre.maxDrawdown),
                    drawdownColor(strategies.bad.maxDrawdown),
                  ],
                },
                text: [
                  `${(strategies.good.maxDrawdown * 100).toFixed(1)}%`,
                  `${(strategies.mediocre.maxDrawdown * 100).toFixed(1)}%`,
                  `${(strategies.bad.maxDrawdown * 100).toFixed(1)}%`,
                ],
                textposition: 'outside' as const,
              },
            ]}
            layout={{
              title: 'Maximum Drawdown Comparison',
              yaxis: { title: { text: 'Max Drawdown (%)' } },
              height: 350,
              showlegend: false,
            }}
          />
          <Text size="sm">
            {"A 10% drawdown is uncomfortable. A 30%+ drawdown is devastating \u2014 you need a 43% gain just to break even after a 30% loss. Strategy C's deep drawdown would shake most traders out of the position before it could recover."}
          </Text>
        </Stack>
      )}

      {/* Win Rate & Profit Factor */}
      {view === 'winrate' && (
        <Stack gap="sm">
          <Title order={4}>
            <GlossaryLink term="Win Rate" />
            {" & "}
            <GlossaryLink term="Profit Factor" />
          </Title>
          <Text>
            {"Win rate alone can be misleading. A 90% win rate with tiny wins and enormous losses is a losing strategy. That's why we pair it with profit factor (gross profits / gross losses). Together, they tell the full story."}
          </Text>
          <PlotlyChart
            data={[
              {
                x: Object.values(strategyLabels),
                y: [strategies.good.winRate, strategies.mediocre.winRate, strategies.bad.winRate],
                type: 'bar',
                name: 'Win Rate (%)',
                marker: {
                  color: [
                    winRateColor(strategies.good.winRate),
                    winRateColor(strategies.mediocre.winRate),
                    winRateColor(strategies.bad.winRate),
                  ],
                },
                text: [
                  `${strategies.good.winRate}%`,
                  `${strategies.mediocre.winRate}%`,
                  `${strategies.bad.winRate}%`,
                ],
                textposition: 'outside' as const,
              },
            ]}
            layout={{
              title: 'Win Rate Comparison',
              yaxis: { title: { text: 'Win Rate (%)' }, range: [0, 80] },
              height: 300,
              showlegend: false,
            }}
          />
          <PlotlyChart
            data={[
              {
                x: Object.values(strategyLabels),
                y: [
                  strategies.good.profitFactor,
                  strategies.mediocre.profitFactor,
                  strategies.bad.profitFactor,
                ],
                type: 'bar',
                name: 'Profit Factor',
                marker: {
                  color: [
                    profitFactorColor(strategies.good.profitFactor),
                    profitFactorColor(strategies.mediocre.profitFactor),
                    profitFactorColor(strategies.bad.profitFactor),
                  ],
                },
                text: [
                  strategies.good.profitFactor.toFixed(2),
                  strategies.mediocre.profitFactor.toFixed(2),
                  strategies.bad.profitFactor.toFixed(2),
                ],
                textposition: 'outside' as const,
              },
              {
                x: [Object.values(strategyLabels)[0], Object.values(strategyLabels)[2]],
                y: [1.0, 1.0],
                type: 'scatter',
                mode: 'lines',
                name: 'Breakeven (1.0)',
                line: { color: '#909296', width: 1, dash: 'dash' },
              },
            ]}
            layout={{
              title: 'Profit Factor Comparison',
              yaxis: { title: { text: 'Profit Factor' } },
              height: 300,
              showlegend: false,
            }}
          />
          <Text size="sm">
            {"Strategy A wins 62% of trades "}
            <em>{"and"}</em>
            {" has a profit factor of 1.85 \u2014 its wins are nearly twice its losses. Strategy C wins only 38% of trades with a profit factor below 1.0 \u2014 it literally loses more than it makes. A profit factor below 1.0 means the strategy is a net loser, regardless of how many trades it takes."}
          </Text>
        </Stack>
      )}

      <Stack gap="sm">
        <Title order={4}>{"The metric cheat sheet"}</Title>
        <Text>
          <Text span c={sharpeColor(1.2)} fw={600}>{"Sharpe > 1.0"}</Text>
          {" \u2014 Good risk-adjusted returns. "}
          <Text span c={drawdownColor(0.15)} fw={600}>{"Max DD < 20%"}</Text>
          {" \u2014 Manageable worst case. "}
          <Text span c={winRateColor(55)} fw={600}>{"Win Rate > 50%"}</Text>
          {" \u2014 More winners than losers. "}
          <Text span c={profitFactorColor(1.5)} fw={600}>{"PF > 1.5"}</Text>
          {" \u2014 Wins substantially outweigh losses."}
        </Text>
        <Text size="sm" c="dimmed">
          {"No single metric tells the whole story. Always look at all four together. A high Sharpe with extreme drawdown might indicate a strategy that works until it doesn't."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" the most dangerous trap in backtesting \u2014 "}
        <GlossaryLink term="Overfitting" />
        {". A strategy that looks amazing on historical data but fails completely on new data."}
      </Text>
    </Stack>
  );
}
