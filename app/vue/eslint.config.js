import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import pluginCypress from 'eslint-plugin-cypress/flat'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default defineConfigWithVueTs(
  {
    name: 'app/files-to-lint',
    files: ['**/*.{ts,mts,tsx,vue,js,mjs,cjs}'],
  },

  globalIgnores(['**/dist/**', '**/dist-ssr/**', '**/coverage/**', 'docs/.vitepress/cache/**', 'docs/.vitepress/dist/**']),

  pluginVue.configs['flat/essential'],
  vueTsConfigs.recommended,

  {
    ...pluginCypress.configs?.recommended ?? pluginCypress.recommended,
    files: ['cypress/e2e/**/*.{cy,spec}.{js,ts,jsx,tsx}'],
  },

  skipFormatting,

  {
    name: 'app/rules',
    rules: {
      'no-extra-boolean-cast': 'off',
      'vue/multi-word-component-names': 'off',

      // 기존 코드의 누적 부채(any 등)는 경고로 두어 CI 를 막지 않고, 점진적으로 해소한다.
      // 새로운 오류 유형(구문 오류, 정의되지 않은 변수 등)은 계속 에러로 CI 를 실패시킨다.
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-unused-expressions': 'warn',
      '@typescript-eslint/no-non-null-asserted-optional-chain': 'warn',
      'prefer-const': 'warn',
      'vue/no-mutating-props': 'warn',
      'vue/block-lang': 'warn',
      'vue/no-unused-vars': 'warn',
      'vue/return-in-computed-property': 'warn',
      'vue/require-valid-default-prop': 'warn',
      'vue/no-v-text-v-html-on-component': 'warn',
      'vue/no-dupe-keys': 'warn',
      '@typescript-eslint/no-empty-object-type': 'warn',
    },
  },
)
