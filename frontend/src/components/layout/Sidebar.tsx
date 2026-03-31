'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Box, Divider, NavLink, Stack, Text } from '@mantine/core';
import {
  IconMicroscope,
  IconSchool,
  IconSearch,
  IconVocabulary,
} from '@tabler/icons-react';

const ACADEMY_ITEMS = [
  {
    label: 'Academy',
    href: '/academy',
    icon: IconSchool,
    description: 'Learn stat arb step by step',
  },
] as const;

const RESEARCH_ITEMS = [
  {
    label: 'Scanner',
    href: '/scanner',
    icon: IconSearch,
    description: 'Batch cointegration scan',
  },
  {
    label: 'Pair Analysis',
    href: '/pair-analysis',
    icon: IconMicroscope,
    description: 'Statistics, research, backtest, optimize',
  },
] as const;

const OTHER_ITEMS = [
  {
    label: 'Glossary',
    href: '/glossary',
    icon: IconVocabulary,
    description: 'Stat arb terms',
  },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <Stack gap={0} p="sm" style={{ height: '100%' }}>
      <Text size="xs" fw={700} c="dimmed" tt="uppercase" px="sm" py={4}>
        Academy
      </Text>
      {ACADEMY_ITEMS.map((item) => (
        <NavLink
          key={item.href}
          component={Link}
          href={item.href}
          label={item.label}
          description={item.description}
          leftSection={<item.icon size={18} stroke={1.5} />}
          active={pathname.startsWith(item.href)}
          variant="light"
        />
      ))}

      <Divider my="xs" />

      <Text size="xs" fw={700} c="dimmed" tt="uppercase" px="sm" py={4}>
        Research & Backtesting
      </Text>
      {RESEARCH_ITEMS.map((item) => (
        <NavLink
          key={item.href}
          component={Link}
          href={item.href}
          label={item.label}
          description={item.description}
          leftSection={<item.icon size={18} stroke={1.5} />}
          active={pathname.startsWith(item.href)}
          variant="light"
        />
      ))}

      <Divider my="xs" />

      {OTHER_ITEMS.map((item) => (
        <NavLink
          key={item.href}
          component={Link}
          href={item.href}
          label={item.label}
          description={item.description}
          leftSection={<item.icon size={18} stroke={1.5} />}
          active={pathname === item.href}
          variant="light"
        />
      ))}

      <Box style={{ flex: 1 }} />

      <Divider my="xs" />

      <Text size="xs" c="dimmed" ta="center" py="xs">
        StatArb v3
      </Text>
    </Stack>
  );
}
