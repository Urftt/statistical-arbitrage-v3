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
  Lesson3_1,
  Lesson3_2,
  Lesson3_3,
  Lesson3_4,
  Lesson4_1,
  Lesson4_2,
  Lesson4_3,
  Lesson4_4,
  Lesson5_1,
  Lesson5_2,
  Lesson5_3,
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
    case '3.1':
      return <Lesson3_1 />;
    case '3.2':
      return <Lesson3_2 />;
    case '3.3':
      return <Lesson3_3 />;
    case '3.4':
      return <Lesson3_4 />;
    case '4.1':
      return <Lesson4_1 />;
    case '4.2':
      return <Lesson4_2 />;
    case '4.3':
      return <Lesson4_3 />;
    case '4.4':
      return <Lesson4_4 />;
    case '5.1':
      return <Lesson5_1 />;
    case '5.2':
      return <Lesson5_2 />;
    case '5.3':
      return <Lesson5_3 />;
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
