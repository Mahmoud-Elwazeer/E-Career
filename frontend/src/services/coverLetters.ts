/**
 * Cover Letter API service.
 * Wraps the existing (previously frontend-less) backend endpoints under
 * /career/. Response bodies here are NOT envelope-wrapped, so apiRequest
 * returns them directly.
 */
import { apiRequest } from "./client";

export interface CoverLetterListItem {
  id: string;
  job_id: string;
  job_title: string;
  company: string;
  tone: string;
  word_count: number;
  version: number;
  is_edited: boolean;
  created_at: string;
}

export interface CoverLetterDetail extends CoverLetterListItem {
  content: string;
  confidence: number;
  updated_at?: string;
}

export interface GenerateResult {
  id: string;
  content: string;
  tone: string;
  confidence: number;
  word_count: number;
  version: number;
  created_at: string;
  message?: string;
}

export type CoverLetterTone = "professional" | "enthusiastic" | "formal";

export async function listCoverLetters(): Promise<CoverLetterListItem[]> {
  const res = await apiRequest<{ cover_letters: CoverLetterListItem[]; total: number }>(
    "/career/cover-letters/"
  );
  return res?.cover_letters ?? [];
}

export async function generateCoverLetter(
  jobId: string,
  tone: CoverLetterTone = "professional",
  regenerate = false
): Promise<GenerateResult> {
  return apiRequest<GenerateResult>(`/career/cover-letter/${jobId}/`, {
    method: "POST",
    body: { tone, regenerate },
  });
}

export async function getCoverLetter(id: string): Promise<CoverLetterDetail> {
  return apiRequest<CoverLetterDetail>(`/career/cover-letter/${id}/detail/`);
}

export async function updateCoverLetter(id: string, content: string): Promise<CoverLetterDetail> {
  return apiRequest<CoverLetterDetail>(`/career/cover-letter/${id}/detail/`, {
    method: "PATCH",
    body: { content },
  });
}

export async function deleteCoverLetter(id: string): Promise<void> {
  await apiRequest(`/career/cover-letter/${id}/detail/`, { method: "DELETE" });
}
