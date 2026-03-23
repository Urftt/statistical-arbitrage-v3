'use client';

import { Container, Title, Text, Stack } from '@mantine/core';

export default function AcademyPage() {
  return (
    <Container size="xl" py="md">
      <Stack gap="md">
        <Title order={1}>Academy</Title>
        <Text c="dimmed">
          Learn statistical arbitrage step by step — from the big idea to
          validating your first strategy. Coming soon.
        </Text>
      </Stack>
    </Container>
  );
}
