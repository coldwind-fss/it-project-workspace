import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'
const root = path.resolve(__dirname, '..')
export default defineConfig(({ mode }) => {
  const env = { ...loadEnv(mode, root, 'VITE_'), ...process.env }
  const base = env.VITE_PUBLIC_BASE || '/pm/'
  const api = env.VITE_API_BASE || base + 'api'
  const target = env.VITE_API_TARGET || 'http://127.0.0.1:8083'
  return {
    root, base, plugins: [vue()],
    define: { 'import.meta.env.VITE_API_BASE': JSON.stringify(api) },
    resolve: { alias: { '@': path.resolve(root, 'src') } },
    css: { postcss: { plugins: [tailwindcss({ config: path.resolve(__dirname, 'tailwind.config.js') }), autoprefixer()] } },
    server: { host: '127.0.0.1', port: 3003, strictPort: true, proxy: {
      [api]: { target, changeOrigin: true, rewrite: (p: string) => p.replace(api, '/api') },
      [base + 'preview-login']: { target, changeOrigin: true },
    } },
    build: { outDir: path.resolve(root, 'dist'), emptyOutDir: true },
  }
})
