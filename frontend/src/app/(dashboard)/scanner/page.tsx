'use client';

import { useState, useCallback, useEffect } from 'react';
import {
  Alert,
  Badge,
  Button,
  Chip,
  Container,
  Divider,
  Group,
  Loader,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core';
import { IconSearch, IconRefresh, IconDownload, IconCheck } from '@tabler/icons-react';
import {
  fetchPairs,
  fetchAcademyScan,
  fetchLiveData,
  type AcademyScanPair,
  type FetchLiveDataResponse,
  type PairInfo,
} from '@/lib/api';

export default function ScannerPage() {
  // Fetch live data state
  const [fetching, setFetching] = useState(false);
  const [fetchResult, setFetchResult] = useState<FetchLiveDataResponse | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Available coins from the cache
  const [availableCoins, setAvailableCoins] = useState<string[]>([]);
  const [selectedCoins, setSelectedCoins] = useState<string[]>([]);
  const [timeframe, setTimeframe] = useState('1h');
  const [loadingPairs, setLoadingPairs] = useState(true);

  // Scan state
  const [scanning, setScanning] = useState(false);
  const [scanResults, setScanResults] = useState<AcademyScanPair[] | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanStats, setScanStats] = useState<{
    total: number;
    cointegrated: number;
    not: number;
  } | null>(null);

  // Reusable function to load available coins from cache
  const loadAvailableCoins = useCallback(async () => {
    setLoadingPairs(true);
    try {
      const res = await fetchPairs();
      const bases = [...new Set(
        res.pairs
          .filter((p) => p.timeframe === timeframe)
          .map((p) => p.base)
      )].sort();
      setAvailableCoins(bases);
      setSelectedCoins(bases); // Select all by default
    } catch {
      // Silently fail — user will see empty coin list
    } finally {
      setLoadingPairs(false);
    }
  }, [timeframe]);

  // Load available coins on mount and when timeframe changes
  useEffect(() => {
    let cancelled = false;
    loadAvailableCoins().then(() => {
      if (cancelled) return;
    });
    return () => { cancelled = true; };
  }, [loadAvailableCoins]);

  // Fetch fresh data from Bitvavo
  const handleFetchData = useCallback(async () => {
    setFetching(true);
    setFetchResult(null);
    setFetchError(null);
    try {
      const result = await fetchLiveData('1h', 90, 20);
      setFetchResult(result);
      // Refresh available coins to pick up newly fetched data
      await loadAvailableCoins();
    } catch (err) {
      setFetchError(
        err instanceof Error ? err.message : 'Failed to fetch data from Bitvavo'
      );
    } finally {
      setFetching(false);
    }
  }, [loadAvailableCoins]);

  const toggleCoin = useCallback((coin: string) => {
    setSelectedCoins((prev) =>
      prev.includes(coin)
        ? prev.filter((c) => c !== coin)
        : [...prev, coin]
    );
  }, []);

  const selectAll = useCallback(() => {
    setSelectedCoins([...availableCoins]);
  }, [availableCoins]);

  const deselectAll = useCallback(() => {
    setSelectedCoins([]);
  }, []);

  const runScan = useCallback(async () => {
    if (selectedCoins.length < 2) return;
    setScanning(true);
    setScanError(null);
    setScanResults(null);
    setScanStats(null);

    try {
      const res = await fetchAcademyScan(timeframe);
      // Filter results to only include selected coins
      const filterPair = (p: AcademyScanPair) => {
        const base1 = p.asset1.split('/')[0];
        const base2 = p.asset2.split('/')[0];
        return selectedCoins.includes(base1) && selectedCoins.includes(base2);
      };

      const cointegrated = res.cointegrated.filter(filterPair);
      const notCointegrated = res.not_cointegrated.filter(filterPair);
      const allResults = [...cointegrated, ...notCointegrated];

      // Sort by p-value
      allResults.sort((a, b) => a.p_value - b.p_value);

      setScanResults(allResults);
      setScanStats({
        total: allResults.length,
        cointegrated: cointegrated.length,
        not: notCointegrated.length,
      });
    } catch (err) {
      setScanError(
        err instanceof Error ? err.message : 'Scan failed. Is the API running?'
      );
    } finally {
      setScanning(false);
    }
  }, [selectedCoins, timeframe]);

  const possibleCombinations = (selectedCoins.length * (selectedCoins.length - 1)) / 2;

  return (
    <Container size="xl" py="md">
      <Stack gap="lg">
        <Stack gap="xs">
          <Title order={1}>Pair Scanner</Title>
          <Text c="dimmed">
            Scan all pair combinations for cointegration. Select coins, pick a timeframe, and hit Scan.
          </Text>
        </Stack>

        {/* Fetch Fresh Data */}
        <Paper p="md" radius="sm" withBorder>
          <Stack gap="md">
            <Text fw={600} size="sm">Fetch Fresh Data</Text>
            <Text size="sm" c="dimmed">
              Pull the latest OHLCV data from Bitvavo for the top 20 EUR-quoted coins (90 days, 1h candles).
            </Text>
            <Group gap="md" align="center">
              <Button
                leftSection={fetching ? <Loader size={14} color="white" /> : <IconDownload size={16} />}
                onClick={handleFetchData}
                disabled={fetching}
                variant="light"
                size="sm"
              >
                {fetching ? 'Fetching data from Bitvavo...' : 'Fetch Top 20 Coins from Bitvavo'}
              </Button>
            </Group>
            {fetchResult && (
              <Alert
                icon={<IconCheck size={16} />}
                color="teal"
                variant="light"
                title="Fetch complete"
              >
                Fetched {fetchResult.fetched} coins, {fetchResult.failed} failed (out of {fetchResult.total} total).
              </Alert>
            )}
            {fetchError && (
              <Alert color="red" variant="light" title="Fetch failed">
                {fetchError}
              </Alert>
            )}
          </Stack>
        </Paper>

        <Divider label="Scan Controls" labelPosition="center" />

        {/* Controls */}
        <Paper p="md" radius="sm" withBorder>
          <Stack gap="md">
            <Group justify="space-between">
              <Text fw={600} size="sm">Select coins to scan</Text>
              <Group gap="xs">
                <Button variant="subtle" size="xs" onClick={selectAll}>
                  All
                </Button>
                <Button variant="subtle" size="xs" onClick={deselectAll}>
                  None
                </Button>
              </Group>
            </Group>

            {loadingPairs ? (
              <Group gap="xs">
                <Loader size="xs" />
                <Text size="sm" c="dimmed">Loading available coins...</Text>
              </Group>
            ) : availableCoins.length === 0 ? (
              <Text size="sm" c="red.4">
                No cached data found. Start the API and ensure data is cached.
              </Text>
            ) : (
              <Group gap="xs">
                {availableCoins.map((coin) => (
                  <Chip
                    key={coin}
                    checked={selectedCoins.includes(coin)}
                    onChange={() => toggleCoin(coin)}
                    variant="filled"
                    size="sm"
                  >
                    {coin}
                  </Chip>
                ))}
              </Group>
            )}

            <Group gap="md" align="end">
              <Select
                label="Timeframe"
                data={[
                  { label: '1 hour', value: '1h' },
                  { label: '4 hours', value: '4h' },
                  { label: '1 day', value: '1d' },
                ]}
                value={timeframe}
                onChange={(v) => setTimeframe(v ?? '1h')}
                w={140}
                size="sm"
              />
              <Button
                leftSection={scanning ? <Loader size={14} color="white" /> : <IconSearch size={16} />}
                onClick={runScan}
                disabled={selectedCoins.length < 2 || scanning}
                size="sm"
              >
                {scanning ? 'Scanning...' : `Scan ${possibleCombinations} pairs`}
              </Button>
            </Group>
          </Stack>
        </Paper>

        {/* Error */}
        {scanError && (
          <Paper p="md" radius="sm" withBorder>
            <Text c="red.4">{scanError}</Text>
            <Text size="xs" c="dimmed" mt="xs">
              Make sure the API is running: uv run python run_api.py
            </Text>
          </Paper>
        )}

        {/* Results summary */}
        {scanStats && (
          <Group gap="lg">
            <Paper p="sm" px="md" radius="sm" withBorder>
              <Text size="xs" c="dimmed">Pairs scanned</Text>
              <Text size="lg" fw={700}>{scanStats.total}</Text>
            </Paper>
            <Paper p="sm" px="md" radius="sm" withBorder>
              <Text size="xs" c="dimmed">Cointegrated</Text>
              <Text size="lg" fw={700} c="teal.4">{scanStats.cointegrated}</Text>
            </Paper>
            <Paper p="sm" px="md" radius="sm" withBorder>
              <Text size="xs" c="dimmed">Not cointegrated</Text>
              <Text size="lg" fw={700} c="red.4">{scanStats.not}</Text>
            </Paper>
          </Group>
        )}

        {/* Results table */}
        {scanResults && scanResults.length > 0 && (
          <Paper radius="sm" withBorder>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Pair</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>p-value</Table.Th>
                  <Table.Th>Score</Table.Th>
                  <Table.Th>Hedge Ratio</Table.Th>
                  <Table.Th>Half-Life</Table.Th>
                  <Table.Th>Correlation</Table.Th>
                  <Table.Th>Observations</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {scanResults.map((pair) => {
                  const base1 = pair.asset1.split('/')[0];
                  const base2 = pair.asset2.split('/')[0];
                  return (
                    <Table.Tr
                      key={`${pair.asset1}-${pair.asset2}`}
                      style={{
                        backgroundColor: pair.is_cointegrated
                          ? 'rgba(32, 201, 151, 0.06)'
                          : undefined,
                      }}
                    >
                      <Table.Td>
                        <Text fw={600} size="sm">
                          {base1} / {base2}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          color={pair.is_cointegrated ? 'teal' : 'red'}
                          variant="light"
                          size="sm"
                        >
                          {pair.is_cointegrated ? 'Cointegrated' : 'Not cointegrated'}
                        </Badge>
                      </Table.Td>
                      <Table.Td>
                        <Text
                          size="sm"
                          fw={700}
                          c={pair.p_value < 0.05 ? 'teal.4' : pair.p_value < 0.1 ? 'yellow.4' : 'red.4'}
                        >
                          {pair.p_value.toFixed(4)}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{pair.cointegration_score.toFixed(3)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{pair.hedge_ratio.toFixed(3)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text
                          size="sm"
                          c={pair.half_life != null && pair.half_life > 0 ? undefined : 'dimmed'}
                        >
                          {pair.half_life != null && pair.half_life > 0
                            ? `${pair.half_life.toFixed(1)} bars`
                            : 'N/A'}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{pair.correlation.toFixed(3)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed">{pair.observations}</Text>
                      </Table.Td>
                    </Table.Tr>
                  );
                })}
              </Table.Tbody>
            </Table>
          </Paper>
        )}

        {scanResults && scanResults.length === 0 && (
          <Paper p="xl" radius="sm" withBorder>
            <Text ta="center" c="dimmed">
              No results. Try selecting more coins or a different timeframe.
            </Text>
          </Paper>
        )}
      </Stack>
    </Container>
  );
}
