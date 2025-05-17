import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig } from 'vite'
import { configDefaults } from 'vitest/config'
import viteConfig from './vite.config.mts'

export default mergeConfig(
  viteConfig,
  // @ts-ignore
  defineConfig({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/*'],
      root: fileURLToPath(new URL('./', import.meta.url)),
      // @ts-ignore
      transformMode: {
        web: [/\.[jt]sx$/],
      },
    },
  }),
)
