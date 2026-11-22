<script lang="ts" setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import {
  filterAccountOptions,
  searchAccountOptions,
  type AccountSortType,
} from './accountFilterUtils'

interface Props {
  options: Array<AccountPicker>
  modelValue?: number | null
  sortType?: AccountSortType
  visible?: boolean
  position?: { top: number; left: number; width: number } | null
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  position: null,
})

interface Emits {
  (e: 'update:modelValue', value: number | null): void
  (e: 'close'): void
}

const emit = defineEmits<Emits>()

const searchInputRef = ref<HTMLInputElement | null>(null)
const containerRef = ref<HTMLElement | null>(null)
const searchQuery = ref('')
const selectedIndex = ref(-1)
let focusTimer: ReturnType<typeof setTimeout> | undefined

// 한글 IME 입력 중에도 즉시 반영
const handleInput = (event: Event) => {
  searchQuery.value = (event.target as HTMLInputElement).value
  selectedIndex.value = -1 // 검색 시 선택 초기화
}

// 필터링된 옵션 생성
const filteredOptions = computed(() =>
  filterAccountOptions(props.options, { sortType: props.sortType }),
)

// 검색 결과 필터링 (부모-자식 관계 포함)
const searchFilteredOptions = computed(() =>
  searchAccountOptions(filteredOptions.value, searchQuery.value),
)

// 선택 가능한 옵션들 (카테고리 전용 항목 제외)
const selectableOptions = computed(() => {
  return searchFilteredOptions.value.filter(opt => !opt.is_cate_only)
})

// 옵션 선택 처리
const selectOption = (option: AccountPicker) => {
  if (!option.is_cate_only) {
    emit('update:modelValue', option.value)
    // v-model 업데이트가 완료된 후 close 이벤트 발생
    nextTick(() => {
      emit('close')
    })
  }
}

// 키보드 네비게이션 처리
const handleKeyDown = (event: KeyboardEvent) => {
  const listEl = containerRef.value?.querySelector('.account-list') as HTMLElement

  const scrollIntoView = () => {
    nextTick(() => {
      if (!listEl) return
      const activeEl = listEl.querySelector('.keyboard-active') as HTMLElement
      const searchContainer = containerRef.value?.querySelector('.search-input') as HTMLElement

      if (activeEl) {
        const listRect = listEl.getBoundingClientRect()
        const activeRect = activeEl.getBoundingClientRect()
        const searchHeight = searchContainer ? searchContainer.offsetHeight : 0

        if (activeRect.top < listRect.top + searchHeight) {
          listEl.scrollTop -= listRect.top + searchHeight - activeRect.top
        } else if (activeRect.bottom > listRect.bottom) {
          listEl.scrollTop += activeRect.bottom - listRect.bottom
        }
      }
    })
  }

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      if (selectableOptions.value.length > 0) {
        selectedIndex.value = Math.min(selectedIndex.value + 1, selectableOptions.value.length - 1)
        scrollIntoView()
      }
      break
    case 'ArrowUp':
      event.preventDefault()
      if (selectableOptions.value.length > 0) {
        selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
        scrollIntoView()
      }
      break
    case 'Enter':
      event.preventDefault()
      if (selectedIndex.value >= 0 && selectableOptions.value[selectedIndex.value]) {
        selectOption(selectableOptions.value[selectedIndex.value])
      }
      break
    case 'Escape':
      event.preventDefault()
      emit('close')
      break
  }
}

const focusAndScrollSelected = () => {
  nextTick(() => {
    clearTimeout(focusTimer)
    focusTimer = setTimeout(() => {
      searchInputRef.value?.focus()

      if (props.modelValue && containerRef.value) {
        const listEl = containerRef.value.querySelector('.account-list') as HTMLElement | null
        const selectedEl = listEl?.querySelector('.selected-item') as HTMLElement | null
        if (listEl && selectedEl) {
          listEl.scrollTop = Math.max(
            0,
            selectedEl.offsetTop - listEl.clientHeight / 2 + selectedEl.clientHeight / 2,
          )
        }
      }
    }, 100)
  })
}

// visible 변경 시 처리
watch(
  () => props.visible,
  newVal => {
    if (newVal) {
      searchQuery.value = ''
      selectedIndex.value = -1
      focusAndScrollSelected()
    }
  },
)

// 외부 클릭 감지
const handleClickOutside = (event: MouseEvent) => {
  if (!props.visible) return

  const target = event.target as Node
  if (containerRef.value && !containerRef.value.contains(target)) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  if (props.visible) focusAndScrollSelected()
})

onUnmounted(() => {
  clearTimeout(focusTimer)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div
    v-if="visible"
    ref="containerRef"
    class="ledger-account-picker"
    :style="
      position
        ? {
            top: `${position.top}px`,
            left: `${position.left}px`,
            width: `300px`,
          }
        : {}
    "
  >
    <!-- 검색 입력 -->
    <div class="search-input p-2">
      <input
        ref="searchInputRef"
        :value="searchQuery"
        type="text"
        class="form-control form-control-sm"
        placeholder="검색..."
        @input="handleInput"
        @keydown="handleKeyDown"
        @click.stop
      />
    </div>

    <!-- 계정 목록 -->
    <div class="account-list">
      <div
        v-for="option in searchFilteredOptions"
        :key="option.value"
        :class="{
          'account-item': true,
          'category-only': option.is_cate_only,
          'selected-item': option.value === modelValue,
          'keyboard-active': selectableOptions[selectedIndex]?.value === option.value,
        }"
        @click.stop="selectOption(option)"
      >
        <span :style="`padding-left: ${(option.depth || 0) * 12}px`">
          {{ option.label }}
        </span>
      </div>

      <!-- 검색 결과가 없을 때 -->
      <div v-if="searchFilteredOptions.length === 0" class="account-item no-result">
        검색 결과가 없습니다
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ledger-account-picker {
  position: fixed;
  background-color: white;
  border: 1px solid #d8dbe0;
  border-radius: 0.25rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  z-index: 10000;
  max-height: 320px;
  display: flex;
  flex-direction: column;
}

.search-input {
  border-bottom: 1px solid #d8dbe0;
  background-color: white;
}

.account-list {
  overflow-y: auto;
  max-height: 280px;
}

.account-item {
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.15s ease-in-out;

  &:hover:not(.category-only):not(.no-result) {
    background-color: #f8f9fa;
  }

  &.category-only {
    font-weight: 600;
    color: #6c757d;
    background-color: #e9ecef;
    cursor: default;
  }

  &.selected-item {
    span {
      color: #20c997;
      font-weight: 600;
    }
  }

  &.keyboard-active {
    background-color: rgba(27, 107, 100, 0.85) !important;
    color: white !important;
    font-weight: bold;

    span {
      color: white !important;
    }
  }

  &.no-result {
    color: #6c757d;
    text-align: center;
    cursor: default;
  }
}

// 다크 테마 지원
:global(body.dark-theme .ledger-account-picker) {
  background-color: #363740;
  border-color: #4a5568;
}

:global(body.dark-theme .search-input) {
  background-color: #363740;
  border-bottom-color: #4a5568;

  input.form-control {
    background-color: #282933;
    border-color: #4a5568;
    color: #e2e8f0;

    &::placeholder {
      color: #a0aec0;
    }

    &:focus {
      background-color: #2d3748;
      border-color: #3e3e3e;
      color: #e2e8f0;
    }
  }
}

:global(body.dark-theme .account-item) {
  color: #eeeeff !important;
}

:global(body.dark-theme .account-item:hover:not(.category-only):not(.no-result)) {
  background-color: #3b3c45;
}

:global(body.dark-theme .account-item.category-only) {
  color: #a8a8a8 !important;
  background-color: #474850 !important;
}
</style>
