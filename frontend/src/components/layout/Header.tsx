'use client';

import {
  Group,
  Select,
  Text,
  ThemeIcon,
  Tooltip,
} from '@mantine/core';
import {
  IconChartCandle,
  IconCoin,
  IconClock,
} from '@tabler/icons-react';
import { usePairContext } from '@/contexts/PairContext';

const TIMEFRAME_OPTIONS = ['15m', '1h', '4h', '1d'];

export function Header() {
  const {
    asset1,
    asset2,
    timeframe,
    setAsset1,
    setAsset2,
    setTimeframe,
    coins,
    loading,
    error,
  } = usePairContext();

  return (
    <Group justify="space-between" h="100%" px="md">
      <Group gap="sm">
        <ThemeIcon
          size="lg"
          radius="md"
          variant="gradient"
          gradient={{ from: 'blue', to: 'cyan', deg: 45 }}
        >
          <IconChartCandle size={22} stroke={1.5} />
        </ThemeIcon>
        <Text fw={700} size="lg" style={{ letterSpacing: '-0.3px' }}>
          Statistical Arbitrage
        </Text>
      </Group>

      <Group gap="xs">
        <Tooltip
          label={error ?? ''}
          disabled={!error}
          color="red"
          withArrow
        >
          <Select
            placeholder="Asset 1"
            searchable
            w={160}
            size="sm"
            leftSection={<IconCoin size={16} stroke={1.5} />}
            data={coins}
            value={asset1 || null}
            onChange={(v) => setAsset1(v ?? '')}
            disabled={loading}
            error={!!error}
          />
        </Tooltip>
        <Text c="dimmed" size="lg">
          x
        </Text>
        <Tooltip
          label={error ?? ''}
          disabled={!error}
          color="red"
          withArrow
        >
          <Select
            placeholder="Asset 2"
            searchable
            w={160}
            size="sm"
            leftSection={<IconCoin size={16} stroke={1.5} />}
            data={coins}
            value={asset2 || null}
            onChange={(v) => setAsset2(v ?? '')}
            disabled={loading}
            error={!!error}
          />
        </Tooltip>
        <Select
          placeholder="Timeframe"
          w={100}
          size="sm"
          leftSection={<IconClock size={16} stroke={1.5} />}
          data={TIMEFRAME_OPTIONS}
          value={timeframe}
          onChange={(v) => setTimeframe(v ?? '1h')}
        />
      </Group>
    </Group>
  );
}
