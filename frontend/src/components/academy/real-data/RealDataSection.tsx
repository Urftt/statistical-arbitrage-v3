'use client';

import { useState, type ReactNode } from 'react';
import {
  Box,
  Button,
  Group,
  Loader,
  SegmentedControl,
  Stack,
  Text,
} from '@mantine/core';
import { IconChartLine, IconX } from '@tabler/icons-react';
import { useAcademyData, type AcademyPairData } from '@/contexts/AcademyDataContext';

/**
 * Wrapper for real data sections in Academy lessons.
 *
 * Provides:
 * - Collapsed/expanded toggle
 * - Good/bad pair selector tabs
 * - Passes the active pair data to children
 *
 * Children receive the active pair data via render prop.
 */
interface RealDataSectionProps {
  /** Intro text shown in collapsed state */
  intro?: string;
  /** Whether to show good/bad pair tabs. Default true. */
  showComparison?: boolean;
  /** Render function receiving the active pair data and whether it's the "good" pair */
  children: (data: AcademyPairData, isGoodPair: boolean) => ReactNode;
}

export function RealDataSection({
  intro = 'See how this looks with real crypto data.',
  showComparison = true,
  children,
}: RealDataSectionProps) {
  const { goodPair, badPair, loading, error, ready, refresh } = useAcademyData();
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'good' | 'bad'>('good');

  const currentData = activeTab === 'good' ? goodPair : badPair;
  const hasBothPairs = goodPair !== null && badPair !== null;

  const handleOpen = () => {
    setOpen(true);
    if (!ready && !loading) refresh();
  };

  // Collapsed
  if (!open) {
    return (
      <Box
        p="md"
        style={{
          borderRadius: 8,
          border: '1px dashed var(--mantine-color-dark-4)',
          backgroundColor: 'rgba(51, 154, 240, 0.03)',
        }}
      >
        <Group justify="space-between">
          <Text size="sm" c="dimmed">{intro}</Text>
          <Button
            variant="light"
            size="xs"
            leftSection={<IconChartLine size={14} />}
            onClick={handleOpen}
          >
            See real data
          </Button>
        </Group>
      </Box>
    );
  }

  // Expanded
  return (
    <Stack
      gap="sm"
      p="md"
      style={{
        borderRadius: 8,
        border: '1px solid var(--mantine-color-dark-4)',
        backgroundColor: 'rgba(51, 154, 240, 0.03)',
      }}
    >
      <Group justify="space-between">
        <Text size="sm" fw={600}>Real data</Text>
        <Button
          variant="subtle"
          size="xs"
          color="gray"
          onClick={() => setOpen(false)}
          leftSection={<IconX size={14} />}
        >
          Close
        </Button>
      </Group>

      {/* Good/Bad pair tabs */}
      {showComparison && hasBothPairs && (
        <SegmentedControl
          value={activeTab}
          onChange={(v) => setActiveTab(v as 'good' | 'bad')}
          data={[
            { label: `${goodPair!.pair.label} (cointegrated)`, value: 'good' },
            { label: `${badPair!.pair.label} (not cointegrated)`, value: 'bad' },
          ]}
          size="xs"
          fullWidth
        />
      )}

      {/* Loading */}
      {loading && (
        <Group justify="center" py="xl">
          <Loader size="sm" />
          <Text size="sm" c="dimmed">Fetching live data from Bitvavo...</Text>
        </Group>
      )}

      {/* Error */}
      {error && (
        <Stack gap="xs" py="sm">
          <Text size="sm" c="red.4">{error}</Text>
          <Text size="xs" c="dimmed">Make sure the API is running: uv run python run_api.py</Text>
        </Stack>
      )}

      {/* Content — rendered by children */}
      {currentData && !loading && children(currentData, activeTab === 'good')}

      {/* No data */}
      {ready && !currentData && !loading && (
        <Text size="sm" c="dimmed" ta="center" py="md">
          No pairs available. Use the Scanner to fetch data first.
        </Text>
      )}
    </Stack>
  );
}
