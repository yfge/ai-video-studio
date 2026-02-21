/**
 * Story novel export type definitions.
 */

export type StoryNovelExportRequest = {
  style?: "zhihu";
  target_words: number;
  chapter_count?: number;
  model?: string;
  temperature?: number;
};

export type StoryNovelExportSummary = {
  id: number;
  business_id: string;
  task_id: number | null;
  style: string;
  target_words: number;
  chapter_count: number | null;
  total_words: number | null;
  model: string | null;
  temperature: number | null;
  file_relative_path: string | null;
  created_at: string;
};

export type StoryNovelDownloadResult = {
  blob: Blob;
  filename: string | null;
};

export type StoryNovelTextResult = {
  text: string;
  filename: string | null;
};
