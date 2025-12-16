<script lang="ts" setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { Account } from '@/store/types/comLedger.ts'

interface Props {
  options: Array<Account>
  modelValue?: number | null
  sortType?: 'deposit' | 'withdraw' | null
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

// 한글 IME 입력 중에도 즉시 반영
const handleInput = (event: Event) => {
  searchQuery.value = (event.target as HTMLInputElement).value
  selectedIndex.value = -1 // 검색 시 선택 초기화
}

// 필터링된 옵션 생성
const filteredOptions = computed(() => {
  let filtered = props.options

  // sortType에 따른 필터링
  if (props.sortType) {
    const targetDirection = props.sortType === 'deposit' ? '입금' : '출금'

    // 1. 조건에 맞는 실제 계정들만 필터링
    const matchingAccounts = filtered.filter(
      option => !option.is_cate_only && option.direction === targetDirection,
    )

    // 2. 매칭된 계정들의 부모 계정들 수집
    const neededParents = new Set<number>()
    matchingAccounts.forEach(account => {
      if (account.parent) {
        // 부모 체인을 따라 올라가며 모든 부모 수집
        let currentParent = account.parent
        let currentOption = filtered.find(opt => opt.value === currentParent)

        while (currentOption) {
          neededParents.add(currentOption.value)
          if (currentOption.parent === null) break
          currentParent = currentOption.parent
          currentOption = filtered.find(opt => opt.value === currentParent)
        }
      }
    })

    // 3. 매칭된 계정들 + 필요한 부모들만 포함
    filtered = filtered.filter(
      option =>
        !props.sortType || // 필터 없으면 전체
        (!option.is_cate_only && option.direction === targetDirection) || // 조건 맞는 실제 계정
        (option.is_cate_only && neededParents.has(option.value)), // 필요한 부모 카테고리만
    )
  }

  return filtered
})

// 검색 결과 필터링 (부모-자식 관계 포함)
const searchFilteredOptions = computed(() => {
  if (!searchQuery.value.trim()) return filteredOptions.value

  const query = searchQuery.value.toLowerCase()
  const matchingOptions = new Set<number>()

  // 1. 검색어에 직접 매치되는 옵션들 찾기
  filteredOptions.value.forEach(option => {
    if (option.label.toLowerCase().includes(query)) {
      matchingOptions.add(option.value)

      // 매치된 옵션의 모든 부모들 추가
      if (option.parent) {
        let currentParent = option.parent
        let parentOption = filteredOptions.value.find(opt => opt.value === currentParent)

        while (parentOption) {
          matchingOptions.add(parentOption.value)
          if (parentOption.parent === null) break
          currentParent = parentOption.parent
          parentOption = filteredOptions.value.find(opt => opt.value === currentParent)
        }
      }
    }
  })

  // 2. 자식이 매치된 경우 부모도 표시
  filteredOptions.value.forEach(option => {
    if (option.is_cate_only) {
      const hasMatchingChildren = filteredOptions.value.some(
        child => child.parent === option.value && matchingOptions.has(child.value),
      )
      if (hasMatchingChildren) {
        matchingOptions.add(option.value)
      }
    }
  })

  return filteredOptions.value.filter(option => matchingOptions.has(option.value))
})

// 선택 가능한 옵션들 (카테고리 전용 항목 제외)
const selectableOptions = computed(() => {
  return searchFilteredOptions.value.filter(opt => !opt.is_cate_only)
})

// 옵션 선택 처리
const selectOption = (option: Account) => {
  if (!option.is_cate_only) {
    emit('update:modelValue', option.value)
    emit('close')
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

// visible 변경 시 처리
watch(
  () => props.visible,
  newVal => {
    if (newVal) {
      searchQuery.value = ''
      selectedIndex.value = -1
      nextTick(() => {
        searchInputRef.value?.focus()
      })
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
})

onUnmounted(() => {
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
        v-for="(option, index) in searchFilteredOptions"
        :key="option.value"
        :class="{
          'account-item': true,
          'category-only': option.is_cate_only,
          'selected-item': option.value === modelValue,
          'keyboard-active': selectableOptions[selectedIndex]?.value === option.value,
        }"
        @click="selectOption(option)"
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
:global(body.dark-theme) {
  .ledger-account-picker {
    background-color: #2d3748;
    border-color: #4a5568;
  }

  .search-input {
    background-color: #3b3c45;
    border-bottom-color: #4a5568;

    input.form-control {
      background-color: #2d3748;
      border-color: #4a5568;
      color: #e2e8f0;

      &::placeholder {
        color: #a0aec0;
      }

      &:focus {
        background-color: #2d3748;
        border-color: #86b7fe;
        color: #e2e8f0;
      }
    }
  }

  .account-item {
    color: #e2e8f0;

    &:hover:not(.category-only):not(.no-result) {
      background-color: #4a5568;
    }

    &.category-only {
      color: #a8a8a8;
      background-color: #2c2d38;
    }

    &.selected-item span {
      color: #63e6be !important;
    }

    &.no-result {
      color: #a0aec0;
    }
  }
}
</style>
