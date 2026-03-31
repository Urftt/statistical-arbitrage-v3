'use client';

import { useState } from 'react';
import {
  SegmentedControl,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { RealDataSection, TabSpread, TabADFTest } from '@/components/academy/real-data';

/**
 * Lesson 2.4 — Stationarity & The ADF Test
 *
 * Builds intuition for what stationarity means visually, then explains
 * the ADF test in plain language. Interactive: stationary vs non-stationary
 * series comparison.
 */
export function Lesson2_4() {
  const [series, setSeries] = useState<string>('stationary');

  const n = 200;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  // Stationary series: OU process (spread-like)
  const stationary: number[] = [0];
  for (let i = 1; i < n; i++) {
    const noise = Math.sin(i * 127.1 + 311.7) * 0.8 + Math.cos(i * 269.5) * 0.4;
    stationary.push(stationary[i - 1] * 0.9 + noise);
  }

  // Non-stationary: random walk (price-like)
  const nonStationary: number[] = [100];
  for (let i = 1; i < n; i++) {
    const noise = Math.sin(i * 127.1 + 311.7) * 1.2 + Math.cos(i * 269.5) * 0.6;
    nonStationary.push(nonStationary[i - 1] + noise * 0.5);
  }

  const active = series === 'stationary' ? stationary : nonStationary;

  // Compute rolling mean and std for visual
  const window = 30;
  const rollingMean: (number | null)[] = [];
  const rollingUpper: (number | null)[] = [];
  const rollingLower: (number | null)[] = [];
  for (let i = 0; i < n; i++) {
    if (i < window) {
      rollingMean.push(null);
      rollingUpper.push(null);
      rollingLower.push(null);
      continue;
    }
    const slice = active.slice(i - window, i);
    const mean = slice.reduce((a, b) => a + b, 0) / window;
    const std = Math.sqrt(
      slice.reduce((a, b) => a + (b - mean) ** 2, 0) / window
    );
    rollingMean.push(mean);
    rollingUpper.push(mean + 2 * std);
    rollingLower.push(mean - 2 * std);
  }

  return (
    <Stack gap="xl">
      <Text>
        {"Toggle between stationary and non-stationary series — watch how the rolling mean and bands behave."}
      </Text>

      {/* Interactive toggle and chart first */}
      <Stack gap="sm">
        <SegmentedControl
          value={series}
          onChange={setSeries}
          data={[
            { label: 'Stationary (Spread)', value: 'stationary' },
            { label: 'Non-Stationary (Price)', value: 'nonstationary' },
          ]}
          fullWidth
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: active,
              type: 'scatter',
              mode: 'lines',
              name: series === 'stationary' ? 'Spread' : 'Price',
              line: { color: '#339AF0', width: 1.5 },
            },
            {
              x: timestamps,
              y: rollingMean,
              type: 'scatter',
              mode: 'lines',
              name: 'Rolling mean',
              line: { color: '#FF922B', width: 2 },
              connectgaps: false,
            },
            {
              x: timestamps,
              y: rollingUpper,
              type: 'scatter',
              mode: 'lines',
              name: '+2σ band',
              line: { color: '#FF922B', width: 1, dash: 'dot' },
              connectgaps: false,
            },
            {
              x: timestamps,
              y: rollingLower,
              type: 'scatter',
              mode: 'lines',
              name: '-2σ band',
              line: { color: '#FF922B', width: 1, dash: 'dot' },
              connectgaps: false,
            },
          ]}
          layout={{
            title: series === 'stationary'
              ? 'Stationary: Mean and Variance Stay Constant'
              : 'Non-Stationary: Mean Drifts Over Time',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Value' } },
            height: 400,
            showlegend: true,
            legend: { x: 0, y: -0.15, orientation: 'h' },
          }}
        />

        <Text size="sm">
          {series === 'stationary'
            ? "The orange rolling mean stays roughly flat. The bands stay roughly the same width. This series is stationary — its statistical properties are constant."
            : "The rolling mean drifts around. The bands shift. At time 50 the mean is different from time 150. This series is non-stationary — you can't predict a \"normal\" level to revert to."}
        </Text>
      </Stack>

      <RealDataSection intro="Run the ADF stationarity test on real crypto spreads.">
        {(data) => (
          <Stack gap="md">
            <TabSpread data={data} />
            <TabADFTest data={data} />
          </Stack>
        )}
      </RealDataSection>

      {/* Explanation BELOW the chart */}
      <Stack gap="md">
        <Text>
          <GlossaryLink term="Stationarity" />
          {" is the foundation of everything we've learned so far. A stationary series has a constant mean and variance over time — it doesn't trend or drift. The spread between cointegrated assets "}
          <em>{"should"}</em>
          {" be stationary."}
        </Text>
        <Text>
          {"An intuitive way to think about it: if you pick any window of time and calculate the average and standard deviation, you should get roughly the same numbers regardless of "}
          <em>{"when"}</em>
          {" you pick. That's stationarity."}
        </Text>
      </Stack>

      {/* ADF test explanation */}
      <Stack gap="sm">
        <Title order={4}>{"The ADF test in plain language"}</Title>
        <Text>
          {"The "}
          <GlossaryLink term="ADF Test" />
          {" (Augmented Dickey-Fuller) is the standard statistical test for stationarity. Here's what it does:"}
        </Text>
        <Text>
          <strong>{"Null hypothesis:"}</strong>
          {" the series has a \"unit root\" — it's non-stationary (like a random walk)."}
        </Text>
        <Text>
          <strong>{"Alternative hypothesis:"}</strong>
          {" the series is stationary."}
        </Text>
        <Text>
          {"The test produces a test statistic and a "}
          <GlossaryLink term="p-value" />
          {". If the p-value is below 0.05, we reject the null — there's strong evidence the series IS stationary. The more negative the test statistic, the stronger the evidence."}
        </Text>
        <Text>
          {"In the Engle-Granger procedure, we run the ADF test on the regression residuals. If p < 0.05: the spread is stationary → the pair is cointegrated → we can trade it."}
        </Text>
      </Stack>

      {/* Chapter wrap-up */}
      <Stack gap="sm" mt="md">
        <Title order={4}>{"Chapter 2 wrap-up"}</Title>
        <Text>
          {"You now understand the statistical foundation:"}
        </Text>
        <Text>
          <strong>{"1."}</strong>
          {" Correlation measures direction — not enough for pairs trading."}
        </Text>
        <Text>
          <strong>{"2."}</strong>
          {" Cointegration measures whether the gap (spread) is bounded and mean-reverting."}
        </Text>
        <Text>
          <strong>{"3."}</strong>
          {" The Engle-Granger test: regress → get residuals → ADF test on residuals."}
        </Text>
        <Text>
          <strong>{"4."}</strong>
          {" Stationarity means constant mean and variance — testable with ADF (p < 0.05)."}
        </Text>
        <Text c="dimmed" size="sm" mt="xs">
          {"Next chapter: we'll build the actual spread and z-score signals you'll use for trading."}
        </Text>
      </Stack>
    </Stack>
  );
}
