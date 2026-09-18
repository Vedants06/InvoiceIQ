import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// The dev server proxies API calls to the FastAPI backend so the browser
// only ever talks to one origin (relative URLs in client code).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Allow the sandbox/preview host in addition to localhost.
    allowedHosts: ['.e2b.app', 'localhost'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
