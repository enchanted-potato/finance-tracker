import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

// Mock firebase BEFORE importing apiClient so the module-level auth reference is mocked
vi.mock('@/lib/firebase', () => ({
  auth: { currentUser: null },
  googleProvider: {},
}));

// Mock firebase/auth getIdToken — alias in vitest.config.ts redirects firebase/auth to stub,
// but we need to mock getIdToken specifically here for return value control
vi.mock('firebase/auth', () => ({
  getIdToken: vi.fn().mockResolvedValue('fake-id-token-123'),
}));

import { apiClient } from '@/lib/apiClient';
import { auth } from '@/lib/firebase';
import { getIdToken } from 'firebase/auth';

const mockGetIdToken = vi.mocked(getIdToken);
const mockAxios = new MockAdapter(apiClient);

describe('apiClient', () => {
  beforeEach(() => {
    mockAxios.reset();
    mockGetIdToken.mockResolvedValue('fake-id-token-123');
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('request interceptor', () => {
    it('attaches Authorization Bearer header when currentUser is set', async () => {
      const fakeUser = { uid: 'abc123' } as any;
      (auth as any).currentUser = fakeUser;
      mockAxios.onGet('/api/test').reply(200, { ok: true });

      const response = await apiClient.get('/api/test');

      expect(mockGetIdToken).toHaveBeenCalledWith(fakeUser);
      expect(response.config.headers.Authorization).toBe('Bearer fake-id-token-123');
    });

    it('does not attach Authorization header when currentUser is null', async () => {
      (auth as any).currentUser = null;
      mockAxios.onGet('/api/test').reply(200, { ok: true });

      const response = await apiClient.get('/api/test');

      expect(mockGetIdToken).not.toHaveBeenCalled();
      expect(response.config.headers.Authorization).toBeUndefined();
    });
  });

  describe('response interceptor — 401 redirect', () => {
    it('sets window.location.href to /login on 401 response', async () => {
      (auth as any).currentUser = null;
      mockAxios.onGet('/api/protected').reply(401, { detail: 'Unauthorized' });

      try {
        await apiClient.get('/api/protected');
      } catch {
        // Expected to throw
      }

      expect(window.location.href).toBe('/login');
    });

    it('does not redirect on non-401 errors', async () => {
      (auth as any).currentUser = null;
      mockAxios.onGet('/api/broken').reply(500, { detail: 'Server Error' });

      try {
        await apiClient.get('/api/broken');
      } catch {
        // Expected to throw
      }

      expect(window.location.href).not.toBe('/login');
    });
  });
});
