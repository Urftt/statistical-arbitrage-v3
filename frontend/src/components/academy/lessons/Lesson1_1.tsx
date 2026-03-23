'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Card,
  Group,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
  SegmentedControl,
} from '@mantine/core';
import {
  IconBulb,
  IconArrowsExchange,
  IconChartLine,
  IconShieldCheck,
} from '@tabler/icons-react';
import { GlossaryLink } from '@/components/glossary/GlossaryLink';
import PlotlyChart from '@/components/charts/PlotlyChart';

/**
 * Lesson 1.1 — What is Statistical Arbitrage?
 *
 * Teaches the core concept through a real-world analogy (two coffee shops)
 * and an interactive price simulation that shows mean reversion visually.
 */
export function Lesson1_1() {
  const [scenario, setScenario] = useState<string>('revert');

  // Generate a simple simulated spread to show mean reversion vs random walk
  const n = 100;
  const timestamps = Array.from({ length: n }, (_, i) => i);

  // Mean-reverting spread (Ornstein-Uhlenbeck-like)
  const revertingSpread: number[] = [0];
  const randomSpread: number[] = [0];

  // Use deterministic seed-like sequence for reproducibility
  const pseudoRandom = (i: number) =>
    Math.sin(i * 127.1 + 311.7) * 0.5;

  for (let i = 1; i < n; i++) {
    const noise = pseudoRandom(i);
    // Mean-reverting: pulled back toward 0
    revertingSpread.push(
      revertingSpread[i - 1] * 0.9 + noise
    );
    // Random walk: no pull-back
    randomSpread.push(randomSpread[i - 1] + noise * 0.3);
  }

  const spread = scenario === 'revert' ? revertingSpread : randomSpread;

  return (
    <Stack gap="xl">
      {/* The analogy */}
      <Card padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group gap="sm">
            <ThemeIcon size="lg" variant="light" color="blue">
              <IconBulb size={20} />
            </ThemeIcon>
            <Title order={4}>The Coffee Shop Analogy</Title>
          </Group>
          <Text>
            Imagine two coffee shops on the same street. On most days, a latte costs
            roughly the same at both — say, around €4. Sometimes Shop A charges €4.50
            while Shop B charges €3.80. The <strong>gap</strong> between their prices
            wobbles around, but it always comes back to roughly zero.
          </Text>
          <Text>
            Now imagine you could <strong>sell</strong> at the expensive shop and{' '}
            <strong>buy</strong> at the cheap one whenever the gap gets unusually wide.
            When it snaps back to normal, you pocket the difference.
          </Text>
          <Text fw={600}>
            That&apos;s{' '}
            <GlossaryLink term="Statistical Arbitrage">
              statistical arbitrage
            </GlossaryLink>{' '}
            in a nutshell — profiting from temporary mispricings between related assets
            that tend to revert to a historical norm.
          </Text>
        </Stack>
      </Card>

      {/* Key properties */}
      <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
        <Card padding="md" radius="sm" withBorder>
          <Group gap="sm" mb="xs">
            <ThemeIcon size="md" variant="light" color="teal">
              <IconArrowsExchange size={16} />
            </ThemeIcon>
            <Text fw={600} size="sm">
              Mean Reversion
            </Text>
          </Group>
          <Text size="sm" c="dimmed">
            The price gap between related assets tends to return to its average over
            time. This is the core bet:{' '}
            <GlossaryLink term="Mean Reversion">what goes up, comes back down</GlossaryLink>.
          </Text>
        </Card>
        <Card padding="md" radius="sm" withBorder>
          <Group gap="sm" mb="xs">
            <ThemeIcon size="md" variant="light" color="violet">
              <IconChartLine size={16} />
            </ThemeIcon>
            <Text fw={600} size="sm">
              Statistical, Not Risk-Free
            </Text>
          </Group>
          <Text size="sm" c="dimmed">
            Unlike true arbitrage (guaranteed profit), stat arb relies on
            historical patterns that <em>might</em> not hold. The &quot;statistical&quot;
            part means we&apos;re betting on probabilities.
          </Text>
        </Card>
        <Card padding="md" radius="sm" withBorder>
          <Group gap="sm" mb="xs">
            <ThemeIcon size="md" variant="light" color="orange">
              <IconShieldCheck size={16} />
            </ThemeIcon>
            <Text fw={600} size="sm">
              Market Neutral
            </Text>
          </Group>
          <Text size="sm" c="dimmed">
            By going long one asset and short the other, you&apos;re hedged against
            the overall market direction. You profit from the{' '}
            <em>relationship</em>, not the trend.
          </Text>
        </Card>
      </SimpleGrid>

      {/* Interactive chart */}
      <Card padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group justify="space-between">
            <Title order={4}>Try it: Mean Reversion vs. Random Walk</Title>
            <SegmentedControl
              value={scenario}
              onChange={setScenario}
              data={[
                { label: 'Mean-Reverting', value: 'revert' },
                { label: 'Random Walk', value: 'random' },
              ]}
              size="sm"
            />
          </Group>
          <Text size="sm" c="dimmed">
            Toggle between a <strong>mean-reverting</strong> spread (what we want for
            trading) and a <strong>random walk</strong> (unpredictable). Notice how the
            mean-reverting spread keeps returning to zero — that&apos;s what makes it
            tradeable.
          </Text>
          <PlotlyChart
            data={[
              {
                x: timestamps,
                y: spread,
                type: 'scatter',
                mode: 'lines',
                name: scenario === 'revert' ? 'Mean-reverting spread' : 'Random walk',
                line: {
                  color: scenario === 'revert' ? '#339AF0' : '#FF6B6B',
                  width: 2,
                },
              },
              {
                x: [0, n - 1],
                y: [0, 0],
                type: 'scatter',
                mode: 'lines',
                name: 'Mean (zero)',
                line: { color: '#909296', width: 1, dash: 'dash' },
              },
            ]}
            layout={{
              title: scenario === 'revert'
                ? 'Mean-Reverting Spread — Always Pulled Back to Zero'
                : 'Random Walk — No Pull-Back, Wanders Freely',
              xaxis: { title: { text: 'Time' } },
              yaxis: { title: { text: 'Spread Value' } },
              height: 350,
              showlegend: true,
              legend: { x: 0, y: 1.15, orientation: 'h' },
            }}
          />
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
          Statistical arbitrage profits from <strong>temporary deviations</strong>{' '}
          in the price relationship between two related assets. The key requirement
          is that this relationship is <strong>mean-reverting</strong> — the gap
          always comes back. In the next lesson, we&apos;ll see how{' '}
          <GlossaryLink term="Pairs Trading">pairs trading</GlossaryLink>{' '}
          puts this idea into practice.
        </Text>
      </Alert>
    </Stack>
  );
}
