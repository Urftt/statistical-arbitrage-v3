'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Card,
  Group,
  Slider,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Timeline,
} from '@mantine/core';
import {
  IconBulb,
  IconArrowUp,
  IconArrowDown,
  IconArrowsExchange,
  IconCash,
} from '@tabler/icons-react';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 1.2 — Pairs Trading Explained
 *
 * Shows how two assets form a tradeable pair, introduces the concept of
 * going long/short simultaneously, and has an interactive P&L simulator.
 */
export function Lesson1_2() {
  // Interactive: user adjusts spread deviation, sees position + P&L
  const [spreadDeviation, setSpreadDeviation] = useState(2);

  // Simulate two "price" series that are cointegrated
  const n = 120;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  // Common trend + individual noise
  const trend = timestamps.map((t) => 100 + t * 0.3 + Math.sin(t / 10) * 5);
  const assetA = trend.map(
    (v, i) => v + Math.sin(i * 0.5) * 3 + Math.sin(i * 127.1 + 311.7) * 1.5
  );
  const assetB = trend.map(
    (v, i) =>
      v * 0.95 +
      5 +
      Math.sin(i * 0.5 + 1) * 3 +
      Math.sin(i * 269.5 + 183.3) * 1.5
  );

  // Calculate simple spread
  const spread = assetA.map((a, i) => a - assetB[i]);
  const spreadMean = spread.reduce((s, v) => s + v, 0) / spread.length;
  const spreadStd = Math.sqrt(
    spread.reduce((s, v) => s + (v - spreadMean) ** 2, 0) / spread.length
  );

  // P&L calculation for the interactive section
  const entrySpread = spreadMean + spreadDeviation * spreadStd;
  const exitSpread = spreadMean;
  const profit = entrySpread - exitSpread;

  return (
    <Stack gap="xl">
      {/* How pairs trading works */}
      <Card padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Title order={4}>How Pairs Trading Works</Title>
          <Text>
            <GlossaryLink term="Pairs Trading" /> is the most common form of stat arb.
            The idea is simple: find two assets that historically move together, wait
            for them to diverge, then bet on convergence.
          </Text>

          <Timeline active={3} bulletSize={28} lineWidth={2} mt="md">
            <Timeline.Item
              bullet={<Text size="xs" fw={700}>1</Text>}
              title="Find a pair"
            >
              <Text size="sm" c="dimmed">
                Identify two assets with a stable long-run relationship.
                In crypto, this might be ETH and ETC — both Ethereum-based,
                influenced by similar market forces.
              </Text>
            </Timeline.Item>
            <Timeline.Item
              bullet={<Text size="xs" fw={700}>2</Text>}
              title="Wait for divergence"
            >
              <Text size="sm" c="dimmed">
                Monitor the price gap (the{' '}
                <GlossaryLink term="Spread">spread</GlossaryLink>). When it
                becomes unusually wide — say 2 standard deviations from the mean —
                that&apos;s your signal.
              </Text>
            </Timeline.Item>
            <Timeline.Item
              bullet={<Text size="xs" fw={700}>3</Text>}
              title="Open both sides"
            >
              <Text size="sm" c="dimmed">
                <strong>Short</strong> the outperformer (sell high) and{' '}
                <strong>long</strong> the underperformer (buy low). You&apos;re now
                market-neutral — if both crash, your short offsets your long.
              </Text>
            </Timeline.Item>
            <Timeline.Item
              bullet={<Text size="xs" fw={700}>4</Text>}
              title="Close on convergence"
            >
              <Text size="sm" c="dimmed">
                When the spread reverts to normal, close both positions. The
                profit comes from the gap narrowing, regardless of market direction.
              </Text>
            </Timeline.Item>
          </Timeline>
        </Stack>
      </Card>

      {/* Visual: two assets moving together */}
      <Card padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Title order={4}>Two Assets, One Relationship</Title>
          <Text size="sm" c="dimmed">
            These two simulated crypto assets share a common trend but diverge
            temporarily. Notice how the gap between them keeps opening and
            closing — each divergence is a potential trade.
          </Text>
          <PlotlyChart
            data={[
              {
                x: timestamps,
                y: assetA,
                type: 'scatter',
                mode: 'lines',
                name: 'Asset A',
                line: { color: '#339AF0', width: 2 },
              },
              {
                x: timestamps,
                y: assetB,
                type: 'scatter',
                mode: 'lines',
                name: 'Asset B',
                line: { color: '#51CF66', width: 2 },
              },
            ]}
            layout={{
              title: 'Two Related Assets Over Time',
              xaxis: { title: { text: 'Time' } },
              yaxis: { title: { text: 'Price (€)' } },
              height: 300,
              showlegend: true,
              legend: { x: 0, y: 1.15, orientation: 'h' },
            }}
          />
        </Stack>
      </Card>

      {/* Interactive P&L simulator */}
      <Card padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Title order={4}>Try it: Your First Pairs Trade</Title>
          <Text size="sm" c="dimmed">
            Adjust how wide the spread gets before you enter a trade. A wider
            entry means more profit per trade, but fewer opportunities.
          </Text>

          <Box>
            <Text size="sm" fw={600} mb="xs">
              Entry at {spreadDeviation.toFixed(1)}σ from the mean
            </Text>
            <Slider
              value={spreadDeviation}
              onChange={setSpreadDeviation}
              min={0.5}
              max={3.5}
              step={0.1}
              marks={[
                { value: 1, label: '1σ' },
                { value: 2, label: '2σ' },
                { value: 3, label: '3σ' },
              ]}
              label={(v) => `${v.toFixed(1)}σ`}
            />
          </Box>

          <Group grow mt="md">
            <Card padding="md" withBorder bg="dark.6">
              <Group gap="xs" mb={4}>
                <ThemeIcon size="sm" variant="light" color="red">
                  <IconArrowDown size={14} />
                </ThemeIcon>
                <Text size="sm" fw={600}>
                  Short (Sell) Asset A
                </Text>
              </Group>
              <Text size="xs" c="dimmed">
                at €{(100 + spreadDeviation * spreadStd / 2).toFixed(2)} — the outperformer
              </Text>
            </Card>
            <Card padding="md" withBorder bg="dark.6">
              <Group gap="xs" mb={4}>
                <ThemeIcon size="sm" variant="light" color="green">
                  <IconArrowUp size={14} />
                </ThemeIcon>
                <Text size="sm" fw={600}>
                  Long (Buy) Asset B
                </Text>
              </Group>
              <Text size="xs" c="dimmed">
                at €{(100 - spreadDeviation * spreadStd / 2).toFixed(2)} — the underperformer
              </Text>
            </Card>
          </Group>

          <Card padding="md" withBorder bg="dark.6">
            <Group gap="xs" mb={4}>
              <ThemeIcon size="sm" variant="light" color="yellow">
                <IconCash size={14} />
              </ThemeIcon>
              <Text size="sm" fw={600}>
                Profit when spread reverts to mean
              </Text>
            </Group>
            <Text size="lg" fw={700} c={profit > 0 ? 'green' : 'red'}>
              €{profit.toFixed(2)} per unit
            </Text>
            <Text size="xs" c="dimmed">
              The wider you wait, the more you make — but the rarer the opportunity.
            </Text>
          </Card>
        </Stack>
      </Card>

      {/* Key takeaway */}
      <Alert
        variant="light"
        color="blue"
        title="Key Takeaway"
        icon={<IconBulb size={20} />}
      >
        <Text size="sm">
          Pairs trading is <strong>market-neutral</strong>: you profit from the spread
          between two assets, not from market direction. You always hold two opposing
          positions. The challenge is finding pairs where the spread reliably reverts.
          Next up: let&apos;s look at <em>real</em> crypto data and see this in action.
        </Text>
      </Alert>
    </Stack>
  );
}
