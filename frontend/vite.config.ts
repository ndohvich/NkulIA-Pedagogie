import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Chemins relatifs pour les assets buildés : filet de sécurité si le
  // build est un jour ouvert autrement que servi par FastAPI (voir
  // desktop/main.py, qui sert normalement frontend/dist en HTTP local).
  base: './',
  server: {
    port: 5173,
    strictPort: true,
    // En développement, l'interface (5173) et l'API (8000) sont deux
    // origines : le proxy garde des appels relatifs `/api/...`, comme
    // en production où FastAPI sert tout (voir desktop/main.py).
    proxy: { '/api': 'http://127.0.0.1:8000', '/health': 'http://127.0.0.1:8000' },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.ts',
  },
})
