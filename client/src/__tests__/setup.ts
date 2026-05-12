// Global test setup
// Firebase SDK is replaced with stubs via vitest.config.ts resolve.alias:
//   firebase/app  -> src/__tests__/__mocks__/firebase-app.ts
//   firebase/auth -> src/__tests__/__mocks__/firebase-auth.ts
// This prevents the real Firebase SDK from being loaded and causing OOM.

// Disable React's act() environment — prevents React 19 from wrapping renders
// in act() which creates an infinite microtask loop in vitest worker forks.
// @ts-ignore
globalThis.IS_REACT_ACT_ENVIRONMENT = false;
