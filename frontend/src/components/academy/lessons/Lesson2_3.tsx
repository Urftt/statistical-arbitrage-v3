'use client';

import {
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 2.3 — The Engle-Granger Test
 *
 * Step-by-step walkthrough of the two-step cointegration test,
 * with visual examples at each step.
 */
export function Lesson2_3() {
  const n = 120;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  // Generate a cointegrated pair for the walkthrough
  const commonTrend: number[] = [100];
  for (let i = 1; i < n; i++) {
    commonTrend.push(commonTrend[i - 1] + Math.sin(i * 127.1 + 311.7) * 1.2);
  }

  const assetA = commonTrend.map(
    (v, i) => v + Math.sin(i * 0.3) * 2
  );
  // Asset B = 0.6 * A + 15 + noise
  const hedgeRatio = 0.6;
  const intercept = 15;
  const assetB = assetA.map(
    (a, i) => hedgeRatio * a + intercept + Math.sin(i * 0.4 + 1) * 1.5
  );

  // Regression line
  const predicted = assetA.map((a) => hedgeRatio * a + intercept);

  // Residuals (spread)
  const residuals = assetB.map((b, i) => b - predicted[i]);

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"The "}
          <GlossaryLink term="Engle-Granger Test" />
          {" is the most common way to test for cointegration. It has exactly two steps. Let's walk through each one with real numbers."}
        </Text>
      </Stack>

      {/* Step 1: Regression */}
      <Stack gap="sm">
        <Title order={4}>{"Step 1: Regress one asset on the other"}</Title>
        <Text>
          {"We run an "}
          <GlossaryLink term="OLS Regression" />
          {" of Asset B on Asset A. This finds the best-fit line: B = β × A + intercept. The slope β is the "}
          <GlossaryLink term="Hedge Ratio" />
          {" — it tells us how much of Asset A we need per unit of Asset B."}
        </Text>

        <PlotlyChart
          data={[
            {
              x: assetA,
              y: assetB,
              type: 'scatter',
              mode: 'markers',
              name: 'Price pairs',
              marker: { color: '#339AF0', size: 4, opacity: 0.6 },
            },
            {
              x: assetA,
              y: predicted,
              type: 'scatter',
              mode: 'lines',
              name: `Regression: B = ${hedgeRatio} × A + ${intercept}`,
              line: { color: '#FF6B6B', width: 2 },
            },
          ]}
          layout={{
            title: 'Step 1: OLS Regression (A vs B)',
            xaxis: { title: { text: 'Asset A Price' } },
            yaxis: { title: { text: 'Asset B Price' } },
            height: 350,
            showlegend: true,
            legend: { x: 0, y: 1.12, orientation: 'h' },
          }}
        />

        <Text size="sm" c="dimmed">
          {"Each dot is one time period. The red line is the OLS fit. In this example, β = "}
          {hedgeRatio}
          {" and the intercept = "}
          {intercept}
          {". The regression tells us Asset B tends to be about 0.6 × Asset A + 15."}
        </Text>
      </Stack>

      {/* Step 2: Residuals */}
      <Stack gap="sm">
        <Title order={4}>{"Step 2: Test the residuals for stationarity"}</Title>
        <Text>
          {"The residuals are what's left over after removing the linear relationship: residual = B − (β × A + intercept). These residuals "}
          <em>{"are"}</em>
          {" the "}
          <GlossaryLink term="Spread" />
          {". If they're "}
          <GlossaryLink term="Stationarity">{"stationary"}</GlossaryLink>
          {" (bounce around a constant mean), the assets are cointegrated."}
        </Text>

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: residuals,
              type: 'scatter',
              mode: 'lines',
              name: 'Residuals (spread)',
              line: { color: '#339AF0', width: 2 },
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
            title: 'Step 2: Residuals — Are They Stationary?',
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Residual (Spread)' } },
            height: 300,
            showlegend: false,
          }}
        />

        <Text>
          {"These residuals oscillate around zero with no trend — they look stationary. But we need a formal test to be sure. That's where the "}
          <GlossaryLink term="ADF Test" />
          {" comes in. We run it on these residuals, and if the p-value is below 0.05, we reject the null hypothesis of non-stationarity. Translation: the spread is stationary, the assets are cointegrated."}
        </Text>
      </Stack>

      {/* Putting it together */}
      <Stack gap="sm">
        <Title order={4}>{"The full picture"}</Title>
        <Text>
          <strong>{"Step 1"}</strong>
          {": Regress B on A → get the hedge ratio (β) and residuals."}
        </Text>
        <Text>
          <strong>{"Step 2"}</strong>
          {": Run the ADF test on the residuals → if p < 0.05, the pair is cointegrated."}
        </Text>
        <Text>
          {"That's really all there is to it. The regression gives you the hedge ratio (how to size your positions), and the ADF test tells you if the spread is mean-reverting (whether the trade works)."}
        </Text>
        <Text size="sm" c="dimmed">
          {"One important caveat: the Engle-Granger test is "}
          <em>{"order-sensitive"}</em>
          {". Regressing B on A can give a different result than regressing A on B. In practice, you test both directions and take the stronger result."}
        </Text>
      </Stack>

      <Text c="dimmed" size="sm">
        <strong>{"Up next:"}</strong>
        {" let's dig deeper into stationarity and the ADF test — the statistical foundation that makes all of this work."}
      </Text>
    </Stack>
  );
}
