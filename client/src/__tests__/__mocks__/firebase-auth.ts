// Lightweight stub for firebase/auth — prevents real Firebase Auth SDK from being loaded in tests
import { vi } from 'vitest';

export function getAuth(_app?: object) {
  return { currentUser: null };
}

export function GoogleAuthProvider() {
  return {};
}

export const onAuthStateChanged = vi.fn((_auth: object, _callback: (user: null) => void) => {
  // Don't call callback — simulates pending auth state
  return vi.fn(); // unsubscribe function
});

export const signOut = vi.fn(() => Promise.resolve());

export const signInWithPopup = vi.fn(() => Promise.resolve({ user: null }));

// User type stub
export type User = {
  uid: string;
  email: string | null;
};
