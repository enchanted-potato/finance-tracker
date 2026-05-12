import { describe, it, expect, vi } from 'vitest';

// Mock react-router-dom (NavLink) to avoid MemoryRouter + React 19 microtask OOM.
// NavLink is replaced with a plain anchor — tests verify label text not routing behavior.
vi.mock('react-router-dom', () => ({
  NavLink: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}));

// Mock shadcn sidebar primitives — they use SidebarProvider context which is heavy.
// These stubs render children transparently so nav labels are still discoverable.
vi.mock('@/components/ui/sidebar', () => ({
  Sidebar: ({ children }: { children: React.ReactNode }) => <nav>{children}</nav>,
  SidebarContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SidebarGroup: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SidebarGroupContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SidebarMenu: ({ children }: { children: React.ReactNode }) => <ul>{children}</ul>,
  SidebarMenuItem: ({ children }: { children: React.ReactNode }) => <li>{children}</li>,
  SidebarMenuButton: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { render, screen } from '@testing-library/react';
import { AppSidebar } from '@/components/AppSidebar';

describe('AppSidebar', () => {
  function renderSidebar() {
    return render(<AppSidebar />);
  }

  it('renders a Dashboard nav link', () => {
    renderSidebar();
    expect(screen.getByText('Dashboard')).toBeTruthy();
  });

  it('renders an Accounts nav link', () => {
    renderSidebar();
    expect(screen.getByText('Accounts')).toBeTruthy();
  });

  it('renders a Liabilities nav link', () => {
    renderSidebar();
    expect(screen.getByText('Liabilities')).toBeTruthy();
  });

  it('renders a Pension nav link', () => {
    renderSidebar();
    expect(screen.getByText('Pension')).toBeTruthy();
  });

  it('renders a History nav link', () => {
    renderSidebar();
    expect(screen.getByText('History')).toBeTruthy();
  });

  it('renders a Configure nav link', () => {
    renderSidebar();
    expect(screen.getByText('Configure')).toBeTruthy();
  });

  it('renders exactly 6 navigation items', () => {
    renderSidebar();
    const labels = ['Dashboard', 'Accounts', 'Liabilities', 'Pension', 'History', 'Configure'];
    labels.forEach(label => expect(screen.getByText(label)).toBeTruthy());
    expect(labels).toHaveLength(6);
  });
});
