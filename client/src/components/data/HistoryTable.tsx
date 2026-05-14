// Stub — will be implemented in Plan 12-03

interface HistoryEntry {
  entry_id: number;
  type_id: number;
  type_name: string;
  balance: number;
}

interface HistoryRow {
  date: string;
  total: number;
  entries: HistoryEntry[];
}

interface HistoryTableProps {
  data: HistoryRow[];
}

export function HistoryTable(_props: HistoryTableProps) {
  return <div>HistoryTable stub</div>;
}
