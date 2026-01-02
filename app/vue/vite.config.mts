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
        // manualChunks(id) {
        //   // Application specific chunks - check before node_modules
        //   if (id.includes('src/views/proCash') || id.includes('src/store/pinia/proCash')) {
        //     return 'proCash'
        //   }
        //
        //   if (id.includes('node_modules')) {
        //     // Vue ecosystem (keep together to avoid circular dependency issues)
        //     if (
        //       id.match(/\/node_modules\/vue\//) ||
        //       id.match(/\/node_modules\/.pnpm\/vue@/) ||
        //       id.match(/\/.pnpm\/vue@/) ||
        //       id.includes('@vue/') ||
        //       id.includes('vue-demi') ||
        //       id.match(/\/.pnpm\/@vue\//) ||
        //       id.includes('vue-router') ||
        //       id.includes('pinia') ||
        //       id.match(/\/.pnpm\/vue-router@/) ||
        //       id.match(/\/.pnpm\/pinia@/)
        //     ) {
        //       return 'vendor-vue'
        //     }
        //
        //     // Vuetify - let Vite handle automatic bundling (removed from manualChunks)
        //     // This prevents circular dependency TDZ errors
        //     // if (id.includes('vuetify') || id.includes('@mdi/font')) {
        //     //   return undefined // Let Vite auto-optimize
        //     // }
        //
        //     // CoreUI framework
        //     if (id.includes('@coreui')) {
        //       return 'vendor-coreui'
        //     }
        //
        //     // Chart and visualization libraries
        //     if (id.includes('d3') || id.includes('chart') || id.includes('@gitgraph')) {
        //       return 'vendor-charts'
        //     }
        //
        //     // Calendar libraries
        //     if (id.includes('fullcalendar') || id.includes('ganttastic')) {
        //       return 'vendor-calendar'
        //     }
        //
        //     // Markdown editor (separate due to initialization issues)
        //     if (id.includes('md-editor-v3')) {
        //       return 'vendor-md-editor'
        //     }
        //
        //     // Rich text editors
        //     if (id.includes('quill') || id.includes('highlight.js')) {
        //       return 'vendor-editors'
        //     }
        //
        //     // Form and input components
        //     if (id.includes('multiselect') || id.includes('datepicker') || id.includes('vue-select')) {
        //       return 'vendor-forms'
        //     }
        //
        //     // Utilities and helpers
        //     if (id.includes('axios') || id.includes('lodash') || id.includes('@vueuse')) {
        //       return 'vendor-utils'
        //     }
        //
        //     // Other vendor packages - avoid generic pnpm grouping
        //     const pkgMatch = id.match(/node_modules\/(?:\.pnpm\/)?([^@\/]+(?:@[^\/]+)?)/)
        //     if (pkgMatch) {
        //       const pkgName = pkgMatch[1].split('@')[0]
        //       return `vendor-${pkgName.replace(/[^a-zA-Z0-9]/g, '-')}`
        //     }
        //   }
        // },
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
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      '@vue/shared',
      '@vue/runtime-dom',
      '@vue/runtime-core',
      'vuetify',
      'md-editor-v3',
      'highlight.js',
    ],
    exclude: [],
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
    deps: {
      inline: ['vuetify'],
    },
  },
})
