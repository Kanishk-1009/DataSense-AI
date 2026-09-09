import type { AgentResponse } from '../types/analysis';
import { postForm } from './apiClient';

export async function sendChatMessage(
  file: File,
  _message: string,
  target?: string,
): Promise<AgentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (target) formData.append('target', target);
  return postForm<AgentResponse>('/analyze/single-agent', formData);
}
