import { describe, it, expect, vi } from 'vitest';

// Mock both AuthContext and react-router-dom so PrivateRoute runs without
// a real Router context (MemoryRouter triggers React 19 concurrent-mode
// microtask loops that exhaust the heap in vitest workers).
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));
vi.mock('react-router-dom', () => ({
  Navigate: vi.fn(() => null),
  useLocation: vi.fn(() => ({ pathname: '/', search: '', hash: '', state: null, key: 'default' })),
}));

import { render, screen } from '@testing-library/react';
import { PrivateRoute } from '@/components/PrivateRoute';
import { useAuth } from '@/contexts/AuthContext';

const mockUseAuth = vi.mocked(useAuth);

describe('PrivateRoute', () => {
  it('renders null while loading=true (no flash of financial data)', () => {
    mockUseAuth.mockReturnValue({ user: null, loading: true, signOut: vi.fn() });
    const { container } = render(
      <PrivateRoute><div>Protected content</div></PrivateRoute>
    );
    expect(container.firstChild).toBeNull();
    expect(screen.queryByText('Protected content')).toBeNull();
  });

  it('redirects to /login when loading=false and user=null', () => {
    mockUseAuth.mockReturnValue({ user: null, loading: false, signOut: vi.fn() });
    const { container } = render(
      <PrivateRoute><div>Protected content</div></PrivateRoute>
    );
    expect(screen.queryByText('Protected content')).toBeNull();
    expect(container).toBeTruthy();
  });

  it('renders children when loading=false and user is authenticated', () => {
    const fakeUser = { uid: 'abc123', email: 'test@example.com' } as any;
    mockUseAuth.mockReturnValue({ user: fakeUser, loading: false, signOut: vi.fn() });
    render(
      <PrivateRoute><div>Protected content</div></PrivateRoute>
    );
    expect(screen.getByText('Protected content')).toBeTruthy();
  });
});
