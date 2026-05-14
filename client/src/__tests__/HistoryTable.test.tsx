import { describe, it, expect, vi } from 'vitest';

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: { children: React.ReactNode }) => <table>{children}</table>,
  TableHeader: ({ children }: { children: React.ReactNode }) => <thead>{children}</thead>,
  TableBody: ({ children }: { children: React.ReactNode }) => <tbody>{children}</tbody>,
  TableHead: ({ children }: { children: React.ReactNode }) => <th>{children}</th>,
  TableRow: ({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) => <tr onClick={onClick} className={className}>{children}</tr>,
  TableCell: ({ children, className }: { children: React.ReactNode; className?: string }) => <td className={className}>{children}</td>,
}));

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HistoryTable } from '@/components/data/HistoryTable';

const sampleData = [
  {
    date: '2025-02-01',
    total: 1500.0,
    entries: [{ entry_id: 1, type_id: 1, type_name: 'Checking', balance: 1500.0 }],
  },
  {
    date: '2025-01-15',
    total: 3000.0,
    entries: [
      { entry_id: 2, type_id: 1, type_name: 'Checking', balance: 1000.0 },
      { entry_id: 3, type_id: 2, type_name: 'ISA', balance: 2000.0 },
    ],
  },
];

describe('HistoryTable', () => {
  it('renders daily total rows from data (RDAT-03)', () => {
    render(<HistoryTable data={sampleData} />);
    expect(screen.getByText('2025-02-01')).toBeTruthy();
    expect(screen.getByText('2025-01-15')).toBeTruthy();
  });

  it('does not show breakdown rows before click (RDAT-03)', () => {
    render(<HistoryTable data={sampleData} />);
    expect(screen.queryByText('Checking')).toBeNull();
    expect(screen.queryByText('ISA')).toBeNull();
  });

  it('expands per-item breakdown on row click (RDAT-03)', async () => {
    const user = userEvent.setup();
    render(<HistoryTable data={sampleData} />);
    const firstRow = screen.getByText('2025-02-01').closest('tr');
    await user.click(firstRow!);
    expect(screen.getByText('Checking')).toBeTruthy();
  });

  it('collapses row on second click (RDAT-03)', async () => {
    const user = userEvent.setup();
    render(<HistoryTable data={sampleData} />);
    const firstRow = screen.getByText('2025-02-01').closest('tr');
    await user.click(firstRow!);
    await user.click(firstRow!);
    expect(screen.queryByText('Checking')).toBeNull();
  });
});
