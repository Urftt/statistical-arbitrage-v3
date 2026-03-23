'use client';

import { Container, Title, Text, Stack } from '@mantine/core';

export default function ResearchPage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="md">
        <Title order={1}>Research</Title>
        <Text c="dimmed">
          8 research modules to test parameters and validate your strategy. Coming soon.
        </Text>
      </Stack>
    </Container>
  );
}
