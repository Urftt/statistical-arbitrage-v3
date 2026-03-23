'use client';

import { useState, useCallback, useEffect, useRef, type ReactNode } from 'react';
import {
  Box,
  Button,
  Group,
  Paper,
  Progress,
  Stack,
  Text,
  Title,
  Stepper,
} from '@mantine/core';
import { IconArrowLeft, IconArrowRight, IconCheck } from '@tabler/icons-react';
import { CHAPTERS, TOTAL_LESSONS, getLessonByFlatIndex, getLessonFlatIndex } from '@/lib/academy';

interface AcademyWizardProps {
  renderLesson: (lessonId: string) => ReactNode;
}

export function AcademyWizard({ renderLesson }: AcademyWizardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const topRef = useRef<HTMLDivElement>(null);

  const info = getLessonByFlatIndex(currentIndex);
  if (!info) return null;

  const { chapter, lesson, lessonIndex } = info;
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === TOTAL_LESSONS - 1;
  const progressPct = ((currentIndex + 1) / TOTAL_LESSONS) * 100;

  // Scroll to top when lesson changes
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    topRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [currentIndex]);

  // Calculate the flat index of the first lesson in the current chapter
  const chapterStartIndex = (() => {
    let idx = 0;
    for (const ch of CHAPTERS) {
      if (ch.number === chapter.number) return idx;
      idx += ch.lessons.length;
    }
    return 0;
  })();

  const goNext = useCallback(() => {
    setCurrentIndex((i) => Math.min(i + 1, TOTAL_LESSONS - 1));
  }, []);

  const goBack = useCallback(() => {
    setCurrentIndex((i) => Math.max(i - 1, 0));
  }, []);

  const goToStep = useCallback(
    (stepIndex: number) => {
      setCurrentIndex(chapterStartIndex + stepIndex);
    },
    [chapterStartIndex]
  );

  return (
    <Stack gap="lg" ref={topRef}>
      {/* Progress header */}
      <Paper p="md" radius="sm" withBorder>
        <Group justify="space-between" mb="xs">
          <Text size="sm" fw={600} c="dimmed">
            Chapter {chapter.number}: {chapter.title}
          </Text>
          <Text size="sm" c="dimmed">
            {currentIndex + 1} / {TOTAL_LESSONS}
          </Text>
        </Group>
        <Progress value={progressPct} size="sm" radius="xl" />

        <Stepper
          active={lessonIndex}
          onStepClick={goToStep}
          size="xs"
          mt="md"
          styles={{
            separator: { marginLeft: 2, marginRight: 2 },
            step: { cursor: 'pointer' },
          }}
        >
          {chapter.lessons.map((l) => (
            <Stepper.Step
              key={l.id}
              label={l.title}
              completedIcon={<IconCheck size={14} />}
            />
          ))}
        </Stepper>
      </Paper>

      {/* Lesson title */}
      <Box>
        <Title order={2}>{lesson.title}</Title>
        <Text c="dimmed" size="sm" mt={4}>
          {lesson.subtitle}
        </Text>
      </Box>

      {/* Lesson content */}
      <Box>{renderLesson(lesson.id)}</Box>

      {/* Navigation */}
      <Group justify="space-between" mt="md">
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          onClick={goBack}
          disabled={isFirst}
        >
          Back
        </Button>
        <Button
          rightSection={
            isLast ? <IconCheck size={16} /> : <IconArrowRight size={16} />
          }
          onClick={goNext}
          disabled={isLast}
        >
          {isLast ? 'Complete' : 'Next'}
        </Button>
      </Group>
    </Stack>
  );
}
