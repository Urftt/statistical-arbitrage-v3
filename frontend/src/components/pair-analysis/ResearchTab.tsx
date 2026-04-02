'use client';

/**
 * ResearchTab component — displays 8 research modules in a Mantine Accordion.
 * Each module has independent loading/error/data state and a click-triggered Run button.
 * Implements cross-tab Apply to Backtest via onApplyToBacktest callback prop.
 */

import { useState, useEffect } from 'react';
import {
  Accordion,
  Alert,
  Button,
  Group,
  Loader,
  Skeleton,
  Stack,
  Text,
} from '@mantine/core';
import { IconPlayerPlay, IconArrowRight, IconAlertTriangle } from '@tabler/icons-react';
import PlotlyChart from '@/components/charts/PlotlyChart';
import { usePairContext } from '@/contexts/PairContext';
import {
  postRollingStability,
  postOOSValidation,
  postCointMethodComparison,
  postLookbackSweep,
  postZScoreThreshold,
  postTxCost,
  postSpreadMethodComparison,
  postTimeframeComparison,
  type BacktestRequest,
  type RollingStabilityResponse,
  type OOSValidationResponse,
  type CointMethodResponse,
  type LookbackSweepResponse,
  type ZScoreThresholdResponse,
  type TxCostResponse,
  type SpreadMethodResponse,
  type TimeframeResponse,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ResearchTabProps {
  onApplyToBacktest: (params: BacktestRequest) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ResearchTab({ onApplyToBacktest }: ResearchTabProps) {
  const { asset1, asset2, timeframe } = usePairContext();

  // Controlled accordion — all 3 section groups share this state
  const [openPanels, setOpenPanels] = useState<string[]>([]);

  // --- Pair Stability module state ---
  const [rollingLoading, setRollingLoading] = useState(false);
  const [rollingError, setRollingError] = useState<string | null>(null);
  const [rollingData, setRollingData] = useState<RollingStabilityResponse | null>(null);

  const [oosLoading, setOosLoading] = useState(false);
  const [oosError, setOosError] = useState<string | null>(null);
  const [oosData, setOosData] = useState<OOSValidationResponse | null>(null);

  const [cointLoading, setCointLoading] = useState(false);
  const [cointError, setCointError] = useState<string | null>(null);
  const [cointData, setCointData] = useState<CointMethodResponse | null>(null);

  // --- Parameter Tuning module state ---
  const [lookbackLoading, setLookbackLoading] = useState(false);
  const [lookbackError, setLookbackError] = useState<string | null>(null);
  const [lookbackData, setLookbackData] = useState<LookbackSweepResponse | null>(null);

  const [zscoreLoading, setZscoreLoading] = useState(false);
  const [zscoreError, setZscoreError] = useState<string | null>(null);
  const [zscoreData, setZscoreData] = useState<ZScoreThresholdResponse | null>(null);

  const [txcostLoading, setTxcostLoading] = useState(false);
  const [txcostError, setTxcostError] = useState<string | null>(null);
  const [txcostData, setTxcostData] = useState<TxCostResponse | null>(null);

  // --- Method Comparison module state ---
  const [spreadLoading, setSpreadLoading] = useState(false);
  const [spreadError, setSpreadError] = useState<string | null>(null);
  const [spreadData, setSpreadData] = useState<SpreadMethodResponse | null>(null);

  const [timeframeLoading, setTimeframeLoading] = useState(false);
  const [timeframeError, setTimeframeError] = useState<string | null>(null);
  const [timeframeData, setTimeframeData] = useState<TimeframeResponse | null>(null);

  // Pair-change reset — clears all module state and collapses panels (NAV-05)
  useEffect(() => {
    setRollingLoading(false); setRollingError(null); setRollingData(null);
    setOosLoading(false); setOosError(null); setOosData(null);
    setCointLoading(false); setCointError(null); setCointData(null);
    setLookbackLoading(false); setLookbackError(null); setLookbackData(null);
    setZscoreLoading(false); setZscoreError(null); setZscoreData(null);
    setTxcostLoading(false); setTxcostError(null); setTxcostData(null);
    setSpreadLoading(false); setSpreadError(null); setSpreadData(null);
    setTimeframeLoading(false); setTimeframeError(null); setTimeframeData(null);
    setOpenPanels([]);
  }, [asset1, asset2, timeframe]);

  // ---------------------------------------------------------------------------
  // Run handlers — click-triggered (RSRCH-04: no auto-load on mount)
  // ---------------------------------------------------------------------------

  async function handleRunRolling() {
    setRollingLoading(true);
    setRollingError(null);
    try {
      const res = await postRollingStability({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
      });
      setRollingData(res);
      setOpenPanels(prev => prev.includes('rolling') ? prev : [...prev, 'rolling']);
    } catch (err) {
      setRollingError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('rolling') ? prev : [...prev, 'rolling']);
    } finally {
      setRollingLoading(false);
    }
  }

  async function handleRunOos() {
    setOosLoading(true);
    setOosError(null);
    try {
      const res = await postOOSValidation({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
      });
      setOosData(res);
      setOpenPanels(prev => prev.includes('oos') ? prev : [...prev, 'oos']);
    } catch (err) {
      setOosError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('oos') ? prev : [...prev, 'oos']);
    } finally {
      setOosLoading(false);
    }
  }

  async function handleRunCoint() {
    setCointLoading(true);
    setCointError(null);
    try {
      const res = await postCointMethodComparison({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
      });
      setCointData(res);
      setOpenPanels(prev => prev.includes('coint') ? prev : [...prev, 'coint']);
    } catch (err) {
      setCointError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('coint') ? prev : [...prev, 'coint']);
    } finally {
      setCointLoading(false);
    }
  }

  async function handleRunLookback() {
    setLookbackLoading(true);
    setLookbackError(null);
    try {
      const res = await postLookbackSweep({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
      });
      setLookbackData(res);
      setOpenPanels(prev => prev.includes('lookback') ? prev : [...prev, 'lookback']);
    } catch (err) {
      setLookbackError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('lookback') ? prev : [...prev, 'lookback']);
    } finally {
      setLookbackLoading(false);
    }
  }

  async function handleRunZscore() {
    setZscoreLoading(true);
    setZscoreError(null);
    try {
      const res = await postZScoreThreshold({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
      });
      setZscoreData(res);
      setOpenPanels(prev => prev.includes('zscore') ? prev : [...prev, 'zscore']);
    } catch (err) {
      setZscoreError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('zscore') ? prev : [...prev, 'zscore']);
    } finally {
      setZscoreLoading(false);
    }
  }

  async function handleRunTxcost() {
    setTxcostLoading(true);
    setTxcostError(null);
    try {
      const res = await postTxCost({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
      });
      setTxcostData(res);
      setOpenPanels(prev => prev.includes('txcost') ? prev : [...prev, 'txcost']);
    } catch (err) {
      setTxcostError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('txcost') ? prev : [...prev, 'txcost']);
    } finally {
      setTxcostLoading(false);
    }
  }

  async function handleRunSpread() {
    setSpreadLoading(true);
    setSpreadError(null);
    try {
      const res = await postSpreadMethodComparison({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        timeframe,
        days_back: 365,
      });
      setSpreadData(res);
      setOpenPanels(prev => prev.includes('spread') ? prev : [...prev, 'spread']);
    } catch (err) {
      setSpreadError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('spread') ? prev : [...prev, 'spread']);
    } finally {
      setSpreadLoading(false);
    }
  }

  async function handleRunTimeframe() {
    setTimeframeLoading(true);
    setTimeframeError(null);
    try {
      const res = await postTimeframeComparison({
        asset1: `${asset1}/EUR`,
        asset2: `${asset2}/EUR`,
        days_back: 365,
      });
      setTimeframeData(res);
      setOpenPanels(prev => prev.includes('timeframe') ? prev : [...prev, 'timeframe']);
    } catch (err) {
      setTimeframeError(err instanceof Error ? err.message : 'Unknown error');
      setOpenPanels(prev => prev.includes('timeframe') ? prev : [...prev, 'timeframe']);
    } finally {
      setTimeframeLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Stack gap="lg">

      {/* ===== PAIR STABILITY ===== */}
      <Text size="xs" fw={600} c="dimmed" tt="uppercase" mb="xs">Pair Stability</Text>
      <Accordion multiple value={openPanels} onChange={setOpenPanels}>

        {/* Rolling Stability */}
        <Accordion.Item value="rolling">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Rolling Stability</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={rollingLoading}
                leftSection={rollingLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunRolling(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {rollingLoading && (
                <>
                  <Skeleton height={260} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {rollingError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {rollingError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {rollingData && (
                <>
                  <PlotlyChart
                    data={[
                      {
                        type: 'scatter' as const,
                        mode: 'lines' as const,
                        x: rollingData.results.map(r => new Date(r.timestamp).toISOString()),
                        y: rollingData.results.map(r => r.p_value),
                        line: { color: '#339AF0', width: 1.5 },
                        name: 'p-value',
                        connectgaps: false,
                      },
                      {
                        type: 'scatter' as const,
                        mode: 'markers' as const,
                        x: rollingData.results
                          .filter(r => r.is_cointegrated && r.p_value !== null)
                          .map(r => new Date(r.timestamp).toISOString()),
                        y: rollingData.results
                          .filter(r => r.is_cointegrated && r.p_value !== null)
                          .map(r => r.p_value),
                        marker: { color: '#51CF66', size: 6 },
                        name: 'Cointegrated',
                      },
                    ]}
                    layout={{
                      shapes: [{
                        type: 'line' as const,
                        x0: 0,
                        x1: 1,
                        xref: 'paper' as const,
                        y0: 0.05,
                        y1: 0.05,
                        line: { color: '#339AF0', width: 1, dash: 'dash' as const },
                      }],
                      xaxis: { type: 'date' as const },
                      yaxis: { title: { text: 'p-value' }, range: [0, 1] },
                      annotations: [{
                        xref: 'paper' as const,
                        yref: 'y' as const,
                        x: 0.02,
                        y: 0.05,
                        text: 'p=0.05',
                        showarrow: false,
                        font: { color: '#339AF0', size: 10 },
                      }],
                      margin: { t: 48, b: 40, l: 56, r: 24 },
                    }}
                    style={{ height: '260px' }}
                  />
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={rollingData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {rollingData.takeaway.text}
                  </Alert>
                  {rollingData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(rollingData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        {/* OOS Validation */}
        <Accordion.Item value="oos">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Out-of-Sample Validation</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={oosLoading}
                leftSection={oosLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunOos(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {oosLoading && (
                <>
                  <Skeleton height={240} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {oosError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {oosError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {oosData && (
                <>
                  <PlotlyChart
                    data={[
                      {
                        type: 'bar' as const,
                        x: oosData.results.map(r => `${Math.round(r.split_ratio * 100)}%`),
                        y: oosData.results.map(r => r.formation_p_value),
                        name: 'Formation',
                        marker: { color: '#339AF0' },
                      },
                      {
                        type: 'bar' as const,
                        x: oosData.results.map(r => `${Math.round(r.split_ratio * 100)}%`),
                        y: oosData.results.map(r => r.trading_p_value),
                        name: 'Trading',
                        marker: { color: '#51CF66' },
                      },
                    ]}
                    layout={{
                      barmode: 'group' as const,
                      xaxis: { title: { text: 'Split Ratio' } },
                      yaxis: { title: { text: 'p-value' } },
                      margin: { t: 48, b: 40, l: 56, r: 24 },
                    }}
                    style={{ height: '240px' }}
                  />
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={oosData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {oosData.takeaway.text}
                  </Alert>
                  {oosData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(oosData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        {/* Cointegration Method */}
        <Accordion.Item value="coint">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Cointegration Method Comparison</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={cointLoading}
                leftSection={cointLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunCoint(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {cointLoading && (
                <>
                  <Skeleton height={220} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {cointError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {cointError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {cointData && (
                <>
                  <PlotlyChart
                    data={[
                      {
                        type: 'bar' as const,
                        x: cointData.results.map(r => r.method),
                        y: cointData.results.map(r => r.statistic),
                        marker: {
                          color: cointData.results.map(r => r.is_cointegrated ? '#51CF66' : '#FF6B6B'),
                        },
                        text: cointData.results.map(r => r.is_cointegrated ? 'Coint.' : 'Not coint.'),
                        textposition: 'outside' as const,
                      },
                    ]}
                    layout={{
                      xaxis: { title: { text: 'Method' } },
                      yaxis: { title: { text: 'Test Statistic' } },
                      margin: { t: 48, b: 40, l: 56, r: 24 },
                    }}
                    style={{ height: '220px' }}
                  />
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={cointData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {cointData.takeaway.text}
                  </Alert>
                  {cointData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(cointData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

      </Accordion>

      {/* ===== PARAMETER TUNING ===== */}
      <Text size="xs" fw={600} c="dimmed" tt="uppercase" mb="xs">Parameter Tuning</Text>
      <Accordion multiple value={openPanels} onChange={setOpenPanels}>

        {/* Lookback Window Sweep */}
        <Accordion.Item value="lookback">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Lookback Window Sweep</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={lookbackLoading}
                leftSection={lookbackLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunLookback(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {lookbackLoading && (
                <>
                  <Skeleton height={240} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {lookbackError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {lookbackError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {lookbackData && (
                <>
                  <Text c="dimmed" size="sm">Chart implementation in Plan 02</Text>
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={lookbackData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {lookbackData.takeaway.text}
                  </Alert>
                  {lookbackData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(lookbackData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        {/* Z-Score Threshold */}
        <Accordion.Item value="zscore">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Z-Score Threshold Sweep</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={zscoreLoading}
                leftSection={zscoreLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunZscore(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {zscoreLoading && (
                <>
                  <Skeleton height={220} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {zscoreError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {zscoreError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {zscoreData && (
                <>
                  <Text c="dimmed" size="sm">Chart implementation in Plan 02</Text>
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={zscoreData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {zscoreData.takeaway.text}
                  </Alert>
                  {zscoreData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(zscoreData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        {/* Transaction Cost */}
        <Accordion.Item value="txcost">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Transaction Cost Impact</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={txcostLoading}
                leftSection={txcostLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunTxcost(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {txcostLoading && (
                <>
                  <Skeleton height={220} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {txcostError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {txcostError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {txcostData && (
                <>
                  <Text c="dimmed" size="sm">Chart implementation in Plan 02</Text>
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={txcostData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {txcostData.takeaway.text}
                  </Alert>
                  {txcostData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(txcostData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

      </Accordion>

      {/* ===== METHOD COMPARISON ===== */}
      <Text size="xs" fw={600} c="dimmed" tt="uppercase" mb="xs">Method Comparison</Text>
      <Accordion multiple value={openPanels} onChange={setOpenPanels}>

        {/* Spread Method */}
        <Accordion.Item value="spread">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Spread Method Comparison</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={spreadLoading}
                leftSection={spreadLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunSpread(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {spreadLoading && (
                <>
                  <Skeleton height={220} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {spreadError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {spreadError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {spreadData && (
                <>
                  <Text c="dimmed" size="sm">Chart implementation in Plan 02</Text>
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={spreadData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {spreadData.takeaway.text}
                  </Alert>
                  {spreadData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(spreadData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        {/* Timeframe Comparison */}
        <Accordion.Item value="timeframe">
          <Accordion.Control>
            <Group justify="space-between" pr="sm">
              <Text size="sm" fw={500}>Timeframe Comparison</Text>
              <Button
                size="xs"
                variant="filled"
                color="blue"
                disabled={timeframeLoading}
                leftSection={timeframeLoading ? <Loader size="xs" /> : <IconPlayerPlay size={14} />}
                onClick={(e) => { e.stopPropagation(); handleRunTimeframe(); }}
              >
                Run
              </Button>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="md">
              {timeframeLoading && (
                <>
                  <Skeleton height={220} />
                  <Text size="sm" c="dimmed" ta="center">Running module...</Text>
                </>
              )}
              {timeframeError && (
                <Alert color="red" icon={<IconAlertTriangle size={16} />}>
                  Module failed — {timeframeError}. Check that both assets have cached data and try again.
                </Alert>
              )}
              {timeframeData && (
                <>
                  <Text c="dimmed" size="sm">Chart implementation in Plan 02</Text>
                  <Text size="xs" c="dimmed">Generated for {asset1}/{asset2}</Text>
                  <Alert color={timeframeData.takeaway.severity} icon={<IconAlertTriangle size={16} />}>
                    {timeframeData.takeaway.text}
                  </Alert>
                  {timeframeData.recommended_backtest_params && (
                    <Button
                      variant="filled"
                      color="blue"
                      size="xs"
                      leftSection={<IconArrowRight size={16} />}
                      onClick={() => onApplyToBacktest(timeframeData.recommended_backtest_params!)}
                    >
                      Apply to Backtest
                    </Button>
                  )}
                </>
              )}
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

      </Accordion>

    </Stack>
  );
}
