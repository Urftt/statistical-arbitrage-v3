'use client';

import { Container, Text } from '@mantine/core';
import { AcademyWizard } from '@/components/academy/AcademyWizard';
import {
  Lesson1_1,
  Lesson1_2,
  Lesson1_3,
  Lesson2_1,
  Lesson2_2,
  Lesson2_3,
  Lesson2_4,
} from '@/components/academy/lessons';

/** Map lesson IDs to their content components. */
function renderLesson(lessonId: string) {
  switch (lessonId) {
    case '1.1':
      return <Lesson1_1 />;
    case '1.2':
      return <Lesson1_2 />;
    case '1.3':
      return <Lesson1_3 />;
    case '2.1':
      return <Lesson2_1 />;
    case '2.2':
      return <Lesson2_2 />;
    case '2.3':
      return <Lesson2_3 />;
    case '2.4':
      return <Lesson2_4 />;
    default:
      return (
        <Text c="dimmed" py="xl" ta="center">
          This lesson is coming soon. Continue to the next available lesson.
        </Text>
      );
  }
}

export default function AcademyPage() {
  return (
    <Container size="lg" py="md">
      <AcademyWizard renderLesson={renderLesson} />
    </Container>
  );
}
