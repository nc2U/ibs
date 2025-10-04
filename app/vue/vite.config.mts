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
    chunkSizeWarningLimit: 2500,
    sourcemap: process.env.NODE_ENV !== 'production',
    cssCodeSplit: true,
    modulePreload: {
      polyfill: true,
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          // node_modules가 아닌 경우 기본 처리
          if (!id.includes('node_modules')) {
            return
          }

          // UI Frameworks (구체적인 것 먼저)
          if (id.includes('vuetify')) {
            return 'vuetify'
          }
          if (id.includes('@coreui')) {
            return 'coreui'
          }

          // Charts & Data Visualization
          if (id.includes('chartjs') || id.includes('node_modules/d3')) {
            return 'charts'
          }

          // Calendar & Gantt
          if (id.includes('fullcalendar') || id.includes('ganttastic')) {
            return 'calendar'
          }

          // Editors
          if (id.includes('quill') || id.includes('md-editor') || id.includes('markdown-it')) {
            return 'editors'
          }

          // Git & Diff tools
          if (id.includes('gitgraph') || id.includes('diff2html') || id.includes('highlight')) {
            return 'git-tools'
          }

          // Form controls
          if (id.includes('datepicker') || id.includes('multiselect') ||
              id.includes('maska') || id.includes('cropper')) {
            return 'form-controls'
          }

          // Utils
          if (id.includes('axios') || id.includes('cookie') || id.includes('vueuse') ||
              id.includes('nprogress') || id.includes('mosha') || id.includes('dompurify')) {
            return 'utils'
          }

          // Core Vue ecosystem (마지막에)
          if (id.includes('vue-router') || id.includes('pinia')) {
            return 'vue-core'
          }
          if (id.includes('/vue/') && !id.includes('vue-')) {
            return 'vue-core'
          }

          // 나머지 vendor 라이브러리
          return 'vendor'
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: process.env.NODE_ENV === 'production'
      }
    }
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
