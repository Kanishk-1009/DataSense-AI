import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/upload': { target: 'http://localhost:8000', changeOrigin: true },
      '/eda': { target: 'http://localhost:8000', changeOrigin: true },
      '/analyze': { target: 'http://localhost:8000', changeOrigin: true },
      '/evaluate': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
