import { apiClient } from '@/lib/apiClient';

export interface AccountTypeResponse {
  id: number;
  name: string;
  is_pension: boolean;
  in_use: boolean;
}

export interface AccountEntryRequest {
  account_type_id: number;
  entry_date: string;    // ISO 'yyyy-MM-dd' — Date serialised by BalanceEntryForm
  balance: number;
  currency?: string;     // defaults to 'GBP' on server
  exchange_rate?: number;
}

export interface EntryItemResponse {
  entry_id: number;
  type_id: number;
  type_name: string;
  balance: number;
}

export interface HistoryDayResponse {
  date: string;
  total: number;
  entries: EntryItemResponse[];
}

export const accountsApi = {
  listTypes: (): Promise<AccountTypeResponse[]> =>
    apiClient.get('/api/accounts/types').then(r => r.data),

  createType: (name: string): Promise<AccountTypeResponse> =>
    apiClient.post('/api/accounts/types', { name }).then(r => r.data),

  updateType: (id: number, name: string): Promise<AccountTypeResponse> =>
    apiClient.put(`/api/accounts/types/${id}`, { name }).then(r => r.data),

  deleteType: (id: number): Promise<void> =>
    apiClient.delete(`/api/accounts/types/${id}`).then(r => r.data),

  createEntry: (body: AccountEntryRequest): Promise<unknown> =>
    apiClient.post('/api/accounts/entries', body).then(r => r.data),

  getHistory: (): Promise<HistoryDayResponse[]> =>
    apiClient.get('/api/accounts/history').then(r => r.data),
};
