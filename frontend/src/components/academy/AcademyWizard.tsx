'use client';

import { useState, useCallback, useEffect, useRef, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Group,
  Menu,
  Paper,
  Progress,
  Stack,
  Text,
  Title,
  Stepper,
} from '@mantine/core';
import {
  Badge,
  Loader,
} from '@mantine/core';
import {
  IconArrowLeft,
  IconArrowRight,
  IconCheck,
  IconChevronDown,
  IconDatabase,
  IconRocket,
} from '@tabler/icons-react';
import {
  CHAPTERS,
  TOTAL_LESSONS,
  getLessonByFlatIndex,
} from '@/lib/academy';
import { useAcademyData } from '@/contexts/AcademyDataContext';

interface AcademyWizardProps {
  renderLesson: (lessonId: string) => ReactNode;
}

export function AcademyWizard({ renderLesson }: AcademyWizardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const topRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { goodPair, badPair, loading: dataLoading, ready: dataReady, refresh: loadData } = useAcademyData();

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

  // Flat index of the first lesson in the current chapter
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

  const goToChapter = useCallback((chapterNumber: number) => {
    let idx = 0;
    for (const ch of CHAPTERS) {
      if (ch.number === chapterNumber) {
        setCurrentIndex(idx);
        return;
      }
      idx += ch.lessons.length;
    }
  }, []);

  const handleComplete = useCallback(() => {
    router.push('/scanner');
  }, [router]);

  return (
    <Stack gap="lg" ref={topRef}>
      {/* Progress header */}
      <Paper p="md" radius="sm" withBorder>
        <Group justify="space-between" mb="xs">
          {/* Chapter selector dropdown */}
          <Menu shadow="md" width={320} position="bottom-start">
            <Menu.Target>
              <Button
                variant="subtle"
                size="compact-sm"
                rightSection={<IconChevronDown size={14} />}
                styles={{
                  root: { fontWeight: 600, paddingLeft: 0 },
                }}
                c="dimmed"
              >
                Chapter {chapter.number}: {chapter.title}
              </Button>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>Jump to chapter</Menu.Label>
              {CHAPTERS.map((ch) => (
                <Menu.Item
                  key={ch.number}
                  onClick={() => goToChapter(ch.number)}
                  fw={ch.number === chapter.number ? 700 : 400}
                  c={ch.number === chapter.number ? 'blue.4' : undefined}
                  leftSection={
                    <Text size="xs" fw={700} c="dimmed" w={20}>
                      {ch.number}
                    </Text>
                  }
                >
                  <div>
                    <Text size="sm">{ch.title}</Text>
                    <Text size="xs" c="dimmed">
                      {ch.description} ({ch.lessons.length} lessons)
                    </Text>
                  </div>
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>

          <Text size="sm" c="dimmed">
            {currentIndex + 1} / {TOTAL_LESSONS}
          </Text>
        </Group>
        <Progress value={progressPct} size="sm" radius="xl" />

        {/* Real data status */}
        <Group gap="xs" mt="xs">
          {!dataReady && !dataLoading && (
            <Button
              variant="light"
              size="compact-xs"
              leftSection={<IconDatabase size={12} />}
              onClick={loadData}
            >
              Load live data
            </Button>
          )}
          {dataLoading && (
            <Group gap="xs">
              <Loader size={12} />
              <Text size="xs" c="dimmed">Fetching live data from Bitvavo...</Text>
            </Group>
          )}
          {dataReady && goodPair && (
            <Group gap="xs">
              <Badge size="xs" color="teal" variant="light">
                {goodPair.pair.label}
              </Badge>
              {badPair && (
                <Badge size="xs" color="red" variant="light">
                  {badPair.pair.label}
                </Badge>
              )}
              <Text size="xs" c="dimmed">following through all lessons</Text>
            </Group>
          )}
        </Group>

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
              allowStepSelect
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
        {isLast ? (
          <Button
            rightSection={<IconRocket size={16} />}
            onClick={handleComplete}
            variant="gradient"
            gradient={{ from: 'blue', to: 'cyan' }}
          >
            Start Research
          </Button>
        ) : (
          <Button
            rightSection={<IconArrowRight size={16} />}
            onClick={goNext}
          >
            Next
          </Button>
        )}
      </Group>
    </Stack>
  );
}
