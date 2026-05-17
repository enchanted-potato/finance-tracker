import { DataPage } from '@/components/data/DataPage';
import { accountsApi } from '@/lib/api/accounts';
import type { AccountTypeResponse } from '@/lib/api/accounts';
import type { DataPageConfig } from '@/components/data/DataPage';

const accountsConfig: DataPageConfig<AccountTypeResponse> = {
  title: 'Accounts',
  queryKey: ['accounts', 'types'] as const,
  historyQueryKey: ['accounts', 'history'] as const,
  fetchItems: accountsApi.listTypes,
  fetchHistory: accountsApi.getHistory,
  createItem: accountsApi.createType,
  updateItem: accountsApi.updateType,
  deleteItem: accountsApi.deleteType,
  submitEntry: (body) => accountsApi.createEntry({
    account_type_id: body.item_type_id,
    entry_date: body.entry_date,
    balance: body.balance,
  }),
  itemLabel: 'account',
};

export function AccountsPage() {
  return <DataPage config={accountsConfig} />;
}
