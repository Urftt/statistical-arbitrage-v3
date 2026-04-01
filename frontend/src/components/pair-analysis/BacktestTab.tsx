'use client';

import { useState, useEffect, useRef } from 'react';
import {
  Stack,
  Group,
  Text,
  Paper,
  SimpleGrid,
  Badge,
  Button,
  Slider,
  Alert,
  Accordion,
  Table,
  Skeleton,
  Tooltip,
  Loader,
  List,
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconRefresh,
  IconAlertTriangle,
} from '@tabler/icons-react';
import PlotlyChart from '@/components/charts/PlotlyChart';
import {
  postBacktest,
  postCointegration,
  DEFAULT_STRATEGY_PARAMETERS,
  type BacktestResponse,
  type CointegrationResponse,
  type StrategyParametersPayload,
  type EquityCurvePointPayload,
  type SignalOverlayPointPayload,
} from '@/lib/api';
import { usePairContext } from '@/contexts/PairContext';

// ---------------------------------------------------------------------------
// Badge helpers
// ---------------------------------------------------------------------------

function sharpeBadge(v: number | null): { color: string; label: string } {
  if (v === null) return { color: 'gray', label: 'N/A' };
  if (v >= 1.5) return { color: 'green', label: 'Good' };
  if (v >= 0.5) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Poor' };
}

function drawdownBadge(v: number): { color: string; label: string } {
  if (v < 10) return { color: 'green', label: 'Low' };
  if (v <= 25) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'High' };
}

function winRateBadge(v: number): { color: string; label: string } {
  if (v > 0.55) return { color: 'green', label: 'Good' };
  if (v >= 0.40) return { color: 'yellow', label: 'Moderate' };
  return { color: 'red', label: 'Poor' };
}

function pnlBadge(v: number): { color: string; label: string } {
  if (v > 0) return { color: 'green', label: 'Profit' };
  return { color: 'red', label: 'Loss' };
}

function tradeCountBadge(v: number): { color: string; label: string } {
  if (v >= 10) return { color: 'green', label: 'Sufficient' };
  if (v >= 3) return { color: 'yellow', label: 'Limited' };
  return { color: 'red', label: 'Too Few' };
}

function equityBadge(v: number, initial: number): { color: string; label: string } {
  if (v > initial) return { color: 'green', label: 'Growth' };
  return { color: 'red', label: 'Decline' };
}

// ---------------------------------------------------------------------------
// Chart helpers
// ---------------------------------------------------------------------------

const MARKER_MAP: Record<string, { symbol: string; color: string; name: string }> = {
  long_entry:  { symbol: 'triangle-up',   color: '#51CF66', name: 'Long Entry' },
  short_entry: { symbol: 'triangle-up',   color: '#FF6B6B', name: 'Short Entry' },
  long_exit:   { symbol: 'triangle-down', color: '#51CF66', name: 'Long Exit' },
  short_exit:  { symbol: 'triangle-down', color: '#FF6B6B', name: 'Short Exit' },
  stop_loss:   { symbol: 'x',             color: '#FF922B', name: 'Stop Loss' },
};

function computeDrawdown(equityCurve: EquityCurvePointPayload[]): number[] {
  let runningMax = equityCurve[0]?.equity ?? 0;
  return equityCurve.map((point) => {
    if (point.equity > runningMax) runningMax = point.equity;
    return runningMax > 0 ? ((point.equity - runningMax) / runningMax) * 100 : 0;
  });
}

function buildZScoreShapes(entry: number, exit: number) {
  return [
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: entry, y1: entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: -entry, y1: -entry, line: { color: '#FF6B6B', width: 1, dash: 'dash' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: exit, y1: exit, line: { color: '#FCC419', width: 1, dash: 'dot' as const } },
    { type: 'line' as const, x0: 0, x1: 1, xref: 'paper' as const, y0: -exit, y1: -exit, line: { color: '#FCC419', width: 1, dash: 'dot' as const } },
  ];
}

function buildPositionShapes(equityCurve: EquityCurvePointPayload[]) {
  const shapes: Array<{
    type: 'rect';
    xref: 'x';
    yref: 'paper';
    x0: string;
    x1: string;
    y0: number;
    y1: number;
    fillcolor: string;
    line: { width: number };
    layer: 'below';
  }> = [];

  if (equityCurve.length === 0) return shapes;

  let segStart = 0;
  let segPos = equityCurve[0].position;

  for (let i = 1; i <= equityCurve.length; i++) {
    const curPos = i < equityCurve.length ? equityCurve[i].position : 'flat';
    if (curPos !== segPos || i === equityCurve.length) {
      if (segPos !== 'flat') {
        shapes.push({
          type: 'rect',
          xref: 'x',
          yref: 'paper',
          x0: equityCurve[segStart].timestamp,
          x1: equityCurve[i - 1].timestamp,
          y0: 0,
          y1: 1,
          fillcolor:
            segPos === 'long_spread'
              ? 'rgba(81, 207, 102, 0.08)'
              : 'rgba(255, 107, 107, 0.08)',
          line: { width: 0 },
          layer: 'below',
        });
      }
      segStart = i;
      segPos = curPos;
    }
  }

  return shapes;
}

/** Build marker traces for signal overlays on z-score or spread charts. */
function buildZScoreMarkerTraces(signals: SignalOverlayPointPayload[]) {
  const traces: Array<{
    type: 'scatter';
    mode: 'markers';
    x: number[];
    y: number[];
    marker: { symbol: string; color: string; size: number };
    name: string;
    showlegend: boolean;
  }> = [];

  for (const signalType of Object.keys(MARKER_MAP)) {
    const matching = signals.filter((s) => s.signal_type === signalType);
    if (matching.length === 0) continue;
    const m = MARKER_MAP[signalType];
    traces.push({
      type: 'scatter' as const,
      mode: 'markers' as const,
      x: matching.map((s) => new Date(s.execution_timestamp).getTime()),
      y: matching.map((s) => s.zscore_at_signal),
      marker: { symbol: m.symbol, color: m.color, size: 10 },
      name: m.name,
      showlegend: true,
    });
  }

  return traces;
}

/** Build marker traces for spread chart -- look up y from spread array by timestamp. */
function buildSpreadMarkerTraces(
  signals: SignalOverlayPointPayload[],
  timestamps: number[],
  spread: (number | null)[],
) {
  const traces: Array<{
    type: 'scatter';
    mode: 'markers';
    x: number[];
    y: number[];
    marker: { symbol: string; color: string; size: number };
    name: string;
    showlegend: boolean;
  }> = [];

  for (const signalType of Object.keys(MARKER_MAP)) {
    const matching = signals.filter((s) => s.signal_type === signalType);
    if (matching.length === 0) continue;

    const xs: number[] = [];
    const ys: number[] = [];

    for (const s of matching) {
      const execMs = new Date(s.execution_timestamp).getTime();
      // Find closest timestamp index
      let bestIdx = 0;
      let bestDist = Math.abs(timestamps[0] - execMs);
      for (let j = 1; j < timestamps.length; j++) {
        const dist = Math.abs(timestamps[j] - execMs);
        if (dist < bestDist) {
          bestDist = dist;
          bestIdx = j;
        }
      }
      const yVal = spread[bestIdx];
      if (yVal !== null) {
        xs.push(execMs);
        ys.push(yVal);
      }
    }

    if (xs.length === 0) continue;
    const m = MARKER_MAP[signalType];
    traces.push({
      type: 'scatter' as const,
      mode: 'markers' as const,
      x: xs,
      y: ys,
      marker: { symbol: m.symbol, color: m.color, size: 10 },
      name: m.name,
      showlegend: true,
    });
  }

  return traces;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function BacktestTab() {
  const { asset1, asset2, timeframe } = usePairContext();

  const [params, setParams] = useState<StrategyParametersPayload>({
    ...DEFAULT_STRATEGY_PARAMETERS,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<BacktestResponse | null>(null);
  const [cointData, setCointData] = useState<CointegrationResponse | null>(null);
  const cancelRef = useRef<boolean>(false);

  // Pair-change clear (D-05, NAV-05)
  useEffect(() => {
    cancelRef.current = true;
    setData(null);
    setCointData(null);
    setError(null);
    setParams({ ...DEFAULT_STRATEGY_PARAMETERS });
  }, [asset1, asset2, timeframe]);

  // Click-triggered fetch (D-05)
  async function handleRun() {
    cancelRef.current = false;
    setLoading(true);
    setError(null);

    const btReq = {
      asset1: `${asset1}/EUR`,
      asset2: `${asset2}/EUR`,
      timeframe,
      days_back: 365,
      strategy: { ...params, min_trade_count_warning: 3 },
    };
    const cointReq = {
      asset1: `${asset1}/EUR`,
      asset2: `${asset2}/EUR`,
      timeframe,
      days_back: 365,
    };

    try {
      const [btRes, cointRes] = await Promise.all([
        postBacktest(btReq),
        postCointegration(cointReq),
      ]);
      if (!cancelRef.current) {
        setData(btRes);
        setCointData(cointRes);
      }
    } catch (err: unknown) {
      if (!cancelRef.current) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    } finally {
      if (!cancelRef.current) {
        setLoading(false);
      }
    }
  }

  // Reset all state (D-04)
  function handleReset() {
    setParams({ ...DEFAULT_STRATEGY_PARAMETERS });
    setData(null);
    setCointData(null);
    setError(null);
  }

  // Helper to update a single param
  function updateParam(key: keyof StrategyParametersPayload, value: number) {
    setParams((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <Stack gap="lg">
      {/* ---- Parameter Form ---- */}
      <Paper p="md" withBorder>
        <Stack gap="lg">
          {/* Signal section */}
          <Stack gap="md">
            <Text size="sm" fw={600}>
              Signal
            </Text>
            <div>
              <Group justify="space-between" mb={4}>
                <Text size="sm">Lookback Window</Text>
                <Text size="xs" c="dimmed">
                  {params.lookback_window} bars
                </Text>
              </Group>
              <Slider
                min={20}
                max={365}
                step={5}
                value={params.lookback_window}
                onChange={(v) => updateParam('lookback_window', v)}
              />
            </div>
            <div>
              <Group justify="space-between" mb={4}>
                <Text size="sm">Entry Threshold</Text>
                <Text size="xs" c="dimmed">
                  {params.entry_threshold.toFixed(1)}&sigma;
                </Text>
              </Group>
              <Slider
                min={1.0}
                max={4.0}
                step={0.1}
                value={params.entry_threshold}
                onChange={(v) => updateParam('entry_threshold', v)}
              />
            </div>
            <div>
              <Group justify="space-between" mb={4}>
                <Text size="sm">Exit Threshold</Text>
                <Text size="xs" c="dimmed">
                  {params.exit_threshold.toFixed(1)}&sigma;
                </Text>
              </Group>
              <Slider
                min={0.0}
                max={2.0}
                step={0.1}
                value={params.exit_threshold}
                onChange={(v) => updateParam('exit_threshold', v)}
              />
            </div>
          </Stack>

          {/* Risk Management section */}
          <Stack gap="md">
            <Text size="sm" fw={600}>
              Risk Management
            </Text>
            <div>
              <Group justify="space-between" mb={4}>
                <Text size="sm">Stop-Loss</Text>
                <Text size="xs" c="dimmed">
                  {params.stop_loss.toFixed(1)}&sigma;
                </Text>
              </Group>
              <Slider
                min={1.0}
                max={6.0}
                step={0.1}
                value={params.stop_loss}
                onChange={(v) => updateParam('stop_loss', v)}
              />
            </div>
            <div>
              <Group justify="space-between" mb={4}>
                <Text size="sm">Position Size</Text>
                <Text size="xs" c="dimmed">
                  {(params.position_size * 100).toFixed(0)}%
                </Text>
              </Group>
              <Slider
                min={0.1}
                max={1.0}
                step={0.05}
                value={params.position_size}
                onChange={(v) => updateParam('position_size', v)}
              />
            </div>
          </Stack>

          {/* Execution section */}
          <Stack gap="md">
            <Text size="sm" fw={600}>
              Execution
            </Text>
            <div>
              <Group justify="space-between" mb={4}>
                <Text size="sm">Initial Capital</Text>
                <Text size="xs" c="dimmed">
                  &euro;{params.initial_capital.toLocaleString()}
                </Text>
              </Group>
              <Slider
                min={1000}
                max={100000}
                step={1000}
                value={params.initial_capital}
                onChange={(v) => updateParam('initial_capital', v)}
              />
            </div>
            <div>
              <Group justify="space-between" mb={4}>
                <Text size="sm">Transaction Fee</Text>
                <Text size="xs" c="dimmed">
                  {(params.transaction_fee * 100).toFixed(2)}%
                </Text>
              </Group>
              <Slider
                min={0}
                max={0.01}
                step={0.0005}
                value={params.transaction_fee}
                onChange={(v) => updateParam('transaction_fee', v)}
              />
            </div>
          </Stack>
        </Stack>

        {/* Button row */}
        <Group mt="md">
          <Button
            variant="filled"
            color="blue"
            onClick={handleRun}
            disabled={loading}
            leftSection={
              loading ? <Loader size="xs" /> : <IconPlayerPlay size={16} />
            }
          >
            Run Backtest
          </Button>
          <Button
            variant="default"
            onClick={handleReset}
            leftSection={<IconRefresh size={16} />}
          >
            Reset to Defaults
          </Button>
        </Group>
      </Paper>

      {/* ---- Error state ---- */}
      {error && (
        <Alert color="red" icon={<IconAlertTriangle size={16} />}>
          Backtest failed &mdash; {error}. Check that both assets have cached
          data and try again.
        </Alert>
      )}

      {/* ---- Loading state ---- */}
      {loading && (
        <Stack gap="md">
          <Skeleton height={28} />
          <SimpleGrid cols={{ base: 2, sm: 3, lg: 6 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} height={88} />
            ))}
          </SimpleGrid>
          <Skeleton height={280} />
          <Skeleton height={180} />
          <Skeleton height={300} />
          <Skeleton height={260} />
          <Skeleton height={200} />
          <Text size="sm" c="dimmed" ta="center">
            Running backtest...
          </Text>
        </Stack>
      )}

      {/* ---- Empty state ---- */}
      {!data && !loading && !error && (
        <Paper p="xl" ta="center">
          <Text size="lg" fw={600}>
            Configure and run a backtest
          </Text>
          <Text size="sm" c="dimmed">
            Set your strategy parameters above and click Run Backtest to see
            equity curve, metrics, and trade log.
          </Text>
        </Paper>
      )}

      {/* ---- Results ---- */}
      {data && !loading && (
        <Stack gap="md">
          {/* 1. Preflight blocker check */}
          {data.status === 'blocked' && (
            <Stack gap="sm">
              {data.data_quality.blockers.map((blocker, i) => (
                <Alert
                  key={i}
                  color="red"
                  icon={<IconAlertTriangle size={16} />}
                  title="Blocked"
                >
                  {blocker.message}
                </Alert>
              ))}
            </Stack>
          )}

          {/* Only show results if not blocked */}
          {data.status !== 'blocked' && (
            <>
              {/* 2. Preflight warnings */}
              {data.data_quality.warnings.length > 0 &&
                data.data_quality.warnings.map((warning, i) => (
                  <Alert
                    key={i}
                    color="yellow"
                    icon={<IconAlertTriangle size={16} />}
                  >
                    {warning.message}
                  </Alert>
                ))}

              {/* 3. Context label */}
              <Text size="xs" c="dimmed">
                Generated for {asset1}/{asset2}
              </Text>

              {/* 4. Metric cards */}
              <SimpleGrid cols={{ base: 2, sm: 3, lg: 6 }} spacing="md">
                {/* Sharpe Ratio */}
                <Tooltip
                  label={`Sortino: ${data.metrics.sortino_ratio?.toFixed(2) ?? 'N/A'}`}
                >
                  <Paper p="md">
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">
                        Sharpe Ratio
                      </Text>
                      <Text size="xl" fw={600}>
                        {data.metrics.sharpe_ratio?.toFixed(2) ?? 'N/A'}
                      </Text>
                      <Badge
                        size="sm"
                        variant="light"
                        color={sharpeBadge(data.metrics.sharpe_ratio).color}
                      >
                        {sharpeBadge(data.metrics.sharpe_ratio).label}
                      </Badge>
                    </Stack>
                  </Paper>
                </Tooltip>

                {/* Max Drawdown */}
                <Paper p="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Max Drawdown
                    </Text>
                    <Text size="xl" fw={600}>
                      {data.metrics.max_drawdown_pct.toFixed(1)}%
                    </Text>
                    <Badge
                      size="sm"
                      variant="light"
                      color={drawdownBadge(data.metrics.max_drawdown_pct).color}
                    >
                      {drawdownBadge(data.metrics.max_drawdown_pct).label}
                    </Badge>
                  </Stack>
                </Paper>

                {/* Win Rate */}
                <Tooltip
                  label={`Profit Factor: ${data.metrics.profit_factor?.toFixed(2) ?? 'N/A'}`}
                >
                  <Paper p="md">
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">
                        Win Rate
                      </Text>
                      <Text size="xl" fw={600}>
                        {(data.metrics.win_rate * 100).toFixed(1)}%
                      </Text>
                      <Badge
                        size="sm"
                        variant="light"
                        color={winRateBadge(data.metrics.win_rate).color}
                      >
                        {winRateBadge(data.metrics.win_rate).label}
                      </Badge>
                    </Stack>
                  </Paper>
                </Tooltip>

                {/* Total P&L */}
                <Paper p="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Total P&L
                    </Text>
                    <Text size="xl" fw={600}>
                      &euro;{data.metrics.total_net_pnl.toFixed(2)}
                    </Text>
                    <Badge
                      size="sm"
                      variant="light"
                      color={pnlBadge(data.metrics.total_net_pnl).color}
                    >
                      {pnlBadge(data.metrics.total_net_pnl).label}
                    </Badge>
                  </Stack>
                </Paper>

                {/* Total Trades */}
                <Tooltip
                  label={`Avg Return: ${data.metrics.average_trade_return_pct.toFixed(2)}% | Avg Holding: ${data.metrics.average_holding_period_bars} bars`}
                >
                  <Paper p="md">
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">
                        Total Trades
                      </Text>
                      <Text size="xl" fw={600}>
                        {data.metrics.total_trades}
                      </Text>
                      <Badge
                        size="sm"
                        variant="light"
                        color={tradeCountBadge(data.metrics.total_trades).color}
                      >
                        {tradeCountBadge(data.metrics.total_trades).label}
                      </Badge>
                    </Stack>
                  </Paper>
                </Tooltip>

                {/* Final Equity */}
                <Paper p="md">
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Final Equity
                    </Text>
                    <Text size="xl" fw={600}>
                      &euro;{data.metrics.final_equity.toFixed(2)}
                    </Text>
                    <Badge
                      size="sm"
                      variant="light"
                      color={
                        equityBadge(data.metrics.final_equity, params.initial_capital)
                          .color
                      }
                    >
                      {
                        equityBadge(data.metrics.final_equity, params.initial_capital)
                          .label
                      }
                    </Badge>
                  </Stack>
                </Paper>
              </SimpleGrid>

              {/* 5. Overfitting warnings */}
              {data.warnings.length > 0 && (
                <Alert
                  color="yellow"
                  icon={<IconAlertTriangle size={16} />}
                  title="Results may be misleading"
                >
                  <List size="sm">
                    {data.warnings.map((w, i) => (
                      <List.Item key={i}>{w.message}</List.Item>
                    ))}
                  </List>
                </Alert>
              )}

              {/* 6. Equity Curve chart */}
              <div>
                <Text size="sm" fw={600}>
                  Equity Curve
                </Text>
                <PlotlyChart
                  data={[
                    {
                      type: 'scatter' as const,
                      mode: 'lines' as const,
                      x: data.equity_curve.map((p) => p.timestamp),
                      y: data.equity_curve.map((p) => p.equity),
                      line: { color: '#339AF0', width: 1.5 },
                      name: 'Equity',
                    },
                  ]}
                  layout={{
                    shapes: buildPositionShapes(data.equity_curve),
                    yaxis: { title: { text: 'EUR' } },
                  }}
                  style={{ height: '280px' }}
                />
              </div>

              {/* 7. Drawdown chart */}
              <div>
                <Text size="sm" fw={600}>
                  Drawdown
                </Text>
                <PlotlyChart
                  data={[
                    {
                      type: 'scatter' as const,
                      mode: 'lines' as const,
                      x: data.equity_curve.map((p) => p.timestamp),
                      y: computeDrawdown(data.equity_curve),
                      fill: 'tozeroy' as const,
                      fillcolor: 'rgba(255, 107, 107, 0.3)',
                      line: { color: '#FF6B6B', width: 1 },
                      name: 'Drawdown %',
                    },
                  ]}
                  layout={{
                    yaxis: { title: { text: 'Drawdown %' } },
                  }}
                  style={{ height: '180px' }}
                />
              </div>

              {/* 8. Z-Score chart with trade markers */}
              {cointData ? (
                <div>
                  <Text size="sm" fw={600}>
                    Z-Score
                  </Text>
                  <PlotlyChart
                    data={[
                      {
                        type: 'scatter' as const,
                        mode: 'lines' as const,
                        x: cointData.timestamps,
                        y: cointData.zscore,
                        line: { color: '#339AF0', width: 1 },
                        name: 'Z-Score',
                      },
                      ...buildZScoreMarkerTraces(data.signal_overlay),
                    ]}
                    layout={{
                      shapes: buildZScoreShapes(
                        params.entry_threshold,
                        params.exit_threshold,
                      ),
                      yaxis: { title: { text: 'Z-Score' } },
                    }}
                    style={{ height: '300px' }}
                  />
                </div>
              ) : (
                <Text size="sm" c="dimmed">
                  Z-score chart unavailable -- cointegration data could not be
                  loaded.
                </Text>
              )}

              {/* 9. Spread chart with trade markers */}
              {cointData ? (
                <div>
                  <Text size="sm" fw={600}>
                    Spread
                  </Text>
                  <PlotlyChart
                    data={[
                      {
                        type: 'scatter' as const,
                        mode: 'lines' as const,
                        x: cointData.timestamps,
                        y: cointData.spread,
                        line: { color: '#339AF0', width: 1 },
                        name: 'Spread',
                      },
                      ...buildSpreadMarkerTraces(
                        data.signal_overlay,
                        cointData.timestamps,
                        cointData.spread,
                      ),
                    ]}
                    layout={{
                      yaxis: { title: { text: 'Spread' } },
                    }}
                    style={{ height: '260px' }}
                  />
                </div>
              ) : (
                <Text size="sm" c="dimmed">
                  Spread chart unavailable -- cointegration data could not be
                  loaded.
                </Text>
              )}

              {/* 10. No-trades check */}
              {data.trade_log.length === 0 ? (
                <Alert color="yellow">
                  No trades executed. Try widening the entry threshold or
                  increasing the lookback window.
                </Alert>
              ) : (
                <>
                  {/* 11. Trade log table */}
                  <Table striped highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>#</Table.Th>
                        <Table.Th>Direction</Table.Th>
                        <Table.Th>Entry</Table.Th>
                        <Table.Th>Exit</Table.Th>
                        <Table.Th>Bars</Table.Th>
                        <Table.Th>Exit Reason</Table.Th>
                        <Table.Th>Net P&L</Table.Th>
                        <Table.Th>Return</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {data.trade_log.slice(0, 50).map((trade) => (
                        <Table.Tr key={trade.trade_id}>
                          <Table.Td>{trade.trade_id}</Table.Td>
                          <Table.Td>
                            <Badge
                              size="sm"
                              variant="light"
                              color={
                                trade.direction === 'long_spread'
                                  ? 'green'
                                  : 'red'
                              }
                            >
                              {trade.direction === 'long_spread'
                                ? 'Long'
                                : 'Short'}
                            </Badge>
                          </Table.Td>
                          <Table.Td>
                            {new Date(trade.entry_timestamp).toLocaleDateString(
                              'en-GB',
                              {
                                day: '2-digit',
                                month: 'short',
                                hour: '2-digit',
                                minute: '2-digit',
                              }
                            )}
                          </Table.Td>
                          <Table.Td>
                            {new Date(trade.exit_timestamp).toLocaleDateString(
                              'en-GB',
                              {
                                day: '2-digit',
                                month: 'short',
                                hour: '2-digit',
                                minute: '2-digit',
                              }
                            )}
                          </Table.Td>
                          <Table.Td>{trade.bars_held}</Table.Td>
                          <Table.Td>
                            {trade.exit_reason === 'stop_loss' ? (
                              <Badge size="sm" variant="light" color="orange">
                                Stop Loss
                              </Badge>
                            ) : (
                              'Mean Rev.'
                            )}
                          </Table.Td>
                          <Table.Td>
                            <Text
                              size="sm"
                              c={trade.net_pnl > 0 ? 'green' : 'red'}
                            >
                              &euro;{trade.net_pnl.toFixed(2)}
                            </Text>
                          </Table.Td>
                          <Table.Td>
                            <Text
                              size="sm"
                              c={trade.return_pct > 0 ? 'green' : 'red'}
                            >
                              {trade.return_pct.toFixed(2)}%
                            </Text>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                  {data.trade_log.length > 50 && (
                    <Text size="xs" c="dimmed">
                      Showing first 50 of {data.trade_log.length} trades.
                    </Text>
                  )}
                </>
              )}

              {/* 12. Assumptions & Limitations accordion */}
              <Accordion variant="contained" radius="sm">
                <Accordion.Item value="assumptions">
                  <Accordion.Control>
                    Assumptions &amp; Limitations
                  </Accordion.Control>
                  <Accordion.Panel>
                    <Stack gap="sm">
                      <div>
                        <Text size="sm" fw={600}>
                          Execution Model
                        </Text>
                        <Text size="sm">{data.footer.execution_model}</Text>
                      </div>
                      <div>
                        <Text size="sm" fw={600}>
                          Fee Model
                        </Text>
                        <Text size="sm">{data.footer.fee_model}</Text>
                      </div>
                      <div>
                        <Text size="sm" fw={600}>
                          Data Basis
                        </Text>
                        <Text size="sm">{data.footer.data_basis}</Text>
                      </div>
                      <div>
                        <Text size="sm" fw={600}>
                          Assumptions
                        </Text>
                        <List size="sm">
                          {data.footer.assumptions.map((a, i) => (
                            <List.Item key={i}>{a}</List.Item>
                          ))}
                        </List>
                      </div>
                      <div>
                        <Text size="sm" fw={600}>
                          Limitations
                        </Text>
                        <List size="sm">
                          {data.footer.limitations.map((l, i) => (
                            <List.Item key={i}>{l}</List.Item>
                          ))}
                        </List>
                      </div>
                    </Stack>
                  </Accordion.Panel>
                </Accordion.Item>
              </Accordion>
            </>
          )}
        </Stack>
      )}
    </Stack>
  );
}
