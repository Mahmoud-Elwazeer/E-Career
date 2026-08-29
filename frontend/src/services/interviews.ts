/**
 * Interviews API service — coding practice endpoints
 */

import { apiRequest } from './client';

// ── Types ────────────────────────────────────────────────────────────────────

export interface CodingProblem {
  title: string;
  description: string;
  examples: Array<{ input: string; output: string }>;
  constraints: string[];
  starter_code: string;
  test_cases: Array<{ input: string; expected: string }>;
  language: string;
  language_name: string;
  difficulty: string;
  topic: string;
}

export interface ExecutionResult {
  success: boolean;
  status?: string;
  output: string | null;
  stderr: string | null;
  error?: string;
  execution_time: number;
  memory: number;
}

export interface EvaluationResult {
  score: number;
  correctness: number;
  efficiency: number;
  style: number;
  suggestions: string[];
  tests_passed: number;
  tests_failed: number;
  total_tests: number;
  execution_time: number;
  memory: number;
}

// ── API functions ────────────────────────────────────────────────────────────

export async function generateCodingProblem(params: {
  difficulty: string;
  language: string;
  topic?: string;
}): Promise<CodingProblem> {
  return apiRequest<CodingProblem>('/interviews/coding-problem/', {
    method: 'POST',
    body: {
      difficulty: params.difficulty,
      language: params.language,
      topic: params.topic ?? 'arrays',
    },
  });
}

export async function submitCodingSolution(params: {
  code: string;
  language: string;
  test_cases?: Array<{ input: string; expected: string }>;
}): Promise<ExecutionResult> {
  return apiRequest<ExecutionResult>('/interviews/coding-solution/', {
    method: 'POST',
    body: {
      code: params.code,
      language: params.language,
      test_cases: params.test_cases ?? [],
    },
  });
}

export async function evaluateCodingSolution(params: {
  code: string;
  language: string;
  problem: CodingProblem;
  execution_result: ExecutionResult;
}): Promise<EvaluationResult> {
  return apiRequest<EvaluationResult>('/interviews/coding-evaluate/', {
    method: 'POST',
    body: {
      code: params.code,
      language: params.language,
      problem: params.problem,
      execution_result: params.execution_result,
    },
  });
}

const interviewsService = {
  generateCodingProblem,
  submitCodingSolution,
  evaluateCodingSolution,
};

export default interviewsService;
