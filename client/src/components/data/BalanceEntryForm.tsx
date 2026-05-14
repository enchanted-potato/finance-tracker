// Stub — will be implemented in Plan 12-02

interface BalanceEntryFormProps {
  items: Array<{ id: number; name: string; is_pension?: boolean; in_use?: boolean }>;
  historyQueryKey: readonly string[];
  submitEntry: (entry: { typeId: number; balance: number; date: string }) => Promise<void>;
  itemLabel: string;
}

export function BalanceEntryForm(_props: BalanceEntryFormProps) {
  return <div>BalanceEntryForm stub</div>;
}
