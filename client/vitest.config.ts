/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    teardownTimeout: 5000,
    pool: 'vmThreads',
    setupFiles: ['./src/__tests__/setup.ts'],
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Redirect firebase SDK to lightweight stubs in tests to prevent OOM
      'firebase/app': path.resolve(__dirname, './src/__tests__/__mocks__/firebase-app.ts'),
      'firebase/auth': path.resolve(__dirname, './src/__tests__/__mocks__/firebase-auth.ts'),
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
