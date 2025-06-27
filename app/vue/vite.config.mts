import vue from '@vitejs/plugin-vue'

import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

import vuetify from 'vite-plugin-vuetify'

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? '/static/dist' : '/',
  build: {
    outDir: '../django/static/dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1350,
  },
  plugins: [
    vue(),
    vuetify({
      autoImport: true,
    }),
    // VuetifyPlugin(),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
    extensions: ['.js', '.json', '.jsx', '.mjs', '.ts', '.mts', '.tsx', '.vue'],
  },
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://localhost',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    deps: {
      inline: ['vuetify'],
    },
  },
})
