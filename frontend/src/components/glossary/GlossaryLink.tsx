'use client';

import type { ReactNode } from 'react';
import { Text, Tooltip } from '@mantine/core';
import { GLOSSARY_TERMS } from '@/lib/glossary';

interface GlossaryLinkProps {
  term: string;
  children?: ReactNode;
}

/**
 * Inline glossary term with hover tooltip showing the definition.
 *
 * Stays in the lesson flow — no page navigation.
 */
export function GlossaryLink({ term, children }: GlossaryLinkProps) {
  const entry = GLOSSARY_TERMS.find(
    (e) => e.term.toLowerCase() === term.toLowerCase()
  );

  const definition = entry?.definition ?? 'Definition not found.';

  return (
    <Tooltip
      label={definition}
      multiline
      w={320}
      withArrow
      position="top"
      color="dark.6"
      transitionProps={{ transition: 'fade', duration: 150 }}
    >
      <Text
        component="span"
        c="blue.4"
        style={{
          cursor: 'help',
          borderBottom: '1px dotted var(--mantine-color-blue-5)',
        }}
      >
        {children ?? term}
      </Text>
    </Tooltip>
  );
}
