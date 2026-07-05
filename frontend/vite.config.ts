import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const backend = process.env.BACKEND_URL || 'http://localhost:8000'
const proxy = Object.fromEntries(
  ['/trips', '/me', '/pois'].map((p) => [p, { target: backend, changeOrigin: true }]),
)

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
})
