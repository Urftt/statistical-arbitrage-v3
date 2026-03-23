'use client';

import { Container, Title, Text, Stack } from '@mantine/core';

export default function BacktestPage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="md">
        <Title order={1}>Backtest</Title>
        <Text c="dimmed">
          Run your z-score mean-reversion strategy over historical data. Coming soon.
        </Text>
      </Stack>
    </Container>
  );
}
