import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

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

import React from 'react';
import { screen } from '@testing-library/react';
import { renderWithQuery } from './test-utils';
import { apiClient } from '@/lib/apiClient';
import { BalanceEntryForm } from '@/components/data/BalanceEntryForm';

const mockAxios = new MockAdapter(apiClient);

const sampleTypes = [{ id: 1, name: 'ISA', is_pension: false, in_use: true }];
const historyQueryKey = ['accounts', 'history'] as const;
const noop = () => Promise.resolve(undefined);

describe('BalanceEntryForm', () => {
  beforeEach(() => { mockAxios.reset(); });
  afterEach(() => { vi.clearAllMocks(); });

  it('renders Save Entry button (RDAT-02)', () => {
    renderWithQuery(
      <BalanceEntryForm
        items={sampleTypes}
        historyQueryKey={historyQueryKey}
        submitEntry={noop}
        itemLabel="account"
      />
    );
    expect(screen.getByRole('button', { name: /save entry/i })).toBeTruthy();
  });

  it('renders date picker trigger button (RDAT-02)', () => {
    renderWithQuery(
      <BalanceEntryForm
        items={sampleTypes}
        historyQueryKey={historyQueryKey}
        submitEntry={noop}
        itemLabel="account"
      />
    );
    // Date picker trigger shows today's date or "Pick a date" placeholder
    expect(screen.getByRole('button', { name: /date|today|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec/i })).toBeTruthy();
  });
});
