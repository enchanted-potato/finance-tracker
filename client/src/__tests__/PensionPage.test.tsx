import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }: { children: React.ReactNode; open: boolean }) =>
    open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/alert-dialog', () => ({
  AlertDialog: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({ children }: { children: React.ReactNode }) => <button>{children}</button>,
  AlertDialogAction: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => <button onClick={onClick}>{children}</button>,
}));

vi.mock('@/components/ui/calendar', () => ({
  Calendar: () => <div data-testid="calendar" />,
}));

vi.mock('@/components/ui/popover', () => ({
  Popover: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PopoverTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  PopoverContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>,
  SelectContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: { children: React.ReactNode }) => <table>{children}</table>,
  TableHeader: ({ children }: { children: React.ReactNode }) => <thead>{children}</thead>,
  TableBody: ({ children }: { children: React.ReactNode }) => <tbody>{children}</tbody>,
  TableHead: ({ children }: { children: React.ReactNode }) => <th>{children}</th>,
  TableRow: ({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) => <tr onClick={onClick} className={className}>{children}</tr>,
  TableCell: ({ children, className }: { children: React.ReactNode; className?: string }) => <td className={className}>{children}</td>,
}));

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { renderWithQuery } from './test-utils';
import { apiClient } from '@/lib/apiClient';
import { PensionPage } from '@/pages/PensionPage';

const mockAxios = new MockAdapter(apiClient);

describe('PensionPage', () => {
  beforeEach(() => { mockAxios.reset(); });
  afterEach(() => { vi.clearAllMocks(); });

  it('renders pension provider list from API (RDAT-06)', async () => {
    mockAxios.onGet('/api/pension/types').reply(200, [
      { id: 1, name: 'NEST', is_pension: true },
      { id: 2, name: 'Company Pension', is_pension: true },
    ]);
    mockAxios.onGet('/api/pension/history').reply(200, []);
    renderWithQuery(<PensionPage />);
    // Items appear in both the list AND the BalanceEntryForm select (via SelectItem mock)
    // Use getAllByText to handle multiple occurrences of the same name
    await waitFor(() => {
      expect(screen.getAllByText('NEST').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Company Pension').length).toBeGreaterThan(0);
    });
  });

  it('renders page title "Pension" (RDAT-06)', async () => {
    mockAxios.onGet('/api/pension/types').reply(200, []);
    mockAxios.onGet('/api/pension/history').reply(200, []);
    renderWithQuery(<PensionPage />);
    await waitFor(() => {
      expect(screen.getByText('Pension')).toBeTruthy();
    });
  });
});
