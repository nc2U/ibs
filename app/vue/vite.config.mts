import vue from '@vitejs/plugin-vue'

import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'

import vuetify from 'vite-plugin-vuetify'

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? '/static/dist' : '/',
  build: {
    outDir: process.env.BUILD_DIR || '../django/static/dist',
    emptyOutDir: true,
    chunkSizeWarningLimit: 2500,
    sourcemap: process.env.NODE_ENV !== 'production',
    cssCodeSplit: true,
    modulePreload: {
      polyfill: true,
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Vuetify UI framework (large) - check first
            if (id.includes('vuetify') || id.includes('@mdi/font')) {
              return 'vendor-vuetify'
            }

            // CoreUI framework
            if (id.includes('@coreui')) {
              return 'vendor-coreui'
            }

            // Chart and visualization libraries
            if (id.includes('d3') || id.includes('chart') || id.includes('@gitgraph')) {
              return 'vendor-charts'
            }

            // Calendar libraries
            if (id.includes('fullcalendar') || id.includes('ganttastic')) {
              return 'vendor-calendar'
            }

            // Rich text editors
            if (id.includes('quill') || id.includes('markdown') || id.includes('highlight.js')) {
              return 'vendor-editors'
            }

            // Form and input components
            if (id.includes('multiselect') || id.includes('datepicker') || id.includes('vue-select')) {
              return 'vendor-forms'
            }

            // Utilities and helpers
            if (id.includes('axios') || id.includes('lodash') || id.includes('@vueuse')) {
              return 'vendor-utils'
            }

            // Vue ecosystem - more specific matching
            if (id.match(/\/node_modules\/vue\//) || id.match(/\/node_modules\/.pnpm\/vue@/)) {
              return 'vendor-vue-core'
            }
            if (id.includes('vue-router') || id.includes('pinia')) {
              return 'vendor-vue-router-pinia'
            }
            if (id.includes('@vue/') || id.includes('vue-demi')) {
              return 'vendor-vue-ecosystem'
            }

            // Remaining small packages - group by pnpm structure
            const match = id.match(/node_modules\/\.pnpm\/([^@\/]+)/)
            if (match) {
              return `vendor-.pnpm`
            }

            // Other vendor packages
            const pkgName = id.toString().split('node_modules/')[1].split('/')[0]
            return `vendor-${pkgName.replace('@', '')}`
          }
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: process.env.NODE_ENV === 'production',
      },
    },
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
