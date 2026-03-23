'use client';

import { Container, Title, Text, Stack } from '@mantine/core';

export default function OptimizePage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="md">
        <Title order={1}>Optimize</Title>
        <Text c="dimmed">
          Grid search and walk-forward analysis for parameter optimization. Coming soon.
        </Text>
      </Stack>
    </Container>
  );
}
