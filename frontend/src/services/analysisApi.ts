import type { EDAResult, FullAnalysisResult } from '../types/analysis';
import { postForm } from './apiClient';

export async function runEDA(
  file: File,
  target?: string,
): Promise<EDAResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (target) formData.append('target', target);
  return postForm<EDAResult>('/eda', formData);
}

export async function runSingleAgent(
  file: File,
  target?: string,
  model?: string,
  ollamaUrl?: string,
): Promise<FullAnalysisResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (target) formData.append('target', target);
  if (model) formData.append('model', model);
  if (ollamaUrl) formData.append('ollama_url', ollamaUrl);
  return postForm<FullAnalysisResult>('/analyze/single-agent', formData);
}

export async function runMultiAgent(
  file: File,
  target?: string,
  model?: string,
  ollamaUrl?: string,
): Promise<FullAnalysisResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (target) formData.append('target', target);
  if (model) formData.append('model', model);
  if (ollamaUrl) formData.append('ollama_url', ollamaUrl);
  return postForm<FullAnalysisResult>('/analyze/multi-agent', formData);
}
