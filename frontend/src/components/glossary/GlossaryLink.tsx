import type { ReactNode } from 'react';
import Link from 'next/link';
import { Anchor, type AnchorProps } from '@mantine/core';
import { getGlossaryHref } from '@/lib/glossary';

interface GlossaryLinkProps extends Omit<AnchorProps, 'href' | 'component' | 'children'> {
  term: string;
  children?: ReactNode;
}

/**
 * Inline glossary link that navigates to `/glossary#glossary-{slug}`.
 * Use throughout Academy and Research for clickable term references.
 */
export function GlossaryLink({
  term,
  children,
  fw = 600,
  c = 'blue.3',
  underline = 'always',
  ...anchorProps
}: GlossaryLinkProps) {
  return (
    <Anchor
      component={Link}
      href={getGlossaryHref(term)}
      fw={fw}
      c={c}
      underline={underline}
      style={{ textUnderlineOffset: '3px' }}
      {...anchorProps}
    >
      {children ?? term}
    </Anchor>
  );
}
