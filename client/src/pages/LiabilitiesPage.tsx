import { DataPage } from '@/components/data/DataPage';
import { liabilitiesApi } from '@/lib/api/liabilities';
import type { LiabilityTypeResponse } from '@/lib/api/liabilities';
import type { DataPageConfig } from '@/components/data/DataPage';

const liabilitiesConfig: DataPageConfig<LiabilityTypeResponse> = {
  title: 'Liabilities',
  queryKey: ['liabilities', 'types'] as const,
  historyQueryKey: ['liabilities', 'history'] as const,
  fetchItems: liabilitiesApi.listTypes,
  fetchHistory: liabilitiesApi.getHistory,
  createItem: liabilitiesApi.createType,
  updateItem: liabilitiesApi.updateType,
  deleteItem: liabilitiesApi.deleteType,
  submitEntry: (body) => liabilitiesApi.createEntry({
    liability_type_id: body.item_type_id,  // NOTE: maps from generic item_type_id
    entry_date: body.entry_date,
    amount: body.balance,                   // NOTE: maps from generic balance → amount
  }),
  itemLabel: 'liability',
};

export function LiabilitiesPage() {
  return <DataPage config={liabilitiesConfig} />;
}
