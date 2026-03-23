/**
 * Academy curriculum structure.
 *
 * Each chapter contains ordered lessons. The lesson `id` is used in the URL
 * and for progress tracking. Chapters are numbered 1-5, lessons are
 * numbered within their chapter (1.1, 1.2, ...).
 */

export interface Lesson {
  /** Unique identifier, e.g. "1.1" */
  id: string;
  /** Short display title */
  title: string;
  /** One-line description shown in the progress bar */
  subtitle: string;
}

export interface Chapter {
  /** Chapter number (1-based) */
  number: number;
  /** Chapter title */
  title: string;
  /** Short description */
  description: string;
  /** Ordered lessons in this chapter */
  lessons: Lesson[];
}

export const CHAPTERS: readonly Chapter[] = [
  {
    number: 1,
    title: 'The Big Idea',
    description: 'What stat arb is, why it works, and your first look at real data',
    lessons: [
      {
        id: '1.1',
        title: 'What is Statistical Arbitrage?',
        subtitle: 'The core concept and why it works',
      },
      {
        id: '1.2',
        title: 'Pairs Trading Explained',
        subtitle: 'How two assets form a tradeable pair',
      },
      {
        id: '1.3',
        title: 'Your First Look at Real Data',
        subtitle: 'Real crypto prices — do they move together?',
      },
    ],
  },
  {
    number: 2,
    title: 'Finding Pairs',
    description: 'Correlation, cointegration, and how to tell them apart',
    lessons: [
      {
        id: '2.1',
        title: 'Correlation — The Familiar Friend',
        subtitle: 'What it measures and where it falls short',
      },
      {
        id: '2.2',
        title: 'Cointegration — The Real Test',
        subtitle: 'Why the spread matters more than direction',
      },
      {
        id: '2.3',
        title: 'The Engle-Granger Test',
        subtitle: 'Step-by-step cointegration testing',
      },
      {
        id: '2.4',
        title: 'Stationarity & The ADF Test',
        subtitle: 'How to verify the spread mean-reverts',
      },
    ],
  },
  {
    number: 3,
    title: 'The Spread & Signals',
    description: 'Building the spread, z-scores, and generating trade signals',
    lessons: [
      {
        id: '3.1',
        title: 'Building the Spread',
        subtitle: 'Hedge ratio, OLS, and the residual series',
      },
      {
        id: '3.2',
        title: 'Z-Scores — Standardizing the Spread',
        subtitle: 'From raw spread to universal signals',
      },
      {
        id: '3.3',
        title: 'Entry & Exit Signals',
        subtitle: 'When to open and close positions',
      },
      {
        id: '3.4',
        title: 'Half-Life — How Fast Does It Revert?',
        subtitle: 'Measuring mean reversion speed',
      },
    ],
  },
  {
    number: 4,
    title: 'Strategy & Backtesting',
    description: 'Turning signals into a strategy and testing it on historical data',
    lessons: [
      {
        id: '4.1',
        title: 'From Signals to Strategy',
        subtitle: 'Position sizing, capital, and fees',
      },
      {
        id: '4.2',
        title: 'Your First Backtest',
        subtitle: 'Running the strategy on real data',
      },
      {
        id: '4.3',
        title: 'Reading Backtest Results',
        subtitle: 'Metrics that matter: Sharpe, drawdown, win rate',
      },
      {
        id: '4.4',
        title: 'Overfitting — The Silent Killer',
        subtitle: 'Why good backtests can be misleading',
      },
    ],
  },
  {
    number: 5,
    title: 'Putting It All Together',
    description: 'The complete pipeline from pair selection to validated strategy',
    lessons: [
      {
        id: '5.1',
        title: 'The Research Pipeline',
        subtitle: 'Systematic approach to finding good pairs',
      },
      {
        id: '5.2',
        title: 'Optimization & Walk-Forward',
        subtitle: 'Tuning parameters without overfitting',
      },
      {
        id: '5.3',
        title: 'Graduation — Ready for Research',
        subtitle: 'What you know and where to go next',
      },
    ],
  },
] as const;

/** Total number of lessons across all chapters. */
export const TOTAL_LESSONS = CHAPTERS.reduce(
  (sum, ch) => sum + ch.lessons.length,
  0
);

/** Get the flat index (0-based) for a lesson by its id. */
export function getLessonFlatIndex(lessonId: string): number {
  let idx = 0;
  for (const chapter of CHAPTERS) {
    for (const lesson of chapter.lessons) {
      if (lesson.id === lessonId) return idx;
      idx++;
    }
  }
  return -1;
}

/** Get lesson + chapter info by flat index. */
export function getLessonByFlatIndex(
  flatIndex: number
): { chapter: Chapter; lesson: Lesson; lessonIndex: number } | null {
  let idx = 0;
  for (const chapter of CHAPTERS) {
    for (let i = 0; i < chapter.lessons.length; i++) {
      if (idx === flatIndex) {
        return { chapter, lesson: chapter.lessons[i], lessonIndex: i };
      }
      idx++;
    }
  }
  return null;
}

/** Get all lessons in a specific chapter. */
export function getChapterLessons(chapterNumber: number): Lesson[] {
  const chapter = CHAPTERS.find((ch) => ch.number === chapterNumber);
  return chapter?.lessons ?? [];
}
