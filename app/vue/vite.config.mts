import vue from '@vitejs/plugin-vue'

import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

import vuetify from 'vite-plugin-vuetify'

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? '/static/dist' : '/',
  build: {
    target: 'ESNext',
    outDir: process.env.BUILD_DIR || '../django/static/dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1000,
    sourcemap: process.env.NODE_ENV !== 'production',
    cssCodeSplit: true,
    modulePreload: {
      polyfill: true,
    },
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('exceljs')) {
              return 'vendor-excel'
            }
            if (id.includes('vuetify')) {
              return 'vendor-vuetify'
            }
            if (id.includes('@coreui') || id.includes('chart.js')) {
              return 'vendor-coreui'
            }
            if (id.includes('@fullcalendar')) {
              return 'vendor-calendar'
            }
            if (id.includes('quill')) {
              return 'vendor-quill'
            }
            if (id.includes('diff2html')) {
              return 'vendor-diff'
            }
            if (
              id.includes('md-editor-v3') ||
              id.includes('markdown-it') ||
              id.includes('highlight.js')
            ) {
              return 'vendor-editor'
            }
            if (
              id.includes('d3') ||
              id.includes('@gitgraph') ||
              id.includes('@infectoone')
            ) {
              return 'vendor-charts'
            }
            if (id.includes('@vuepic/vue-datepicker')) {
              return 'vendor-datepicker'
            }
            if (
              id.includes('/node_modules/vue/') ||
              id.includes('/node_modules/@vue/') ||
              id.includes('/node_modules/vue-router/') ||
              id.includes('/node_modules/pinia/') ||
              id.includes('/node_modules/@vueuse/') ||
              id.includes('/node_modules/axios/')
            ) {
              return 'vendor-vue'
            }
          }
        },
      },
    },
    minify: 'esbuild',
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
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'vuetify', 'md-editor-v3', 'highlight.js'],
    exclude: [],
    esbuildOptions: {
      target: 'ESNext',
    },
  },
  esbuild: {
    drop: process.env.VITE_DROP_CONSOLE === 'false' ? ['console', 'debugger'] : [],
    target: 'ESNext',
  },
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://localhost',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://localhost',
        ws: true,
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost',
        changeOrigin: true,
      },
      '/pdf': {
        target: 'http://localhost',
        changeOrigin: true,
      },
      '/excel': {
        target: 'http://localhost',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    server: {
      deps: {
        inline: ['vuetify'],
      },
    },
  },
})
