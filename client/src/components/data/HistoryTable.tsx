import React, { useState } from 'react';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';

export interface EntryItemDisplay {
  entry_id: number;
  type_id: number;
  type_name: string;
  balance: number;
}

export interface HistoryDayDisplay {
  date: string;
  total: number;
  entries: EntryItemDisplay[];
}

const fmt = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' });

export function HistoryTable({ data }: { data: HistoryDayDisplay[] }) {
  const [expandedDate, setExpandedDate] = useState<string | null>(null);

  if (data.length === 0) {
    return <p className="text-muted-foreground text-sm">No entries yet.</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead className="text-right">Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map(day => (
          <React.Fragment key={day.date}>
            <TableRow
              className={expandedDate === day.date
                ? 'cursor-pointer bg-muted/50'
                : 'cursor-pointer hover:bg-muted/50'}
              onClick={() => setExpandedDate(expandedDate === day.date ? null : day.date)}
            >
              <TableCell>{day.date}</TableCell>
              <TableCell className="text-right">{fmt.format(day.total)}</TableCell>
            </TableRow>
            {expandedDate === day.date && day.entries.map(entry => (
              <TableRow key={entry.entry_id} className="bg-muted/20">
                <TableCell className="pl-8 text-muted-foreground">{entry.type_name}</TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {fmt.format(entry.balance)}
                </TableCell>
              </TableRow>
            ))}
          </React.Fragment>
        ))}
      </TableBody>
    </Table>
  );
}
