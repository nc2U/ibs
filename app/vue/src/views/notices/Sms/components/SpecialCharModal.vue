<script lang="ts" setup>
import { ref, computed } from 'vue'

// Emits 정의
const emit = defineEmits<{
  insert: [char: string]
}>()

// 모달 상태
const visible = ref(false)
const selectedCategory = ref('common')

// 특수문자 데이터 (카테고리별)
interface SpecialCharCategory {
  name: string
  label: string
  chars: string[]
}

const specialChars: SpecialCharCategory[] = [
  {
    name: 'common',
    label: '자주 사용',
    chars: ['●', '○', '■', '□', '★', '☆', '◆', '◇', '▲', '△', '▼', '▽', '♥', '♡', '※', '▣', '◈'],
  },
  {
    name: 'symbol',
    label: '기호',
    chars: [
      '!',
      '@',
      '#',
      '$',
      '%',
      '^',
      '&',
      '*',
      '(',
      ')',
      '-',
      '_',
      '+',
      '=',
      '[',
      ']',
      '{',
      '}',
      '|',
      '\\',
      '/',
      '~',
      '`',
    ],
  },
  {
    name: 'punctuation',
    label: '문장부호',
    chars: [
      '.',
      ',',
      ';',
      ':',
      '?',
      '!',
      '"',
      "'",
      '<',
      '>',
      '「',
      '」',
      '『',
      '』',
      '【',
      '】',
      '(',
      ')',
      '…',
      '·',
    ],
  },
  {
    name: 'arrow',
    label: '화살표',
    chars: ['←', '→', '↑', '↓', '↔', '↕', '⇐', '⇒', '⇑', '⇓', '⇔', '⇕', '➜', '➝', '➞', '➟', '➠'],
  },
  {
    name: 'line',
    label: '선/도형',
    chars: [
      '─',
      '━',
      '│',
      '┃',
      '┌',
      '┐',
      '└',
      '┘',
      '├',
      '┤',
      '┬',
      '┴',
      '┼',
      '╋',
      '═',
      '║',
      '╔',
      '╗',
      '╚',
      '╝',
    ],
  },
  {
    name: 'math',
    label: '수학기호',
    chars: [
      '+',
      '-',
      '×',
      '÷',
      '=',
      '≠',
      '<',
      '>',
      '≤',
      '≥',
      '±',
      '∞',
      '∑',
      '∫',
      '√',
      '∝',
      '∈',
      '∀',
      '∃',
      '∧',
      '∨',
    ],
  },
  {
    name: 'unit',
    label: '단위',
    chars: [
      '℃',
      '℉',
      '°',
      '㎡',
      '㎥',
      '㎝',
      '㎜',
      '㎞',
      '㎏',
      '㎎',
      '㎖',
      '㎗',
      '㎘',
      '€',
      '£',
      '¥',
      '₩',
      '$',
    ],
  },
  {
    name: 'number',
    label: '특수숫자',
    chars: [
      '①',
      '②',
      '③',
      '④',
      '⑤',
      '⑥',
      '⑦',
      '⑧',
      '⑨',
      '⑩',
      'Ⅰ',
      'Ⅱ',
      'Ⅲ',
      'Ⅳ',
      'Ⅴ',
      'Ⅵ',
      'Ⅶ',
      'Ⅷ',
      'Ⅸ',
      'Ⅹ',
    ],
  },
  {
    name: 'etc',
    label: '기타',
    chars: [
      '©',
      '®',
      '™',
      '℡',
      '№',
      '㉿',
      '☎',
      '☏',
      '✓',
      '✔',
      '✕',
      '✖',
      '✗',
      '✘',
      '♪',
      '♬',
      '♭',
      '♯',
      '♮',
    ],
  },
]

// 현재 선택된 카테고리의 문자들
const currentChars = computed(() => {
  const category = specialChars.find(cat => cat.name === selectedCategory.value)
  return category?.chars || []
})

// 카테고리 탭 옵션
const categoryTabs = computed(() => {
  return specialChars.map(cat => ({
    value: cat.name,
    label: cat.label,
  }))
})

// 모달 열기/닫기
const openModal = () => {
  visible.value = true
  selectedCategory.value = 'common'
}

const closeModal = () => {
  visible.value = false
}

// 특수문자 클릭 처리
const handleCharClick = (char: string) => {
  emit('insert', char)
  // 모달은 닫지 않고 계속 선택할 수 있도록 유지
}

// 외부에서 호출할 수 있도록 expose
defineExpose({
  openModal,
  closeModal,
})
</script>

<template>
  <v-dialog v-model="visible" max-width="600px" persistent>
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span class="text-h6">
          <v-icon icon="mdi-code-braces" class="me-2" />
          특수문자 선택
        </span>
        <v-btn icon="mdi-close" variant="text" size="small" @click="closeModal" />
      </v-card-title>

      <v-card-text>
        <!-- 카테고리 탭 -->
        <v-tabs v-model="selectedCategory" density="compact" class="mb-4">
          <v-tab v-for="tab in categoryTabs" :key="tab.value" :value="tab.value">
            {{ tab.label }}
          </v-tab>
        </v-tabs>

        <!-- 특수문자 그리드 -->
        <div class="special-char-grid">
          <v-btn
            v-for="(char, index) in currentChars"
            :key="`${selectedCategory}-${index}`"
            variant="outlined"
            size="large"
            class="special-char-btn"
            @click="handleCharClick(char)"
          >
            {{ char }}
          </v-btn>
        </div>

        <v-alert type="info" variant="tonal" density="compact" class="mt-4">
          <small> 특수문자를 클릭하면 메시지 입력란의 커서 위치에 삽입됩니다. </small>
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn color="primary" variant="text" @click="closeModal"> 닫기 </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped lang="scss">
.special-char-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #fafafa;
}

.dark-theme {
  .special-char-grid {
    background-color: #1e1e1e;
    border-color: #3a3b45;
  }
}

.special-char-btn {
  min-width: 50px;
  height: 50px;
  font-size: 20px;
  font-weight: bold;
  transition: all 0.2s ease;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  &:active {
    transform: scale(0.95);
  }
}
</style>
