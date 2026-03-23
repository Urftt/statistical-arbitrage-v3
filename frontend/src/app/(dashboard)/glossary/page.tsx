'use client';

import { useState } from 'react';
import {
  Container,
  Title,
  Text,
  TextInput,
  Stack,
  Card,
  Badge,
  Group,
} from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import {
  GLOSSARY_TERMS,
  getGlossaryId,
  getGlossaryAliases,
  glossaryMatchesQuery,
} from '@/lib/glossary';

export default function GlossaryPage() {
  const [query, setQuery] = useState('');

  const filtered = GLOSSARY_TERMS.filter((entry) =>
    glossaryMatchesQuery(entry, query)
  );

  return (
    <Container size="xl" py="md">
      <Stack gap="lg">
        <Title order={1}>Glossary</Title>
        <Text c="dimmed">
          Key terms and concepts used throughout the platform.
        </Text>

        <TextInput
          placeholder="Search terms..."
          leftSection={<IconSearch size={16} />}
          value={query}
          onChange={(e) => setQuery(e.currentTarget.value)}
        />

        {filtered.map((entry) => {
          const aliases = getGlossaryAliases(entry);
          return (
            <Card
              key={entry.term}
              id={getGlossaryId(entry)}
              padding="lg"
              radius="sm"
              withBorder
              data-glossary-card
            >
              <Group gap="sm" mb="xs">
                <Text fw={700} size="lg">
                  {entry.term}
                </Text>
                {aliases.map((alias) => (
                  <Badge key={alias} variant="light" size="sm">
                    {alias}
                  </Badge>
                ))}
              </Group>
              <Text size="sm" c="dimmed">
                {entry.definition}
              </Text>
            </Card>
          );
        })}

        {filtered.length === 0 && (
          <Text c="dimmed" ta="center" py="xl">
            No terms match your search.
          </Text>
        )}
      </Stack>
    </Container>
  );
}
