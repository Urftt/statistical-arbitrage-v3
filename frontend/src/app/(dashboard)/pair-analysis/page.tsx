'use client';

import { Suspense, useEffect } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { Container, Stack, Tabs, Text, Title } from '@mantine/core';
import {
  IconChartHistogram,
  IconMicroscope,
  IconChartLine,
  IconAdjustments,
} from '@tabler/icons-react';
import { usePairContext } from '@/contexts/PairContext';
import StatisticsTab from '@/components/pair-analysis/StatisticsTab';
import BacktestTab from '@/components/pair-analysis/BacktestTab';

// ---------------------------------------------------------------------------

function PairAnalysisContent() {
  const { asset1, asset2, setAsset1, setAsset2, setTimeframe } =
    usePairContext();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // D-03: hydrate PairContext from URL params on initial mount (deep linking support)
  useEffect(() => {
    const urlAsset1 = searchParams.get('asset1');
    const urlAsset2 = searchParams.get('asset2');
    const urlTimeframe = searchParams.get('timeframe');
    if (urlAsset1) setAsset1(urlAsset1);
    if (urlAsset2) setAsset2(urlAsset2);
    if (urlTimeframe) setTimeframe(urlTimeframe);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const tab = searchParams.get('tab') ?? 'statistics';

  function handleTabChange(value: string | null) {
    if (!value) return;
    const params = new URLSearchParams(searchParams.toString());
    params.set('tab', value);
    router.replace(pathname + '?' + params.toString());
  }

  if (!asset1 && !asset2) {
    return (
      <>
        <Title order={2} c="dimmed">
          Select a pair to begin
        </Title>
        <Text c="dimmed">
          Use the Asset 1 and Asset 2 dropdowns in the header, or click a row in
          the Scanner.
        </Text>
      </>
    );
  }

  return (
    <>
      <Title order={2}>
        {asset1} / {asset2}
      </Title>
      <Tabs
        // D-07: remount all tab content when pair changes to clear stale results
        key={`${asset1}-${asset2}`}
        value={tab}
        onChange={handleTabChange}
        variant="pills"
      >
        <Tabs.List mb="md">
          <Tabs.Tab
            value="statistics"
            leftSection={<IconChartHistogram size={16} stroke={1.5} />}
          >
            Statistics
          </Tabs.Tab>
          <Tabs.Tab
            value="research"
            leftSection={<IconMicroscope size={16} stroke={1.5} />}
          >
            Research
          </Tabs.Tab>
          <Tabs.Tab
            value="backtest"
            leftSection={<IconChartLine size={16} stroke={1.5} />}
          >
            Backtest
          </Tabs.Tab>
          <Tabs.Tab
            value="optimize"
            leftSection={<IconAdjustments size={16} stroke={1.5} />}
          >
            Optimize
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="statistics" pt="md">
          <StatisticsTab />
        </Tabs.Panel>
        <Tabs.Panel value="research" pt="md">
          <Text c="dimmed">Research — coming in Phase 4</Text>
        </Tabs.Panel>
        <Tabs.Panel value="backtest" pt="md">
          <BacktestTab />
        </Tabs.Panel>
        <Tabs.Panel value="optimize" pt="md">
          <Text c="dimmed">Optimize — coming in Phase 5</Text>
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

// ---------------------------------------------------------------------------

export default function PairAnalysisPage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="lg">
        <Suspense fallback={<Text c="dimmed">Loading...</Text>}>
          <PairAnalysisContent />
        </Suspense>
      </Stack>
    </Container>
  );
}
