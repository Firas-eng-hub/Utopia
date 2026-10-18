import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  if (process.env.VERCEL === '1') {
    const value = process.env.VITE_API_BASE_URL || env.VITE_API_BASE_URL
    let api: URL
    try {
      api = new URL(value || '')
    } catch {
      throw new Error('Set VITE_API_BASE_URL to your hosted backend HTTPS URL ending in /api/v1 in Vercel project settings.')
    }
    if (api.protocol !== 'https:' || ['localhost', '127.0.0.1', '[::1]'].includes(api.hostname) || api.username || api.password || api.search || api.hash || api.pathname.replace(/\/+$/, '') !== '/api/v1') {
      throw new Error('VITE_API_BASE_URL must be a public HTTPS backend URL ending in /api/v1, without credentials, query parameters, or a fragment.')
    }
  }
  return { plugins: [react()] }
})
