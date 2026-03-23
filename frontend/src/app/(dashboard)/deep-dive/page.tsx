'use client';

import { Container, Title, Text, Stack } from '@mantine/core';

export default function DeepDivePage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="md">
        <Title order={1}>Pair Deep Dive</Title>
        <Text c="dimmed">
          Full analysis of a single pair — cointegration, spread, z-score, and more. Coming soon.
        </Text>
      </Stack>
    </Container>
  );
}
