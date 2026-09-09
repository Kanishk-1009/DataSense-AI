import type { DatasetProfile } from '../types/dataset';
import type { EvaluationResult } from '../types/evaluation';
import { postForm } from './apiClient';

export async function uploadDataset(file: File): Promise<DatasetProfile> {
  const formData = new FormData();
  formData.append('file', file);
  return postForm<DatasetProfile>('/upload', formData);
}

export async function runEvaluation(
  file: File,
  target?: string,
  model?: string,
  ollamaUrl?: string,
): Promise<EvaluationResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (target) formData.append('target', target);
  if (model) formData.append('model', model);
  if (ollamaUrl) formData.append('ollama_url', ollamaUrl);
  return postForm<EvaluationResult>('/evaluate', formData);
}
