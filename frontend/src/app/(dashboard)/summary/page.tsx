'use client';

import { Container, Title, Text, Stack } from '@mantine/core';

export default function SummaryPage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="md">
        <Title order={1}>Research Summary</Title>
        <Text c="dimmed">
          Aggregate findings from all research modules. Compare pairs and run comprehensive backtests. Coming soon.
        </Text>
      </Stack>
    </Container>
  );
}
