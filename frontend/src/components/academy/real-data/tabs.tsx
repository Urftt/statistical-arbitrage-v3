'use client';

/**
 * Modular real-data tab components for Academy lessons.
 *
 * Each tab is a focused visualization that can be composed per-lesson.
 * All tabs receive AcademyPairData and render their specific chart/stats.
 */

import { useMemo, useState } from 'react';
import { Badge, Group, Slider, Stack, Text } from '@mantine/core';
import PlotlyChart from '@/components/charts/PlotlyChart';
import type { AcademyPairData } from '@/contexts/AcademyDataContext';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function base(symbol: string): string {
  return symbol.split('/')[0] ?? symbol;
}

/** Align OHLCV close prices to cointegration timestamps */
function alignPrices(data: AcademyPairData) {
  const { coint, ohlcv1, ohlcv2 } = data;
  const lookup1 = new Map(ohlcv1.timestamps.map((t, i) => [t, ohlcv1.close[i]]));
  const lookup2 = new Map(ohlcv2.timestamps.map((t, i) => [t, ohlcv2.close[i]]));
  const dates: Date[] = [];
  const close1: number[] = [];
  const close2: number[] = [];
  for (let i = 0; i < coint.timestamps.length; i++) {
    const ts = coint.timestamps[i];
    const c1 = lookup1.get(ts);
    const c2 = lookup2.get(ts);
    if (c1 !== undefined && c2 !== undefined) {
      dates.push(new Date(ts));
      close1.push(c1);
      close2.push(c2);
    }
  }
  return { dates, close1, close2 };
}

function computeRollingMean(values: number[], window: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < window - 1) { result.push(null); continue; }
    const slice = values.slice(i - window + 1, i + 1);
    result.push(slice.reduce((a, b) => a + b, 0) / window);
  }
  return result;
}

function computeRollingZScore(spread: number[], window: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < spread.length; i++) {
    if (i < window - 1) { result.push(null); continue; }
    const slice = spread.slice(i - window + 1, i + 1);
    const mean = slice.reduce((a, b) => a + b, 0) / window;
    const std = Math.sqrt(slice.reduce((a, b) => a + (b - mean) ** 2, 0) / window);
    result.push(std > 0 ? (spread[i] - mean) / std : 0);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Tab: Raw Prices (dual y-axis)
// ---------------------------------------------------------------------------

export function TabRawPrices({ data }: { data: AcademyPairData }) {
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);
  const { dates, close1, close2 } = alignPrices(data);

  return (
    <PlotlyChart
      data={[
        { x: dates, y: close1, type: 'scatter', mode: 'lines', name: `${a1} (EUR)`, line: { color: '#339AF0', width: 2 }, yaxis: 'y' },
        { x: dates, y: close2, type: 'scatter', mode: 'lines', name: `${a2} (EUR)`, line: { color: '#51CF66', width: 2 }, yaxis: 'y2' },
      ]}
      layout={{
        title: `${a1} vs ${a2} — Actual EUR Prices`,
        xaxis: { title: { text: 'Date' } },
        yaxis: { title: { text: `${a1} (EUR)`, font: { color: '#339AF0' } }, tickfont: { color: '#339AF0' }, side: 'left' },
        yaxis2: { title: { text: `${a2} (EUR)`, font: { color: '#51CF66' } }, tickfont: { color: '#51CF66' }, overlaying: 'y', side: 'right' },
        height: 300,
        showlegend: true,
        legend: { x: 0, y: 1.12, orientation: 'h' },
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Tab: Normalized Prices (% change)
// ---------------------------------------------------------------------------

export function TabNormalizedPrices({ data }: { data: AcademyPairData }) {
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);
  const { dates, close1, close2 } = alignPrices(data);

  const norm = (prices: number[]) => {
    const b = prices[0] || 1;
    return prices.map((p) => ((p - b) / b) * 100);
  };

  return (
    <PlotlyChart
      data={[
        { x: dates, y: norm(close1), type: 'scatter', mode: 'lines', name: a1, line: { color: '#339AF0', width: 2 } },
        { x: dates, y: norm(close2), type: 'scatter', mode: 'lines', name: a2, line: { color: '#51CF66', width: 2 } },
      ]}
      layout={{
        title: `${a1} vs ${a2} — Normalized (% Change)`,
        xaxis: { title: { text: 'Date' } },
        yaxis: { title: { text: '% Change' } },
        height: 300,
        showlegend: true,
        legend: { x: 0, y: 1.12, orientation: 'h' },
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Tab: Scatter + OLS regression line
// ---------------------------------------------------------------------------

export function TabScatterOLS({ data }: { data: AcademyPairData }) {
  const { coint } = data;
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);
  const { close1, close2 } = alignPrices(data);

  // Backend: asset1 = β × asset2 + intercept → X = asset2, Y = asset1
  const minB = Math.min(...close2);
  const maxB = Math.max(...close2);
  const regX = [minB, maxB];
  const regY = regX.map((x) => coint.hedge_ratio * x + coint.intercept);

  return (
    <Stack gap="xs">
      <Group gap="lg" wrap="wrap">
        <Text size="sm"><Text component="span" c="dimmed">{"β: "}</Text><Text component="span" fw={700}>{coint.hedge_ratio.toFixed(4)}</Text></Text>
        <Text size="sm"><Text component="span" c="dimmed">{"Intercept: "}</Text><Text component="span" fw={700}>{coint.intercept.toFixed(4)}</Text></Text>
        <Text size="sm"><Text component="span" c="dimmed">{"r: "}</Text><Text component="span" fw={700}>{coint.correlation.toFixed(4)}</Text></Text>
      </Group>
      <PlotlyChart
        data={[
          { x: close2, y: close1, type: 'scatter', mode: 'markers', name: 'Price pairs', marker: { color: '#339AF0', size: 3, opacity: 0.4 } },
          { x: regX, y: regY, type: 'scatter', mode: 'lines', name: `OLS: ${a1} = ${coint.hedge_ratio.toFixed(3)} × ${a2} + ${coint.intercept.toFixed(2)}`, line: { color: '#FF6B6B', width: 2.5 } },
        ]}
        layout={{
          title: `Scatter: ${a1} vs ${a2} (OLS Regression)`,
          xaxis: { title: { text: `${a2} (EUR)` } },
          yaxis: { title: { text: `${a1} (EUR)` } },
          height: 300,
          showlegend: true,
          legend: { x: 0, y: 1.12, orientation: 'h' },
        }}
      />
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Tab: Spread (residuals) with mean + sigma bands
// ---------------------------------------------------------------------------

export function TabSpread({ data }: { data: AcademyPairData }) {
  const { coint } = data;
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);
  const spreadVals = coint.spread.filter((v): v is number => v !== null);
  const dates = coint.timestamps.map((t) => new Date(t));
  const spreadDates = dates.slice(dates.length - spreadVals.length);
  const mean = spreadVals.reduce((s, v) => s + v, 0) / spreadVals.length;
  const std = Math.sqrt(spreadVals.reduce((s, v) => s + (v - mean) ** 2, 0) / spreadVals.length);

  return (
    <Stack gap="xs">
      <Group gap="lg" wrap="wrap">
        <Text size="sm"><Text component="span" c="dimmed">{"Mean: "}</Text><Text component="span" fw={700}>{mean.toFixed(4)}</Text></Text>
        <Text size="sm"><Text component="span" c="dimmed">{"Std: "}</Text><Text component="span" fw={700}>{std.toFixed(4)}</Text></Text>
        <Text size="sm"><Text component="span" c="dimmed">{"Points: "}</Text><Text component="span" fw={700}>{spreadVals.length}</Text></Text>
      </Group>
      <PlotlyChart
        data={[
          { x: spreadDates, y: spreadVals, type: 'scatter', mode: 'lines', name: 'Spread', line: { color: '#CC5DE8', width: 2 } },
          { x: [spreadDates[0], spreadDates[spreadDates.length - 1]], y: [mean, mean], type: 'scatter', mode: 'lines', name: 'Mean', line: { color: '#909296', width: 1, dash: 'dash' } },
          { x: [spreadDates[0], spreadDates[spreadDates.length - 1]], y: [mean + std, mean + std], type: 'scatter', mode: 'lines', name: '+1σ', line: { color: '#FCC419', width: 1, dash: 'dot' } },
          { x: [spreadDates[0], spreadDates[spreadDates.length - 1]], y: [mean - std, mean - std], type: 'scatter', mode: 'lines', name: '-1σ', line: { color: '#FCC419', width: 1, dash: 'dot' } },
        ]}
        layout={{
          title: `Spread: ${a1} − β × ${a2} (β = ${coint.hedge_ratio.toFixed(2)})`,
          xaxis: { title: { text: 'Date' } },
          yaxis: { title: { text: 'Spread' } },
          height: 300,
          showlegend: false,
        }}
      />
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Tab: ADF Test results
// ---------------------------------------------------------------------------

export function TabADFTest({ data }: { data: AcademyPairData }) {
  const { coint } = data;
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);

  return (
    <Stack gap="xs">
      <Group gap="sm">
        <Text size="sm" fw={700}>{a1} / {a2}</Text>
        <Badge
          color={coint.is_cointegrated ? 'teal' : 'red'}
          variant="light"
          size="sm"
        >
          {coint.is_cointegrated ? 'Stationary (cointegrated)' : 'Non-stationary'}
        </Badge>
      </Group>
      <Group gap="lg" wrap="wrap">
        <Text size="sm"><Text component="span" c="dimmed">{"Test statistic: "}</Text><Text component="span" fw={700}>{coint.cointegration_score.toFixed(4)}</Text></Text>
        <Text size="sm">
          <Text component="span" c="dimmed">{"p-value: "}</Text>
          <Text component="span" fw={700} c={coint.p_value < 0.05 ? 'teal.4' : 'red.4'}>{coint.p_value.toFixed(4)}</Text>
        </Text>
        <Text size="sm">
          <Text component="span" c="dimmed">{"Critical (5%): "}</Text>
          <Text component="span" fw={700}>{coint.critical_values.five_pct.toFixed(2)}</Text>
        </Text>
      </Group>
      <Text size="sm" c={coint.is_cointegrated ? 'teal.4' : 'red.4'}>
        {coint.is_cointegrated
          ? "The spread is stationary — it mean-reverts. This pair passes the cointegration test."
          : `The spread may not be stationary (p = ${coint.p_value.toFixed(4)}). Not suitable for pairs trading.`}
      </Text>
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Tab: Z-Score (static, from coint response)
// ---------------------------------------------------------------------------

export function TabZScore({ data }: { data: AcademyPairData }) {
  const { coint } = data;
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);
  const zVals = coint.zscore.filter((v): v is number => v !== null);
  const dates = coint.timestamps.map((t) => new Date(t));
  const zDates = dates.slice(dates.length - zVals.length);

  return (
    <PlotlyChart
      data={[
        { x: zDates, y: zVals, type: 'scatter', mode: 'lines', name: 'Z-Score', line: { color: '#FF922B', width: 2 } },
        { x: [zDates[0], zDates[zDates.length - 1]], y: [2, 2], type: 'scatter', mode: 'lines', name: '+2σ', line: { color: '#FF6B6B', width: 1, dash: 'dot' } },
        { x: [zDates[0], zDates[zDates.length - 1]], y: [-2, -2], type: 'scatter', mode: 'lines', name: '-2σ', line: { color: '#51CF66', width: 1, dash: 'dot' } },
        { x: [zDates[0], zDates[zDates.length - 1]], y: [0, 0], type: 'scatter', mode: 'lines', line: { color: '#909296', width: 1, dash: 'dash' }, showlegend: false },
      ]}
      layout={{
        title: `Z-Score: ${a1} / ${a2}`,
        xaxis: { title: { text: 'Date' } },
        yaxis: { title: { text: 'Z-Score (σ)' } },
        height: 300,
        showlegend: true,
        legend: { x: 0, y: 1.12, orientation: 'h' },
      }}
    />
  );
}

// ---------------------------------------------------------------------------
// Tab: Z-Score with interactive rolling window slider
// ---------------------------------------------------------------------------

export function TabZScoreSlider({ data }: { data: AcademyPairData }) {
  const [window, setWindow] = useState(60);
  const { coint } = data;
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);

  const spreadVals = useMemo(() => coint.spread.filter((v): v is number => v !== null), [coint.spread]);
  const dates = useMemo(() => {
    const allDates = coint.timestamps.map((t) => new Date(t));
    return allDates.slice(allDates.length - spreadVals.length);
  }, [coint.timestamps, spreadVals.length]);

  const zScores = useMemo(() => computeRollingZScore(spreadVals, window), [spreadVals, window]);
  const zValid = zScores.filter((v): v is number => v !== null);
  const crossings = useMemo(() => {
    let count = 0;
    for (let i = 1; i < zValid.length; i++) {
      if ((zValid[i] > 2 && zValid[i - 1] <= 2) || (zValid[i] < -2 && zValid[i - 1] >= -2)) count++;
    }
    return count;
  }, [zValid]);

  return (
    <Stack gap="xs">
      <Text size="sm" fw={600}>Rolling window (bars)</Text>
      <Slider value={window} onChange={setWindow} min={20} max={120} step={5}
        marks={[{ value: 20, label: '20' }, { value: 60, label: '60' }, { value: 120, label: '120' }]}
        label={(v) => `${v} bars`} color="blue"
      />
      <PlotlyChart
        data={[
          { x: dates, y: spreadVals, type: 'scatter', mode: 'lines', name: 'Raw Spread', line: { color: '#CC5DE8', width: 1.5 } },
        ]}
        layout={{
          title: `Raw Spread: ${a1} / ${a2}`,
          xaxis: { title: { text: 'Date' } },
          yaxis: { title: { text: 'Spread' } },
          height: 220,
          showlegend: false,
        }}
      />
      <PlotlyChart
        data={[
          { x: dates, y: zScores, type: 'scatter', mode: 'lines', name: 'Z-Score', line: { color: '#FF922B', width: 2 }, connectgaps: false },
          { x: [dates[0], dates[dates.length - 1]], y: [2, 2], type: 'scatter', mode: 'lines', name: '+2σ', line: { color: '#FF6B6B', width: 1, dash: 'dot' } },
          { x: [dates[0], dates[dates.length - 1]], y: [-2, -2], type: 'scatter', mode: 'lines', name: '-2σ', line: { color: '#51CF66', width: 1, dash: 'dot' } },
        ]}
        layout={{
          title: `Z-Score (window = ${window})`,
          xaxis: { title: { text: 'Date' } },
          yaxis: { title: { text: 'Z-Score (σ)' } },
          height: 250,
          showlegend: true,
          legend: { x: 0, y: 1.12, orientation: 'h' },
        }}
      />
      <Text size="sm">{"±2σ crossings: "}<strong>{crossings}</strong>{" | Window: "}<strong>{window}{" bars"}</strong></Text>
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Tab: Signals with interactive entry/exit sliders
// ---------------------------------------------------------------------------

export function TabSignals({ data }: { data: AcademyPairData }) {
  const [entryThreshold, setEntryThreshold] = useState(2.0);
  const [exitThreshold, setExitThreshold] = useState(0.5);
  const { coint } = data;
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);

  const spreadVals = useMemo(() => coint.spread.filter((v): v is number => v !== null), [coint.spread]);
  const dates = useMemo(() => {
    const allDates = coint.timestamps.map((t) => new Date(t));
    return allDates.slice(allDates.length - spreadVals.length);
  }, [coint.timestamps, spreadVals.length]);
  const zScores = useMemo(() => computeRollingZScore(spreadVals, 60), [spreadVals]);

  // Find signal points
  const { shortX, shortY, longX, longY, exitX, exitY, tradeCount } = useMemo(() => {
    const sX: Date[] = [], sY: number[] = [];
    const lX: Date[] = [], lY: number[] = [];
    const eX: Date[] = [], eY: number[] = [];
    let trades = 0;
    let inPosition = false;

    for (let i = 0; i < zScores.length; i++) {
      const z = zScores[i];
      if (z === null) continue;
      if (!inPosition) {
        if (z > entryThreshold) { sX.push(dates[i]); sY.push(z); inPosition = true; trades++; }
        else if (z < -entryThreshold) { lX.push(dates[i]); lY.push(z); inPosition = true; trades++; }
      } else {
        if (Math.abs(z) < exitThreshold) { eX.push(dates[i]); eY.push(z); inPosition = false; }
      }
    }
    return { shortX: sX, shortY: sY, longX: lX, longY: lY, exitX: eX, exitY: eY, tradeCount: trades };
  }, [zScores, entryThreshold, exitThreshold, dates]);

  return (
    <Stack gap="xs">
      <Group gap="xl" grow>
        <Stack gap={4}>
          <Text size="xs" c="dimmed">Entry threshold (z-score)</Text>
          <Slider value={entryThreshold} onChange={setEntryThreshold} min={1.0} max={3.0} step={0.1}
            label={(v) => `±${v.toFixed(1)}σ`} color="blue" />
        </Stack>
        <Stack gap={4}>
          <Text size="xs" c="dimmed">Exit threshold (z-score)</Text>
          <Slider value={exitThreshold} onChange={setExitThreshold} min={0.0} max={1.5} step={0.1}
            label={(v) => `±${v.toFixed(1)}σ`} color="gray" />
        </Stack>
      </Group>
      <Text size="sm" c="blue.4" fw={600}>
        {"Trades: "}{tradeCount}{" | Short entries: "}{shortX.length}{" | Long entries: "}{longX.length}{" | Closes: "}{exitX.length}
      </Text>
      <PlotlyChart
        data={[
          { x: dates, y: zScores, type: 'scatter', mode: 'lines', name: 'Z-Score', line: { color: '#FF922B', width: 2 }, connectgaps: false },
          { x: shortX, y: shortY, type: 'scatter', mode: 'markers', name: 'Short entry', marker: { color: '#FF6B6B', size: 8, symbol: 'triangle-down' } },
          { x: longX, y: longY, type: 'scatter', mode: 'markers', name: 'Long entry', marker: { color: '#51CF66', size: 8, symbol: 'triangle-up' } },
          { x: exitX, y: exitY, type: 'scatter', mode: 'markers', name: 'Exit', marker: { color: '#909296', size: 6, symbol: 'circle' } },
          { x: [dates[0], dates[dates.length - 1]], y: [entryThreshold, entryThreshold], type: 'scatter', mode: 'lines', name: `+${entryThreshold.toFixed(1)}σ entry`, line: { color: '#FF6B6B', width: 1, dash: 'dot' }, showlegend: false },
          { x: [dates[0], dates[dates.length - 1]], y: [-entryThreshold, -entryThreshold], type: 'scatter', mode: 'lines', name: `-${entryThreshold.toFixed(1)}σ entry`, line: { color: '#51CF66', width: 1, dash: 'dot' }, showlegend: false },
          { x: [dates[0], dates[dates.length - 1]], y: [exitThreshold, exitThreshold], type: 'scatter', mode: 'lines', name: `+${exitThreshold.toFixed(1)}σ exit`, line: { color: '#909296', width: 1, dash: 'dash' }, showlegend: false },
          { x: [dates[0], dates[dates.length - 1]], y: [-exitThreshold, -exitThreshold], type: 'scatter', mode: 'lines', name: `-${exitThreshold.toFixed(1)}σ exit`, line: { color: '#909296', width: 1, dash: 'dash' }, showlegend: false },
          { x: [dates[0], dates[dates.length - 1]], y: [0, 0], type: 'scatter', mode: 'lines', line: { color: '#909296', width: 0.5, dash: 'dot' }, showlegend: false },
        ]}
        layout={{
          title: `Signals: ${a1} / ${a2} (entry ±${entryThreshold.toFixed(1)}σ, exit ±${exitThreshold.toFixed(1)}σ)`,
          xaxis: { title: { text: 'Date' } },
          yaxis: { title: { text: 'Z-Score (σ)' } },
          height: 300,
          showlegend: true,
          legend: { x: 0, y: 1.12, orientation: 'h' },
        }}
      />
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Tab: Half-Life / Autocorrelation decay
// ---------------------------------------------------------------------------

function computeAutoCorrelation(spread: number[], maxLag: number): number[] {
  const mean = spread.reduce((s, v) => s + v, 0) / spread.length;
  const centered = spread.map((v) => v - mean);
  const variance = centered.reduce((s, v) => s + v * v, 0) / centered.length;
  if (variance === 0) return Array(maxLag + 1).fill(0);
  const acf: number[] = [1];
  for (let lag = 1; lag <= maxLag; lag++) {
    let sum = 0;
    for (let i = lag; i < centered.length; i++) sum += centered[i] * centered[i - lag];
    acf.push(sum / (centered.length * variance));
  }
  return acf;
}

export function TabHalfLife({ data }: { data: AcademyPairData }) {
  const { coint } = data;
  const a1 = base(data.pair.asset1);
  const a2 = base(data.pair.asset2);
  const spreadVals = coint.spread.filter((v): v is number => v !== null);

  const maxLag = 50;
  const acf = useMemo(() => computeAutoCorrelation(spreadVals, maxLag), [spreadVals]);
  const lags = Array.from({ length: maxLag + 1 }, (_, i) => i);
  const empiricalHL = acf.findIndex((v, i) => i > 0 && v < 0.5);

  // Client-side AR(1) half-life
  const { phi, halfLife } = useMemo(() => {
    if (spreadVals.length < 20) return { phi: 1, halfLife: null as number | null };
    const mean = spreadVals.reduce((s, v) => s + v, 0) / spreadVals.length;
    const centered = spreadVals.map((v) => v - mean);
    let sumXY = 0, sumXX = 0;
    for (let i = 1; i < centered.length; i++) {
      sumXY += centered[i - 1] * centered[i];
      sumXX += centered[i - 1] * centered[i - 1];
    }
    const p = sumXX > 0 ? sumXY / sumXX : 1;
    if (p <= 0 || p >= 1) return { phi: p, halfLife: null };
    return { phi: p, halfLife: -Math.log(2) / Math.log(p) };
  }, [spreadVals]);

  const color = coint.is_cointegrated ? '#20C997' : '#FF6B6B';

  return (
    <Stack gap="xs">
      <Group gap="sm">
        <Badge color={coint.is_cointegrated ? 'teal' : 'red'} variant="light" size="sm">
          {coint.is_cointegrated ? 'Cointegrated' : 'Not cointegrated'}
        </Badge>
        {halfLife !== null && halfLife > 0 && (
          <Badge color={halfLife < 35 ? 'teal' : halfLife < 60 ? 'yellow' : 'orange'} variant="light" size="sm">
            {"Half-life: "}{halfLife.toFixed(0)}{" bars"}
          </Badge>
        )}
      </Group>
      <PlotlyChart
        data={[
          { x: lags, y: acf, type: 'bar', name: 'ACF', marker: { color: acf.map((v) => v > 0.5 ? color : v > 0 ? '#FCC419' : '#909296') } },
          { x: [0, maxLag], y: [0.5, 0.5], type: 'scatter', mode: 'lines', name: '50% line', line: { color: '#909296', width: 1, dash: 'dash' } },
        ]}
        layout={{
          title: `Autocorrelation Decay: ${a1} / ${a2}${empiricalHL > 0 ? ` — below 50% at lag ${empiricalHL}` : ''}`,
          xaxis: { title: { text: 'Lag (bars)' } },
          yaxis: { title: { text: 'Autocorrelation' }, range: [-0.3, 1.1] },
          height: 250,
          showlegend: false,
        }}
      />
      <Group gap="lg" wrap="wrap">
        <Text size="sm"><Text component="span" c="dimmed">{"φ: "}</Text><Text component="span" fw={700}>{phi.toFixed(4)}</Text></Text>
        {halfLife !== null && halfLife > 0 && (
          <Text size="sm"><Text component="span" c="dimmed">{"Half-life: "}</Text><Text component="span" fw={700}>{halfLife.toFixed(1)}{" bars"}</Text></Text>
        )}
        {empiricalHL > 0 && (
          <Text size="sm"><Text component="span" c="dimmed">{"ACF < 50%: "}</Text><Text component="span" fw={700}>{"lag "}{empiricalHL}</Text></Text>
        )}
      </Group>
    </Stack>
  );
}
