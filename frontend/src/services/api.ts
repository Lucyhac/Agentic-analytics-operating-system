import axios from 'axios';

import type { AgentResponse, UploadResponse } from '../types/dataset';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  timeout: 60_000,
});

function getApiErrorMessage(caught: unknown, fallback: string): string {
  if (axios.isAxiosError(caught)) {
    const detail = caught.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg ?? JSON.stringify(item)).join(', ');
    return caught.message;
  }
  return caught instanceof Error ? caught.message : fallback;
}

export async function uploadDataset(
  file: File,
  onUploadProgress?: (progress: number) => void,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await api.post<UploadResponse>('/api/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (!event.total || !onUploadProgress) return;
        onUploadProgress(Math.round((event.loaded * 100) / event.total));
      },
    });

    return response.data;
  } catch (caught) {
    throw new Error(getApiErrorMessage(caught, 'Upload failed. Please try another file.'));
  }
}

export async function invokeAgent(
  datasetId: string,
  message: string,
  conversationId?: string | null,
): Promise<AgentResponse> {
  try {
    const response = await api.post<AgentResponse>('/api/agent/invoke', {
      dataset_id: datasetId,
      message,
      conversation_id: conversationId,
    });

    return response.data;
  } catch (caught) {
    throw new Error(getApiErrorMessage(caught, 'Agent execution failed. Try a more specific request.'));
  }
}
