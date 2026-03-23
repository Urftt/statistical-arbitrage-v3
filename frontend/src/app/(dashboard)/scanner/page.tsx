'use client';

import { Container, Title, Text, Stack } from '@mantine/core';

export default function ScannerPage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="md">
        <Title order={1}>Pair Scanner</Title>
        <Text c="dimmed">
          Batch cointegration scanning across available pairs. Coming soon.
        </Text>
      </Stack>
    </Container>
  );
}
