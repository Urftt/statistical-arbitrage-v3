'use client';

import { useState, useCallback, type ReactNode } from 'react';
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
import { CHAPTERS, TOTAL_LESSONS, getLessonByFlatIndex } from '@/lib/academy';

interface AcademyWizardProps {
  /** Render function for each lesson. Receives the lesson id (e.g. "1.1"). */
  renderLesson: (lessonId: string) => ReactNode;
}

/**
 * Step-by-step wizard that walks through all Academy lessons.
 *
 * Shows a progress bar at the top, chapter/lesson title, content area,
 * and Back/Next navigation buttons.
 */
export function AcademyWizard({ renderLesson }: AcademyWizardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const info = getLessonByFlatIndex(currentIndex);
  if (!info) return null;

  const { chapter, lesson, lessonIndex } = info;
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === TOTAL_LESSONS - 1;
  const progressPct = ((currentIndex + 1) / TOTAL_LESSONS) * 100;

  const goNext = useCallback(() => {
    setCurrentIndex((i) => Math.min(i + 1, TOTAL_LESSONS - 1));
  }, []);

  const goBack = useCallback(() => {
    setCurrentIndex((i) => Math.max(i - 1, 0));
  }, []);

  return (
    <Stack gap="lg">
      {/* Progress header */}
      <Paper p="md" radius="sm" withBorder>
        <Group justify="space-between" mb="xs">
          <Text size="sm" fw={600} c="dimmed">
            Chapter {chapter.number}: {chapter.title}
          </Text>
          <Text size="sm" c="dimmed">
            Lesson {currentIndex + 1} of {TOTAL_LESSONS}
          </Text>
        </Group>
        <Progress value={progressPct} size="sm" radius="xl" animated />

        {/* Chapter lesson stepper */}
        <Stepper
          active={lessonIndex}
          size="xs"
          mt="md"
          styles={{
            separator: { marginLeft: 2, marginRight: 2 },
          }}
        >
          {chapter.lessons.map((l) => (
            <Stepper.Step
              key={l.id}
              label={l.title}
              description={l.subtitle}
              completedIcon={<IconCheck size={14} />}
            />
          ))}
        </Stepper>
      </Paper>

      {/* Lesson title */}
      <Box>
        <Title order={2}>{lesson.title}</Title>
        <Text c="dimmed" mt={4}>
          {lesson.subtitle}
        </Text>
      </Box>

      {/* Lesson content */}
      <Box>{renderLesson(lesson.id)}</Box>

      {/* Navigation */}
      <Group justify="space-between" mt="xl">
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
