import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const basePath = (globalThis as any).process?.env?.VITE_BASE_PATH || '/webapp/'

export default defineConfig({
  plugins: [react()],
  base: basePath,
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-motion': ['framer-motion'],
          'vendor-icons': ['lucide-react'],
        },
      },
    },
  },
  server: {
    port: 3000,
  },
})
