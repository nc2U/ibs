<script lang="ts" setup>
import { computed, inject, nextTick, onMounted, onUnmounted, ref, type Ref } from 'vue'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import {
  filterAccountOptions,
  searchAccountOptions,
  type AccountCateType,
  type AccountSortType,
} from './accountFilterUtils'

interface ComponentElRef {
  $el?: HTMLElement
}

interface Props {
  options: Array<AccountPicker>
  modelValue?: number | null
  placeholder?: string
  cateType?: AccountCateType
  sortType?: AccountSortType
  isSearch?: boolean
  required?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '회계 계정',
  isSearch: false,
  required: false,
})

interface Emits {
  (e: 'update:modelValue', value: number | null): void
}

const emit = defineEmits<Emits>()

const clearSelection = () => {
  emit('update:modelValue', null)
}

const searchInputRef = ref<HTMLInputElement | null>(null)
const dropdownRef = ref<ComponentElRef | null>(null)
const menuRef = ref<ComponentElRef | null>(null)
const toggleRef = ref<ComponentElRef | null>(null)
let focusTimer: ReturnType<typeof setTimeout> | undefined

const validated = inject<Ref<boolean>>('validated', ref(false))
const isInvalid = computed(() => {
  return props.required && validated.value && !props.modelValue
})
const isValid = computed(() => {
  return validated.value && !isInvalid.value
})

// 드롭다운 상태
const dropdownVisible = ref(false)
const searchQuery = ref('')
const selectedIndex = ref(-1)

// 한글 IME 입력 중에도 즉시 반영
const handleInput = (event: Event) => {
  searchQuery.value = (event.target as HTMLInputElement).value
  selectedIndex.value = -1 // 검색 시 선택 초기화
}

// 필터링된 옵션 생성
const filteredOptions = computed(() =>
  filterAccountOptions(props.options, { cateType: props.cateType, sortType: props.sortType }),
)

// 검색 결과 필터링 (부모-자식 관계 포함)
const searchFilteredOptions = computed(() =>
  searchAccountOptions(filteredOptions.value, searchQuery.value),
)

// 현재 선택된 옵션의 표시 텍스트
const selectedLabel = computed(() => {
  if (!props.modelValue) return ''
  const selected = props.options.find(opt => opt.value === props.modelValue)
  return selected ? selected.label : ''
})

// 옵션 선택 처리
const selectOption = (option: AccountPicker) => {
  // 검색 모드가 아닐 때만 카테고리 전용 항목 선택 차단
  if (!option.is_cate_only || props.isSearch) {
    emit('update:modelValue', option.value)
    closeDropdown()
  }
}

// 선택 가능한 옵션들 (검색 모드가 아닐 때만 is_cate_only 제외)
const selectableOptions = computed(() => {
  if (props.isSearch) {
    // 검색 모드: 모든 항목 선택 가능
    return searchFilteredOptions.value
  }
  // 일반 모드: 카테고리 전용 항목 제외
  return searchFilteredOptions.value.filter(opt => !opt.is_cate_only)
})

// 드롭다운 닫기 함수
const closeDropdown = () => {
  dropdownVisible.value = false
  const dropdownEl = dropdownRef.value?.$el
  if (dropdownEl) {
    const toggleButton = dropdownEl.querySelector('.dropdown-toggle') as HTMLElement | null
    if (toggleButton && toggleButton.getAttribute('aria-expanded') === 'true') {
      toggleButton.click()
    }
  }
}

// 키보드 네비게이션 처리
const handleKeyDown = (event: KeyboardEvent) => {
  const scrollIntoView = () => {
    nextTick(() => {
      const menuEl = menuRef.value?.$el
      if (!menuEl) return
      const activeEl = menuEl.querySelector('.keyboard-active') as HTMLElement | null
      const searchContainer = menuEl.querySelector('.search-container') as HTMLElement | null

      if (activeEl) {
        // 메뉴 컨테이너 내부에서만 스크롤, 페이지 전체 스크롤 방지
        const menuRect = menuEl.getBoundingClientRect()
        const activeRect = activeEl.getBoundingClientRect()
        const searchHeight = searchContainer ? searchContainer.offsetHeight : 0

        if (activeRect.top < menuRect.top + searchHeight) {
          menuEl.scrollTop -= menuRect.top + searchHeight - activeRect.top
        } else if (activeRect.bottom > menuRect.bottom) {
          menuEl.scrollTop += activeRect.bottom - menuRect.bottom
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
      closeDropdown()
      break
  }
}

// 검색 초기화
const clearSearch = () => {
  searchQuery.value = ''
  selectedIndex.value = -1
}

const onDropdownShow = () => {
  dropdownVisible.value = true
  clearSearch()

  // nextTick과 setTimeout을 함께 사용하여 DOM 렌더링 및 포커스 타이밍 보장
  nextTick(() => {
    clearTimeout(focusTimer)
    focusTimer = setTimeout(() => {
      // 1. 검색창에 포커스
      searchInputRef.value?.focus()

      // 2. 선택된 항목으로 스크롤 (메뉴 내부에서만)
      const menuEl = menuRef.value?.$el
      if (menuEl) {
        const selectedEl = menuEl.querySelector('.selected-item') as HTMLElement | null
        if (selectedEl) {
          menuEl.scrollTop = Math.max(
            0,
            selectedEl.offsetTop - menuEl.clientHeight / 2 + selectedEl.clientHeight / 2,
          )
        }
      }
    }, 100)
  })
}

const onDropdownHide = () => {
  dropdownVisible.value = false
}

// 외부 클릭 감지
const handleClickOutside = (event: MouseEvent) => {
  if (!dropdownVisible.value) return

  const target = event.target as Node
  const menuEl = menuRef.value?.$el
  const toggleEl = toggleRef.value?.$el

  if (toggleEl && toggleEl.contains(target)) {
    return
  }

  if (menuEl && menuEl.contains(target)) {
    return
  }

  if (toggleEl) {
    toggleEl.click()
  }
}

// 라이프사이클 훅
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  clearTimeout(focusTimer)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div style="position: relative; width: 100%">
    <CDropdown
      ref="dropdownRef"
      v-model="dropdownVisible"
      variant="btn-group"
      :auto-close="false"
      @show="onDropdownShow"
      @hide="onDropdownHide"
      style="width: 100%"
    >
      <CDropdownToggle
        ref="toggleRef"
        class="form-select text-start"
        :class="{ 'text-muted': !selectedLabel, 'is-invalid': isInvalid, 'is-valid': isValid }"
      >
        {{ selectedLabel || placeholder }}
      </CDropdownToggle>

      <CDropdownMenu ref="menuRef" class="pt-0" style="max-height: 300px; overflow-y: auto">
        <!-- 검색 입력 -->
        <div class="search-container p-2 border-bottom" @click.stop @mousedown.stop>
          <input
            ref="searchInputRef"
            :value="searchQuery"
            type="text"
            class="form-control form-control-sm"
            placeholder="검색..."
            @input="handleInput"
            @keydown="handleKeyDown"
            @click.stop
            @mousedown.stop
          />
        </div>

        <!-- 옵션 리스트 -->
        <CDropdownItem
          v-for="option in searchFilteredOptions"
          :key="option.value"
          :class="{
            'text-muted fw-semibold': option.is_cate_only,
            'bg-light': option.is_cate_only,
            'category-only': !isSearch && option.is_cate_only,
            'selected-item': option.value === modelValue,
            'keyboard-active': selectableOptions[selectedIndex]?.value === option.value,
          }"
          :disabled="!isSearch && option.is_cate_only"
          @click="selectOption(option)"
        >
          <span :style="`padding-left: ${(option.depth || 0) * 12}px`">
            {{ option.label }}
          </span>
        </CDropdownItem>

        <!-- 검색 결과가 없을 때 -->
        <CDropdownItem v-if="searchFilteredOptions.length === 0" disabled>
          검색 결과가 없습니다
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>

    <!-- 초기화(x) 버튼 추가 -->
    <button
      v-if="props.modelValue"
      type="button"
      class="clear-button"
      aria-label="Clear selection"
      @click.stop="clearSelection"
    >
      &times;
    </button>
  </div>
</template>

<style lang="scss" scoped>
/* 초기화 버튼 스타일 */
.clear-button {
  position: absolute;
  top: 46%;
  right: 35px; /* 드롭다운 화살표와 겹치지 않도록 조정 */
  transform: translateY(-50%);
  border: none;
  background: transparent;
  padding: 0 0.5rem;
  margin: 0;
  font-size: 1.3rem;
  line-height: 1;
  cursor: pointer;
  color: #888;
  z-index: 10; /* 드롭다운 토글 위에 위치하도록 */
}

.clear-button:hover {
  color: #333;
}

/* 다크 모드일 때 초기화 버튼 색상 */
:global(body.dark-theme) .clear-button {
  color: #bbb;
}
:global(body.dark-theme) .clear-button:hover {
  color: #fff;
}

/* 검색창 고정 */
.search-container {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: white;
}

.category-only,
.dropdown-item-disabled {
  pointer-events: none;
  cursor: text;
  color: #8c8c8c !important;
  background-color: #dddddd !important;
}

.selected-item > span {
  color: #20c997 !important;
  font-weight: 600;
}

:deep(.dropdown),
:deep(.btn-group) {
  overflow: visible !important;
}

:deep(.dropdown-menu) {
  width: 100% !important;
  position: absolute !important;
  z-index: 1050 !important;
}

:deep(.dropdown-toggle) {
  border: 1px solid var(--border-color, #d8dbe0);
  background-color: var(--background-color, white);
  color: var(--text-color, inherit);
}

:deep(.dropdown-toggle:focus) {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(114, 114, 114, 0.25);
}

:deep(.dropdown-toggle.is-invalid) {
  border-color: #dc3545 !important;
  //#box-shadow: 0 0 0 0.25rem rgba(220, 53, 69, 0.25) !important;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 13 13' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5' stroke-width='1'/%3e%3cpath d='M6 9h.01M6 3v4' stroke-width='1.5' stroke-linecap='round'/%3e%3c/svg%3e") !important;
  background-repeat: no-repeat !important;
  background-position: right calc(0.375em + 0.1875rem) center !important;
  background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
  padding-right: calc(1.5em + 0.75rem) !important;
}

:deep(.dropdown-toggle.is-valid) {
  border-color: #2eb85c !important;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 9 9'%3e%3cpath fill='%232eb85c' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e") !important;
  background-repeat: no-repeat !important;
  background-position: right calc(0.375em + 0.1875rem) center !important;
  background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem) !important;
  padding-right: calc(1.5em + 0.75rem) !important;
}

:deep(.dropdown-toggle.is-valid:focus) {
  box-shadow: 0 0 0 0.25rem rgba(46, 184, 92, 0.25) !important;
}
:deep(.keyboard-active) {
  background-color: rgba(27, 107, 100, 0.85) !important;
  font-weight: bold;
  color: white !important;
}

/* Dark theme support */
:global(body.dark-theme .search-container) {
  background-color: #363740 !important;
}

:global(body.dark-theme .category-only),
:global(body.dark-theme .dropdown-item.text-muted) {
  color: #a8a8a8 !important;
  background-color: #474850 !important;
}

:global(body.dark-theme) {
  .bg-light {
    background-color: #4a5568 !important;
  }
  /* 검색 input 스타일 */
  input.form-control {
    background-color: #2d3748;
    border-color: #4a5568;
    color: #e2e8f0;
  }
  input.form-control::placeholder {
    color: #a0aec0;
  }
  input.form-control:focus {
    background-color: #2d3748;
    border-color: #86b7fe;
    color: #e2e8f0;
  }
  .selected-item > span {
    color: #63e6be !important;
  }

  :deep(.dropdown-toggle) {
    --background-color: #474850 !important;
    --border-color: #4a5568;
    --color: #cdcdcf;
  }
  :deep(.dropdown-menu) {
    background-color: #2d3748;
    border-color: #4a5568;
  }
  :deep(.dropdown-item) {
    color: #e2e8f0;
  }
  :deep(.dropdown-item:hover) {
    background-color: #4a5568;
  }
}
</style>
