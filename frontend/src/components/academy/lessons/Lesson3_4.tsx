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
import { RealDataSection, TabSpread, TabHalfLife } from '@/components/academy/real-data';

/**
 * Lesson 3.4 — Half-Life: How Fast Does It Revert?
 *
 * Interactive slider controls the mean-reversion speed (half-life).
 * Users see an Ornstein-Uhlenbeck process with configurable decay.
 * Includes chapter wrap-up.
 */
export function Lesson3_4() {
  const [halfLife, setHalfLife] = useState(20);

  const n = 250;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Deterministic pseudo-random noise
  const noise = (i: number, seed: number) =>
    Math.sin(i * 127.1 + seed) * 0.7 + Math.cos(i * 269.5 + seed * 0.7) * 0.5;

  // Generate OU process: x[t] = phi * x[t-1] + noise
  // phi = exp(-log(2) / halfLife), so half-life is exact
  const { spread, decayCurve, phi } = useMemo(() => {
    const phiVal = Math.exp(-Math.LN2 / halfLife);
    const values: number[] = [3.0]; // start away from mean to show decay

    for (let i = 1; i < n; i++) {
      // Kick the spread away from zero periodically to show reversion
      const kick =
        i === 60 ? 3.5 :
        i === 130 ? -3.0 :
        i === 190 ? 2.8 :
        0;
      values.push(values[i - 1] * phiVal + noise(i, 311.7) * 0.6 + kick);
    }

    // Theoretical decay curve from initial value
    const decay: number[] = [];
    for (let i = 0; i < n; i++) {
      decay.push(3.0 * Math.pow(phiVal, i));
    }

    return { spread: values, decayCurve: decay, phi: phiVal };
  }, [halfLife]);

  // Compute how many bars until 50% decay for display
  const halfLifeLabel =
    halfLife < 15
      ? 'Fast reversion — great for trading, positions close quickly'
      : halfLife < 30
        ? 'Moderate speed — reasonable for daily trading timeframes'
        : halfLife < 50
          ? 'Slow reversion — requires patience, capital tied up longer'
          : 'Very slow — spread takes too long to revert for most strategies';

  const isGoodSpeed = halfLife < 35;

  return (
    <Stack gap="xl">
      <Text>
        {"Drag the slider to control the "}
        <GlossaryLink term="Half-Life" />
        {" and watch how fast the spread snaps back to zero after each shock."}
      </Text>

      {/* Interactive slider and charts — immediately visible */}
      <Stack gap="sm">
        <Text size="sm" fw={600} c={isGoodSpeed ? 'blue.4' : 'red.4'}>
          {halfLifeLabel}
        </Text>

        <Text size="sm" c="dimmed">
          {`\u03C6 = ${phi.toFixed(4)} | Half-life = ${halfLife} periods | 90% reversion \u2248 ${Math.round(halfLife * 3.32)} periods`}
        </Text>

        <Slider
          value={halfLife}
          onChange={setHalfLife}
          min={5}
          max={80}
          step={1}
          marks={[
            { value: 5, label: '5' },
            { value: 20, label: '20' },
            { value: 40, label: '40' },
            { value: 60, label: '60' },
            { value: 80, label: '80' },
          ]}
          label={(v) => `${v} bars`}
          color={isGoodSpeed ? 'blue' : 'red'}
        />

        {/* Spread chart showing OU process */}
        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: spread,
              type: 'scatter',
              mode: 'lines',
              name: 'Spread (OU Process)',
              line: { color: '#CC5DE8', width: 2 },
            },
            // Zero mean line
            {
              x: [0, n - 1],
              y: [0, 0],
              type: 'scatter',
              mode: 'lines',
              name: 'Mean (zero)',
              line: { color: '#909296', width: 1, dash: 'dash' },
              showlegend: false,
            },
          ]}
          layout={{
            title: `Spread with Half-Life = ${halfLife} Periods`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Spread Value' } },
            height: 300,
            showlegend: false,
            annotations: [
              {
                x: 60,
                y: 3.5,
                text: 'Shock',
                showarrow: true,
                arrowhead: 2,
                ax: 0,
                ay: -30,
                font: { color: '#FF922B', size: 11 },
                arrowcolor: '#FF922B',
              },
              {
                x: 130,
                y: -3.0,
                text: 'Shock',
                showarrow: true,
                arrowhead: 2,
                ax: 0,
                ay: 30,
                font: { color: '#FF922B', size: 11 },
                arrowcolor: '#FF922B',
              },
              {
                x: 190,
                y: 2.8,
                text: 'Shock',
                showarrow: true,
                arrowhead: 2,
                ax: 0,
                ay: -30,
                font: { color: '#FF922B', size: 11 },
                arrowcolor: '#FF922B',
              },
            ],
          }}
        />

        {/* Theoretical decay curve */}
        <PlotlyChart
          data={[
            {
              x: timestamps.slice(0, 80),
              y: decayCurve.slice(0, 80),
              type: 'scatter',
              mode: 'lines',
              name: 'Theoretical Decay',
              line: { color: '#FF922B', width: 2.5 },
            },
            // 50% mark
            {
              x: [0, halfLife, halfLife],
              y: [1.5, 1.5, 0],
              type: 'scatter',
              mode: 'lines',
              name: '50% level',
              line: { color: '#20C997', width: 1.5, dash: 'dot' },
            },
            // Half-life marker
            {
              x: [halfLife],
              y: [1.5],
              type: 'scatter',
              mode: 'text+markers',
              name: `Half-life (${halfLife})`,
              text: [`t = ${halfLife}`],
              textposition: 'top center',
              marker: { color: '#20C997', size: 10 },
              textfont: { color: '#20C997' },
            },
          ]}
          layout={{
            title: `Theoretical Decay Curve (\u03C6 = ${phi.toFixed(3)})`,
            xaxis: { title: { text: 'Periods After Shock' }, range: [0, 80] },
            yaxis: { title: { text: 'Remaining Deviation' } },
            height: 260,
            showlegend: true,
            legend: { x: 0, y: 1.15, orientation: 'h' },
          }}
        />
      </Stack>

      <RealDataSection intro="See how fast real spreads revert.">
        {(data, isGoodPair) => (
          <Stack gap="md">
            <TabSpread data={data} />
            <TabHalfLife data={data} />
          </Stack>
        )}
      </RealDataSection>

      {/* Detailed explanation below the charts */}
      <Stack gap="md">
        <Title order={4}>{"Understanding the half-life"}</Title>
        <Text>
          {"The "}
          <GlossaryLink term="Half-Life" />
          {" measures how many periods it takes for a deviation to shrink by half. A spread with a half-life of 10 bars that starts 2\u03C3 above the mean will be about 1\u03C3 above the mean after 10 bars. Shorter half-life means faster reversion, which means faster trades and less time exposed to risk."}
        </Text>
        <Text>
          {"For most pairs trading strategies, you want a half-life between 5 and 40 periods \u2014 fast enough to be practical, but not so fast that transaction costs eat the profit."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"The math behind half-life"}</Title>
        <Text>
          {"The spread follows an AR(1) process: "}
          <Text component="span" ff="monospace" fw={600} c="blue.4">
            {"spread[t] = \u03C6 \u00D7 spread[t-1] + noise"}
          </Text>
          {" where \u03C6 (phi) is the autoregressive coefficient. Values of \u03C6 close to 1 mean slow decay; values close to 0 mean fast decay."}
        </Text>
        <Text>
          {"The half-life formula: "}
          <Text component="span" ff="monospace" fw={600} c="blue.4">
            {"half_life = -log(2) / log(\u03C6)"}
          </Text>
          {" In practice, we estimate \u03C6 by regressing spread[t] on spread[t-1]."}
        </Text>
      </Stack>

      <Stack gap="sm">
        <Title order={4}>{"What's a good half-life?"}</Title>
        <Text>
          {"For daily data, a half-life of 5 to 40 bars is the sweet spot. Faster than 5 and the reversion happens within the bid-ask spread \u2014 you can't profit after fees. Slower than 40 and your capital is locked up too long, dragging down returns."}
        </Text>
        <Text>
          {"Half-life also helps you size your lookback window for z-scores. A common rule of thumb: set the rolling window to about 2-4 times the half-life. That gives enough history to estimate the mean and standard deviation while staying relevant to the current regime."}
        </Text>
      </Stack>

      {/* Chapter wrap-up */}
      <Stack gap="sm" mt="lg">
        <Title order={3}>{"Chapter 3 Wrap-Up: The Spread & Signals"}</Title>
        <Text>
          {"In this chapter you learned the complete signal pipeline that powers a pairs trading strategy:"}
        </Text>
        <Text>
          <strong>{"1. Build the spread"}</strong>
          {" using the "}
          <GlossaryLink term="Hedge Ratio" />
          {" from OLS. The spread = price_A - \u03B2 \u00D7 price_B. Getting \u03B2 right makes the spread stationary."}
        </Text>
        <Text>
          <strong>{"2. Standardize with z-scores"}</strong>
          {" using a rolling window. The "}
          <GlossaryLink term="Z-Score" />
          {" tells you how extreme the current spread is in units of standard deviation."}
        </Text>
        <Text>
          <strong>{"3. Generate signals"}</strong>
          {" by comparing z-scores to entry and exit thresholds. Enter when the z-score is extreme; exit when it reverts toward the mean."}
        </Text>
        <Text>
          <strong>{"4. Check the half-life"}</strong>
          {" to make sure the spread reverts fast enough to be tradeable. The "}
          <GlossaryLink term="Half-Life" />
          {" tells you how long you'll typically hold a position."}
        </Text>
        <Text>
          {"These four pieces \u2014 spread construction, normalization, signal generation, and speed validation \u2014 form the analytical core of every mean-reversion pairs trading strategy."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Coming up in Chapter 4:"}</strong>
        {" we put it all together and "}
        <em>{"backtest"}</em>
        {" the strategy on historical data. You'll see how parameter choices affect real profit and loss."}
      </Text>
    </Stack>
  );
}
