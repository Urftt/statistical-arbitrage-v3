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
  Select,
  NumberInput,
  Alert,
  Accordion,
  Skeleton,
  List,
} from '@mantine/core';
import { IconPlayerPlay, IconAlertTriangle } from '@tabler/icons-react';
import PlotlyChart from '@/components/charts/PlotlyChart';
import {
  postGridSearch,
  postWalkForward,
  type BacktestRequest,
  type StrategyParametersPayload,
  type GridSearchRequest,
  type GridSearchResponse,
  type GridSearchCellPayload,
  type WalkForwardRequest,
  type WalkForwardResponse,
  type ParameterAxisPayload,
} from '@/lib/api';
import { usePairContext } from '@/contexts/PairContext';
import type { Data } from 'plotly.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SWEEPABLE_PARAMS = [
  { value: 'entry_threshold', label: 'Entry Threshold' },
  { value: 'exit_threshold', label: 'Exit Threshold' },
  { value: 'lookback_window', label: 'Lookback Window' },
  { value: 'stop_loss', label: 'Stop-Loss' },
  { value: 'position_size', label: 'Position Size' },
];

const PARAM_DEFAULTS: Record<string, { min: number; max: number; step: number }> = {
  entry_threshold: { min: 1.0, max: 3.0, step: 0.5 },
  exit_threshold: { min: 0.1, max: 1.0, step: 0.1 },
  lookback_window: { min: 20, max: 120, step: 10 },
  stop_loss: { min: 2.0, max: 5.0, step: 0.5 },
  position_size: { min: 0.2, max: 0.8, step: 0.1 },
};

const METRIC_OPTIONS = [
  { value: 'sharpe_ratio', label: 'Sharpe Ratio' },
  { value: 'total_pnl', label: 'Total P&L' },
  { value: 'win_rate', label: 'Win Rate' },
  { value: 'max_drawdown', label: 'Max Drawdown' },
];

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

function buildAxisValues(axis: ParameterAxisPayload): number[] {
  const values: number[] = [];
  for (let v = axis.min_value; v <= axis.max_value + axis.step / 2; v += axis.step) {
    values.push(Math.round(v * 1e10) / 1e10);
  }
  return values;
}

function getMetricValue(cell: GridSearchCellPayload, metric: string): number | null {
  switch (metric) {
    case 'sharpe_ratio':
      return cell.metrics.sharpe_ratio;
    case 'total_pnl':
      return cell.metrics.total_net_pnl;
    case 'win_rate':
      return cell.metrics.win_rate;
    case 'max_drawdown':
      return cell.metrics.max_drawdown_pct;
    default:
      return null;
  }
}

function colorscaleForMetric(metric: string): string {
  if (metric === 'win_rate') return 'Blues';
  if (metric === 'max_drawdown') return 'RdYlGn_r';
  return 'RdYlGn';
}

function robustnessLabel(score: number | null): { label: string; color: string } {
  if (score === null) return { label: 'N/A', color: 'gray' };
  if (score >= 0.7) return { label: 'Strong', color: 'green' };
  if (score >= 0.4) return { label: 'Moderate', color: 'yellow' };
  return { label: 'Weak', color: 'red' };
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface OptimizeTabProps {
  baseStrategy: StrategyParametersPayload;
  onApplyToBacktest: (params: BacktestRequest) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function OptimizeTab({ baseStrategy, onApplyToBacktest }: OptimizeTabProps) {
  const { asset1, asset2, timeframe } = usePairContext();

  // Axis 1 config
  const [axis1Param, setAxis1Param] = useState<string>('entry_threshold');
  const [axis1Min, setAxis1Min] = useState<number>(PARAM_DEFAULTS.entry_threshold.min);
  const [axis1Max, setAxis1Max] = useState<number>(PARAM_DEFAULTS.entry_threshold.max);
  const [axis1Step, setAxis1Step] = useState<number>(PARAM_DEFAULTS.entry_threshold.step);

  // Axis 2 config
  const [axis2Param, setAxis2Param] = useState<string>('exit_threshold');
  const [axis2Min, setAxis2Min] = useState<number>(PARAM_DEFAULTS.exit_threshold.min);
  const [axis2Max, setAxis2Max] = useState<number>(PARAM_DEFAULTS.exit_threshold.max);
  const [axis2Step, setAxis2Step] = useState<number>(PARAM_DEFAULTS.exit_threshold.step);

  // Grid search state
  const [gridLoading, setGridLoading] = useState(false);
  const [gridError, setGridError] = useState<string | null>(null);
  const [gridData, setGridData] = useState<GridSearchResponse | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<string>('sharpe_ratio');

  // Walk-forward state (data managed here, UI in Plan 02)
  const [wfLoading, setWfLoading] = useState(false);
  const [wfError, setWfError] = useState<string | null>(null);
  const [wfData, setWfData] = useState<WalkForwardResponse | null>(null);
  const [foldCount] = useState<number>(5);
  const [trainPct] = useState<number>(60);

  const cancelRef = useRef<boolean>(false);

  // Pair-change effect
  useEffect(() => {
    cancelRef.current = true;
    setGridData(null);
    setWfData(null);
    setGridError(null);
    setWfError(null);
  }, [asset1, asset2, timeframe]);

  // Axis param change handlers
  function handleAxis1ParamChange(value: string | null) {
    if (!value) return;
    setAxis1Param(value);
    const d = PARAM_DEFAULTS[value];
    setAxis1Min(d.min);
    setAxis1Max(d.max);
    setAxis1Step(d.step);
    setGridData(null);
    setWfData(null);
  }

  function handleAxis2ParamChange(value: string | null) {
    if (!value) return;
    setAxis2Param(value);
    const d = PARAM_DEFAULTS[value];
    setAxis2Min(d.min);
    setAxis2Max(d.max);
    setAxis2Step(d.step);
    setGridData(null);
    setWfData(null);
  }

  // Grid search handler
  async function handleGridSearch() {
    cancelRef.current = false;
    setGridLoading(true);
    setGridError(null);
    try {
      const req: GridSearchRequest = {
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
        axes: [
          { name: axis1Param, min_value: axis1Min, max_value: axis1Max, step: axis1Step },
          { name: axis2Param, min_value: axis2Min, max_value: axis2Max, step: axis2Step },
        ],
        base_strategy: { ...baseStrategy, min_trade_count_warning: 3 },
        optimize_metric: 'sharpe_ratio',
        max_combinations: 500,
      };
      const res = await postGridSearch(req);
      if (!cancelRef.current) setGridData(res);
    } catch (err: unknown) {
      if (!cancelRef.current) setGridError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      if (!cancelRef.current) setGridLoading(false);
    }
  }

  // Walk-forward handler
  async function handleWalkForward() {
    cancelRef.current = false;
    setWfLoading(true);
    setWfError(null);
    try {
      const req: WalkForwardRequest = {
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
        axes: [
          { name: axis1Param, min_value: axis1Min, max_value: axis1Max, step: axis1Step },
          { name: axis2Param, min_value: axis2Min, max_value: axis2Max, step: axis2Step },
        ],
        base_strategy: { ...baseStrategy, min_trade_count_warning: 3 },
        fold_count: foldCount,
        train_pct: trainPct / 100,
        optimize_metric: 'sharpe_ratio',
        max_combinations_per_fold: 500,
      };
      const res = await postWalkForward(req);
      if (!cancelRef.current) setWfData(res);
    } catch (err: unknown) {
      if (!cancelRef.current) setWfError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      if (!cancelRef.current) setWfLoading(false);
    }
  }

  if (!asset1 || !asset2) {
    return (
      <Paper p="xl" ta="center">
        <Text c="dimmed">Select a pair in the header to run optimization.</Text>
      </Paper>
    );
  }

  return (
    <Stack gap="lg">
      {/* Axis Configuration */}
      <Paper withBorder p="md">
        <SimpleGrid cols={2} spacing="lg">
          {/* Column 1: Parameter 1 */}
          <Stack gap="sm">
            <Text size="sm" fw={600}>
              Parameter 1
            </Text>
            <Select
              data={SWEEPABLE_PARAMS}
              value={axis1Param}
              onChange={handleAxis1ParamChange}
            />
            <SimpleGrid cols={3} spacing="sm">
              <NumberInput
                label="Min"
                value={axis1Min}
                onChange={(v) => setAxis1Min(typeof v === 'number' ? v : parseFloat(String(v)) || 0)}
                step={axis1Step}
                decimalScale={2}
              />
              <NumberInput
                label="Max"
                value={axis1Max}
                onChange={(v) => setAxis1Max(typeof v === 'number' ? v : parseFloat(String(v)) || 0)}
                step={axis1Step}
                decimalScale={2}
              />
              <NumberInput
                label="Step"
                value={axis1Step}
                onChange={(v) => setAxis1Step(typeof v === 'number' ? v : parseFloat(String(v)) || 0)}
                step={0.1}
                decimalScale={2}
                min={0.01}
              />
            </SimpleGrid>
          </Stack>

          {/* Column 2: Parameter 2 */}
          <Stack gap="sm">
            <Text size="sm" fw={600}>
              Parameter 2
            </Text>
            <Select
              data={SWEEPABLE_PARAMS}
              value={axis2Param}
              onChange={handleAxis2ParamChange}
            />
            <SimpleGrid cols={3} spacing="sm">
              <NumberInput
                label="Min"
                value={axis2Min}
                onChange={(v) => setAxis2Min(typeof v === 'number' ? v : parseFloat(String(v)) || 0)}
                step={axis2Step}
                decimalScale={2}
              />
              <NumberInput
                label="Max"
                value={axis2Max}
                onChange={(v) => setAxis2Max(typeof v === 'number' ? v : parseFloat(String(v)) || 0)}
                step={axis2Step}
                decimalScale={2}
              />
              <NumberInput
                label="Step"
                value={axis2Step}
                onChange={(v) => setAxis2Step(typeof v === 'number' ? v : parseFloat(String(v)) || 0)}
                step={0.1}
                decimalScale={2}
                min={0.01}
              />
            </SimpleGrid>
          </Stack>
        </SimpleGrid>
      </Paper>

      {/* Run Buttons */}
      <Group gap="md">
        <Button
          variant="filled"
          color="blue"
          onClick={handleGridSearch}
          disabled={gridLoading || wfLoading || !asset1 || !asset2}
          loading={gridLoading}
          leftSection={<IconPlayerPlay size={16} />}
        >
          Run Grid Search
        </Button>
        <Button
          variant="filled"
          color="blue"
          onClick={handleWalkForward}
          disabled={gridLoading || wfLoading || !asset1 || !asset2}
          loading={wfLoading}
          leftSection={<IconPlayerPlay size={16} />}
        >
          Run Walk-Forward
        </Button>
      </Group>

      {/* Error states */}
      {gridError && (
        <Alert color="red" icon={<IconAlertTriangle size={16} />}>
          Grid search failed: {gridError}. Check that the selected pair has cached data and try
          again.
        </Alert>
      )}
      {wfError && (
        <Alert color="red" icon={<IconAlertTriangle size={16} />}>
          Walk-forward failed: {wfError}. Check that the selected pair has cached data and try
          again.
        </Alert>
      )}

      {/* Empty state */}
      {!gridData && !wfData && !gridLoading && !wfLoading && !gridError && !wfError && (
        <Paper p="xl" ta="center">
          <Text size="lg" fw={600}>
            Configure axes to begin
          </Text>
          <Text size="sm" c="dimmed">
            Select two parameters and define their sweep ranges above, then run Grid Search or
            Walk-Forward.
          </Text>
        </Paper>
      )}

      {/* Grid Search Loading skeleton */}
      {gridLoading && (
        <Stack gap="md">
          <Skeleton height={88} />
          <Skeleton height={360} />
          <Text size="sm" c="dimmed" ta="center">
            Running grid search...
          </Text>
        </Stack>
      )}

      {/* Grid Search Results */}
      {gridData && !gridLoading && (
        <Stack gap="md">
          {/* Warnings */}
          {gridData.warnings.map((warning, i) => (
            <Alert
              key={i}
              color={warning.severity === 'blocking' ? 'red' : 'yellow'}
              icon={<IconAlertTriangle size={16} />}
            >
              {warning.message}
            </Alert>
          ))}

          {/* Best Cell Card */}
          {gridData.best_cell && (
            <Paper withBorder p="md">
              <Group justify="space-between">
                <Text size="md" fw={600}>
                  Best Parameters (In-Sample)
                </Text>
                <Badge
                  size="lg"
                  variant="light"
                  color={robustnessLabel(gridData.robustness_score).color}
                >
                  {robustnessLabel(gridData.robustness_score).label}
                </Badge>
              </Group>
              <SimpleGrid cols={4} spacing="sm" mt="sm">
                <Stack gap={4}>
                  <Text size="xs" c="dimmed">
                    {gridData.axes[0].name}
                  </Text>
                  <Text size="md" fw={600}>
                    {gridData.best_cell.params[gridData.axes[0].name]}
                  </Text>
                </Stack>
                <Stack gap={4}>
                  <Text size="xs" c="dimmed">
                    {gridData.axes[1].name}
                  </Text>
                  <Text size="md" fw={600}>
                    {gridData.best_cell.params[gridData.axes[1].name]}
                  </Text>
                </Stack>
                <Stack gap={4}>
                  <Text size="xs" c="dimmed">
                    Sharpe Ratio
                  </Text>
                  <Text size="md" fw={600}>
                    {gridData.best_cell.metrics.sharpe_ratio?.toFixed(2) ?? 'N/A'}
                  </Text>
                </Stack>
                <Stack gap={4}>
                  <Text size="xs" c="dimmed">
                    Total P&L
                  </Text>
                  <Text size="md" fw={600}>
                    EUR {gridData.best_cell.metrics.total_net_pnl.toFixed(2)}
                  </Text>
                </Stack>
              </SimpleGrid>
              <Group justify="flex-end" mt="sm">
                <Button
                  variant="light"
                  color="blue"
                  size="sm"
                  onClick={() => {
                    if (gridData.recommended_backtest_params)
                      onApplyToBacktest(gridData.recommended_backtest_params);
                  }}
                  disabled={!gridData.recommended_backtest_params}
                >
                  Apply to Backtest
                </Button>
              </Group>
            </Paper>
          )}

          {/* Metric Selector + Section Heading */}
          <Group justify="space-between">
            <Text size="md" fw={600}>
              Parameter Heatmap
            </Text>
            <Select
              label="Color by"
              data={METRIC_OPTIONS}
              value={selectedMetric}
              onChange={(v) => {
                if (v) setSelectedMetric(v);
              }}
              w={180}
            />
          </Group>

          {/* Heatmap */}
          {(() => {
            const [nRows, nCols] = gridData.grid_shape;
            const axis1Values = buildAxisValues(gridData.axes[0]);
            const axis2Values = buildAxisValues(gridData.axes[1]);
            const zMatrix: (number | null)[][] = Array.from({ length: nRows }, (_, r) =>
              Array.from({ length: nCols }, (_, c) => {
                const cell = gridData.cells[r * nCols + c];
                return cell.status === 'ok' ? getMetricValue(cell, selectedMetric) : null;
              })
            );
            const customData = Array.from({ length: nRows }, (_, r) =>
              Array.from({ length: nCols }, (_, c) => {
                const cell = gridData.cells[r * nCols + c];
                if (cell.status !== 'ok') return 'No data';
                return `Sharpe: ${cell.metrics.sharpe_ratio?.toFixed(3) ?? 'N/A'}\nP&L: EUR ${cell.metrics.total_net_pnl.toFixed(2)}\nWin Rate: ${(cell.metrics.win_rate * 100).toFixed(1)}%\nTrades: ${cell.trade_count}`;
              })
            );
            const annotations =
              gridData.best_cell_index !== null
                ? [
                    {
                      x: axis2Values[gridData.best_cell_index % nCols],
                      y: axis1Values[Math.floor(gridData.best_cell_index / nCols)],
                      text: '\u2605',
                      font: { size: 18, color: '#FCC419' },
                      showarrow: false,
                    },
                  ]
                : [];

            const heatmapData: Data[] = [
              {
                type: 'heatmap' as const,
                x: axis2Values,
                y: axis1Values,
                z: zMatrix,
                colorscale: colorscaleForMetric(selectedMetric),
                hovertemplate:
                  `${gridData.axes[1].name}: %{x}<br>` +
                  `${gridData.axes[0].name}: %{y}<br>` +
                  `%{text}<extra></extra>`,
                text: customData as unknown as string[],
              },
            ];

            return (
              <PlotlyChart
                data={heatmapData}
                layout={{
                  annotations,
                  xaxis: { title: { text: gridData.axes[1].name } },
                  yaxis: { title: { text: gridData.axes[0].name } },
                }}
                style={{ height: 360 }}
              />
            );
          })()}

          {/* Honest Reporting Accordion */}
          <Accordion variant="separated">
            <Accordion.Item value="gs-assumptions">
              <Accordion.Control>Assumptions &amp; Limitations</Accordion.Control>
              <Accordion.Panel>
                <List size="sm">
                  {gridData.footer.assumptions.map((a, i) => (
                    <List.Item key={`a-${i}`}>
                      <Text size="sm" c="dimmed">
                        {a}
                      </Text>
                    </List.Item>
                  ))}
                  {gridData.footer.limitations.map((l, i) => (
                    <List.Item key={`l-${i}`}>
                      <Text size="sm" c="dimmed">
                        {l}
                      </Text>
                    </List.Item>
                  ))}
                </List>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Stack>
      )}

      {/* Walk-Forward Loading skeleton */}
      {wfLoading && (
        <Stack gap="md">
          <Skeleton height={200} />
          <Text size="sm" c="dimmed" ta="center">
            Running walk-forward...
          </Text>
        </Stack>
      )}

      {/* Walk-Forward Results placeholder (Plan 02 will fill this in) */}
      {wfData && !wfLoading && (
        <Paper withBorder p="md">
          <Text size="md" fw={600}>
            Walk-Forward Validation
          </Text>
          <Text size="sm" c="dimmed">
            Walk-forward results will be rendered in Plan 02.
          </Text>
        </Paper>
      )}
    </Stack>
  );
}
