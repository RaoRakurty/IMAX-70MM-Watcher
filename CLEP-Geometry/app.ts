export type GeometryDiagram = { type: string; [key: string]: unknown } | null;

export interface GeometryQuestion {
  id: string;
  topic: string;
  level: "Routine" | "Nonroutine";
  stem: string;
  choices: string[];
  answer: number;
  explanation: string;
  diagram: GeometryDiagram;
}

export interface AttemptState {
  startedAt: number;
  currentIndex: number;
  answers: Record<string, number>;
  flags: string[];
  submittedAt?: number;
}

declare global {
  interface Window {
    GEOMETRY_QUESTIONS: GeometryQuestion[];
  }
}

export const TOTAL_QUESTIONS = 32;
export const EXAM_SECONDS = 50 * 60;
export const STORAGE_KEY = "clep-geometry-mastery-v1";

export const questions: GeometryQuestion[] = window.GEOMETRY_QUESTIONS;

export function scoreAttempt(attempt: AttemptState): number {
  return questions.reduce((score, question) =>
    score + (attempt.answers[question.id] === question.answer ? 1 : 0), 0);
}

export function topicBreakdown(attempt: AttemptState) {
  const topics = [...new Set(questions.map(q => q.topic))];
  return topics.map(topic => {
    const group = questions.filter(q => q.topic === topic);
    const correct = group.filter(q => attempt.answers[q.id] === q.answer).length;
    return { topic, correct, total: group.length };
  });
}

// The deployed app.js is the browser-ready compiled/static build used by GitHub Pages.
// This TypeScript source defines the typed data model and scoring contract for the frontend.