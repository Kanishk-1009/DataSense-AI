import { create } from 'zustand/react';
import type { DatasetProfile } from '../types/dataset';
import type { EDAResult } from '../types/analysis';
import type { UploadStage } from '../types/api';
import type { AgentResponse } from '../types/analysis';
import type { EvaluationResult } from '../types/evaluation';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface DatasetState {
  profile: DatasetProfile | null;
  edaResult: EDAResult | null;
  fileName: string | null;
  uploadStage: UploadStage;
  uploadProgress: number;
  agentResult: AgentResponse | null;
  chatMessages: ChatMessage[];
  isChatOpen: boolean;
  evaluationResult: EvaluationResult | null;
  setProfile: (p: DatasetProfile | null) => void;
  setEdaResult: (r: EDAResult | null) => void;
  setFileName: (n: string | null) => void;
  setUploadStage: (s: UploadStage) => void;
  setUploadProgress: (p: number) => void;
  setAgentResult: (r: AgentResponse | null) => void;
  setEvaluationResult: (r: EvaluationResult | null) => void;
  addChatMessage: (m: ChatMessage) => void;
  clearChat: () => void;
  setChatOpen: (open: boolean) => void;
  clearDataset: () => void;
  isLoaded: () => boolean;
}

export const useDatasetStore = create<DatasetState>()((set, get) => ({
  profile: null,
  edaResult: null,
  fileName: null,
  uploadStage: 'idle' as UploadStage,
  uploadProgress: 0,
  agentResult: null,
  chatMessages: [] as ChatMessage[],
  isChatOpen: false,
  evaluationResult: null,

  setProfile: (p: DatasetProfile | null) => set({ profile: p }),
  setEdaResult: (r: EDAResult | null) => set({ edaResult: r }),
  setFileName: (n: string | null) => set({ fileName: n }),
  setUploadStage: (s: UploadStage) => set({ uploadStage: s }),
  setUploadProgress: (p: number) => set({ uploadProgress: p }),
  setAgentResult: (r: AgentResponse | null) => set({ agentResult: r }),
  setEvaluationResult: (r: EvaluationResult | null) => set({ evaluationResult: r }),

  addChatMessage: (m: ChatMessage) =>
    set((state: DatasetState) => ({ chatMessages: [...state.chatMessages, m] })),

  clearChat: () => set({ chatMessages: [] }),

  setChatOpen: (open: boolean) => set({ isChatOpen: open }),

  clearDataset: () =>
    set({
      profile: null,
      edaResult: null,
      fileName: null,
      agentResult: null,
      chatMessages: [],
      evaluationResult: null,
      uploadStage: 'idle' as UploadStage,
      uploadProgress: 0,
    }),

  isLoaded: () => get().profile !== null,
}));
