import { DataPage } from '@/components/data/DataPage';
import { pensionApi } from '@/lib/api/pension';
import type { PensionTypeResponse } from '@/lib/api/pension';
import type { DataPageConfig } from '@/components/data/DataPage';

const pensionConfig: DataPageConfig<PensionTypeResponse> = {
  title: 'Pension',
  queryKey: ['pension', 'types'] as const,
  historyQueryKey: ['pension', 'history'] as const,
  fetchItems: pensionApi.listTypes,
  fetchHistory: pensionApi.getHistory,
  createItem: pensionApi.createType,
  updateItem: pensionApi.updateType,
  deleteItem: pensionApi.deleteType,
  submitEntry: (body) => pensionApi.createEntry({
    account_type_id: body.item_type_id,   // NOTE: pension uses account_type_id (same as accounts)
    entry_date: body.entry_date,
    balance: body.balance,
  }),
  itemLabel: 'provider',
};

export function PensionPage() {
  return <DataPage config={pensionConfig} />;
}
