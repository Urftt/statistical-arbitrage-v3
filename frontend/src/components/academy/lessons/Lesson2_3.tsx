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
 * Lesson 2.3 — The Engle-Granger Test
 *
 * Interactive hedge ratio slider: users drag β and watch the residuals
 * change in real-time. The "right" ratio produces flat residuals.
 */
export function Lesson2_3() {
  const trueHedgeRatio = 0.6;
  const trueIntercept = 15;

  // User-controlled hedge ratio
  const [userBeta, setUserBeta] = useState(0.3);

  const n = 120;
  const timestamps = useMemo(() => Array.from({ length: n }, (_, i) => i), []);

  // Generate a cointegrated pair
  const { assetA, assetB } = useMemo(() => {
    const commonTrend: number[] = [100];
    for (let i = 1; i < n; i++) {
      commonTrend.push(commonTrend[i - 1] + Math.sin(i * 127.1 + 311.7) * 1.2);
    }
    const a = commonTrend.map((v, i) => v + Math.sin(i * 0.3) * 2);
    const b = a.map((aVal, i) => trueHedgeRatio * aVal + trueIntercept + Math.sin(i * 0.4 + 1) * 1.5);
    return { assetA: a, assetB: b };
  }, []);

  // Compute residuals based on user's hedge ratio
  const { residuals, predicted, residualStd, isFlat } = useMemo(() => {
    // Simple intercept estimate for the user's beta
    const meanA = assetA.reduce((s, v) => s + v, 0) / assetA.length;
    const meanB = assetB.reduce((s, v) => s + v, 0) / assetB.length;
    const userIntercept = meanB - userBeta * meanA;

    const pred = assetA.map((a) => userBeta * a + userIntercept);
    const res = assetB.map((b, i) => b - pred[i]);

    const resMean = res.reduce((s, v) => s + v, 0) / res.length;
    const resStd = Math.sqrt(
      res.reduce((s, v) => s + (v - resMean) ** 2, 0) / res.length
    );

    // Is the spread "flat enough"? Check if std is low relative to price scale
    const flat = resStd < 3 && Math.abs(userBeta - trueHedgeRatio) < 0.15;

    return { residuals: res, predicted: pred, residualStd: resStd, isFlat: flat };
  }, [userBeta, assetA, assetB]);

  const betaLabel =
    Math.abs(userBeta - trueHedgeRatio) < 0.05
      ? 'Excellent — residuals are flat and stationary!'
      : Math.abs(userBeta - trueHedgeRatio) < 0.15
        ? 'Close — residuals are mostly bounded'
        : 'Off — residuals show a trend (not stationary)';

  return (
    <Stack gap="xl">
      <Stack gap="md">
        <Text>
          {"The "}
          <GlossaryLink term="Engle-Granger Test" />
          {" is the most common way to test for cointegration. It has exactly two steps. Let's walk through each one — and you'll do Step 1 yourself."}
        </Text>
      </Stack>

      {/* Step 1: Interactive Regression */}
      <Stack gap="sm">
        <Title order={4}>{"Step 1: Find the right hedge ratio"}</Title>
        <Text>
          {"We need to find the "}
          <GlossaryLink term="Hedge Ratio" />
          {" (β) that makes the spread as flat as possible. In practice, "}
          <GlossaryLink term="OLS Regression" />
          {" computes this automatically. But first, try finding it by hand — drag the slider until the residuals below look as flat as you can get them."}
        </Text>

        <Text size="sm" fw={600} c={isFlat ? 'teal.4' : 'yellow.4'}>
          {"β = "}{userBeta.toFixed(2)}{" — "}{betaLabel}
        </Text>

        <Slider
          value={userBeta}
          onChange={setUserBeta}
          min={0.1}
          max={1.2}
          step={0.01}
          marks={[
            { value: 0.1, label: '0.1' },
            { value: trueHedgeRatio, label: `OLS (${trueHedgeRatio})` },
            { value: 1.2, label: '1.2' },
          ]}
          label={(v) => `β = ${v.toFixed(2)}`}
          color={isFlat ? 'teal' : 'yellow'}
        />

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
              name: `Your fit: B = ${userBeta.toFixed(2)} × A + intercept`,
              line: { color: '#FF6B6B', width: 2 },
            },
          ]}
          layout={{
            title: 'Step 1: Your Regression Line (Drag β to Adjust)',
            xaxis: { title: { text: 'Asset A Price' } },
            yaxis: { title: { text: 'Asset B Price' } },
            height: 320,
            showlegend: true,
            legend: { x: 0, y: 1.12, orientation: 'h' },
          }}
        />

        <PlotlyChart
          data={[
            {
              x: timestamps,
              y: residuals,
              type: 'scatter',
              mode: 'lines',
              name: 'Residuals (spread)',
              line: {
                color: isFlat ? '#20C997' : '#FCC419',
                width: 2,
              },
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
            title: `Residuals (Spread) — Std Dev: ${residualStd.toFixed(2)}`,
            xaxis: { title: { text: 'Time' } },
            yaxis: { title: { text: 'Residual' } },
            height: 280,
            showlegend: false,
          }}
        />

        <Text size="sm" c="dimmed">
          {"When β is wrong, the residuals trend up or down — that's a non-stationary spread. When β is right (~"}
          {trueHedgeRatio}
          {"), the residuals oscillate around zero — stationary and tradeable. OLS finds this optimal β automatically."}
        </Text>
      </Stack>

      {/* Step 2 */}
      <Stack gap="sm">
        <Title order={4}>{"Step 2: Test the residuals for stationarity"}</Title>
        <Text>
          {"Once we have the residuals from the optimal β, we run the "}
          <GlossaryLink term="ADF Test" />
          {" on them. If the "}
          <GlossaryLink term="p-value" />
          {" is below 0.05, we reject the null hypothesis of non-stationarity. Translation: the spread is stationary, the assets are cointegrated."}
        </Text>
      </Stack>

      {/* Summary */}
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
