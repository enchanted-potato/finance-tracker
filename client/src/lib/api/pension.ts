import { apiClient } from '@/lib/apiClient';

export interface PensionTypeResponse {
  id: number;
  name: string;
  is_pension: boolean;
  // NOTE: No in_use field on pension types
}

export interface PensionEntryRequest {
  account_type_id: number;   // NOTE: uses account_type_id (same as accounts)
  entry_date: string;         // ISO 'yyyy-MM-dd'
  balance: number;
  exchange_rate?: number;
}

export interface PensionHistoryItemResponse {
  entry_id: number;
  type_id: number;
  type_name: string;
  balance: number;
}

export interface PensionHistoryDayResponse {
  date: string;
  total: number;
  entries: PensionHistoryItemResponse[];
}

export const pensionApi = {
  listTypes: (): Promise<PensionTypeResponse[]> =>
    apiClient.get('/api/pension/types').then(r => r.data),

  createType: (name: string): Promise<PensionTypeResponse> =>
    apiClient.post('/api/pension/types', { name }).then(r => r.data),

  updateType: (id: number, name: string): Promise<PensionTypeResponse> =>
    apiClient.put(`/api/pension/types/${id}`, { name }).then(r => r.data),

  deleteType: (id: number): Promise<void> =>
    apiClient.delete(`/api/pension/types/${id}`).then(r => r.data),

  createEntry: (body: PensionEntryRequest): Promise<unknown> =>
    apiClient.post('/api/pension/entries', body).then(r => r.data),

  getHistory: (): Promise<PensionHistoryDayResponse[]> =>
    apiClient.get('/api/pension/history').then(r => r.data),
};
