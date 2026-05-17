import { apiClient } from '@/lib/apiClient';

export interface LiabilityTypeResponse {
  id: number;
  name: string;
  in_use: boolean;
  // NOTE: No is_pension field on liability types
}

export interface LiabilityEntryRequest {
  liability_type_id: number;  // NOTE: liability_type_id, not account_type_id
  entry_date: string;          // ISO 'yyyy-MM-dd'
  amount: number;              // NOTE: amount, not balance
  currency?: string;
}

export interface LiabilityHistoryItemResponse {
  entry_id: number;
  type_id: number;
  type_name: string;
  balance: number;             // unified history shape (API maps amount -> balance)
}

export interface LiabilityHistoryDayResponse {
  date: string;
  total: number;
  entries: LiabilityHistoryItemResponse[];
}

export const liabilitiesApi = {
  listTypes: (): Promise<LiabilityTypeResponse[]> =>
    apiClient.get('/api/liabilities/types').then(r => r.data),

  createType: (name: string): Promise<LiabilityTypeResponse> =>
    apiClient.post('/api/liabilities/types', { name }).then(r => r.data),

  updateType: (id: number, name: string): Promise<LiabilityTypeResponse> =>
    apiClient.put(`/api/liabilities/types/${id}`, { name }).then(r => r.data),

  deleteType: (id: number): Promise<void> =>
    apiClient.delete(`/api/liabilities/types/${id}`).then(r => r.data),

  createEntry: (body: LiabilityEntryRequest): Promise<unknown> =>
    apiClient.post('/api/liabilities/entries', body).then(r => r.data),

  getHistory: (): Promise<LiabilityHistoryDayResponse[]> =>
    apiClient.get('/api/liabilities/history').then(r => r.data),
};
