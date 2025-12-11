<script lang="ts" setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'

interface Props {
  options: Array<{
    value: number
    label: string
    parent: number | null
    is_cate_only: boolean
    depth?: number
    direction?: string
  }>
  modelValue?: number | null
  placeholder?: string
  filterType?: 'deposit' | 'withdraw' | null
}

interface Emits {
  (e: 'update:modelValue', value: number | null): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '회계 계정',
})

const emit = defineEmits<Emits>()

const searchInputRef = ref<HTMLInputElement | null>(null)
const dropdownRef = ref<any>(null)
const menuRef = ref<HTMLElement | null>(null)
const toggleRef = ref<HTMLElement | null>(null)

// 드롭다운 상태
const dropdownVisible = ref(false)
const searchQuery = ref('')
const selectedIndex = ref(-1)

// 드롭다운 메뉴 위치
const menuPosition = ref({ top: 0, left: 0, width: 0 })

// 한글 IME 입력 중에도 즉시 반영
const handleInput = (event: Event) => {
  searchQuery.value = (event.target as HTMLInputElement).value
  selectedIndex.value = -1 // 검색 시 선택 초기화
}

// 필터링된 옵션 생성
const filteredOptions = computed(() => {
  let filtered = props.options

  // filterType에 따른 필터링
  if (props.filterType) {
    const targetDirection = props.filterType === 'deposit' ? '입금' : '출금'

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
        !props.filterType || // 필터 없으면 전체
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

// 현재 선택된 옵션의 표시 텍스트
const selectedLabel = computed(() => {
  if (!props.modelValue) return ''
  const selected = props.options.find(opt => opt.value === props.modelValue)
  return selected ? selected.label : ''
})

// 옵션 선택 처리
const selectOption = (option: any) => {
  if (!option.is_cate_only) {
    emit('update:modelValue', option.value)

    // v-model, hide()가 모두 동작하지 않는 비정상적인 상황이므로,
    // 최후의 수단으로 토글 버튼을 직접 찾아 클릭 이벤트를 발생시켜 팝업을 닫습니다.
    const dropdownEl = (dropdownRef.value as any)?.$el
    if (dropdownEl) {
      const toggleButton = dropdownEl.querySelector('.dropdown-toggle') as HTMLElement
      if (toggleButton) {
        toggleButton.click()
      }
    }
  }
}

// 선택 가능한 옵션들 (is_cate_only 제외)
const selectableOptions = computed(() => {
  return searchFilteredOptions.value.filter(opt => !opt.is_cate_only)
})

// 키보드 네비게이션 처리
const handleKeyDown = (event: KeyboardEvent) => {
  // dropdownVisible 상태가 v-model을 통해 동기화되지 않는 것으로 보여 이 가드를 제거합니다.
  // if (!dropdownVisible.value) return

  const scrollIntoView = () => {
    nextTick(() => {
      const menuEl = (menuRef.value as any)?.$el
      if (!menuEl) return
      const activeEl = menuEl.querySelector('.keyboard-active') as HTMLElement
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' })
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
      dropdownVisible.value = false
      break
  }
}

// 검색 초기화
const clearSearch = () => {
  searchQuery.value = ''
  selectedIndex.value = -1
}

// 드롭다운 메뉴 위치 계산
const updateMenuPosition = () => {
  const dropdownEl = (dropdownRef.value as any)?.$el
  if (!dropdownEl) return

  const toggleButton = dropdownEl.querySelector('.dropdown-toggle') as HTMLElement
  if (!toggleButton) return

  const rect = toggleButton.getBoundingClientRect()
  menuPosition.value = {
    top: rect.bottom + window.scrollY,
    left: rect.left + window.scrollX,
    width: rect.width,
  }
}

const onDropdownShow = () => {
  clearSearch()
  updateMenuPosition()

  // nextTick과 setTimeout을 함께 사용하여 DOM 렌더링 및 포커스 타이밍 보장
  nextTick(() => {
    setTimeout(() => {
      // 1. 검색창에 포커스
      if (searchInputRef.value) {
        ;(searchInputRef.value as any).focus()
      }

      // 2. 선택된 항목으로 스크롤
      const menuEl = (menuRef.value as any)?.$el // 컴포넌트의 실제 DOM 엘리먼트 접근
      if (menuEl) {
        const selectedEl = menuEl.querySelector('.selected-item') as HTMLElement
        if (selectedEl) {
          selectedEl.scrollIntoView({ block: 'nearest' })
        }
      }
    }, 100)
  })
}

// 드롭다운 토글
const toggleDropdown = () => {
  dropdownVisible.value = !dropdownVisible.value
  if (dropdownVisible.value) {
    nextTick(() => {
      clearSearch()
    })
  }
}

// 외부 클릭 감지
const handleClickOutside = (event: MouseEvent) => {
  if (!dropdownVisible.value) return

  const menuEl = (menuRef.value as any)?.$el
  const dropdownEl = (dropdownRef.value as any)?.$el
  const target = event.target as Node

  // 드롭다운 토글 버튼 또는 메뉴 내부 클릭이 아닌 경우에만 닫기
  if (
    dropdownEl &&
    !dropdownEl.contains(target) &&
    menuEl &&
    !menuEl.contains(target)
  ) {
    dropdownVisible.value = false
  }
}

// 스크롤 시 메뉴 위치 업데이트
const handleScroll = () => {
  if (dropdownVisible.value) {
    updateMenuPosition()
  }
}

// 리사이즈 시 메뉴 위치 업데이트
const handleResize = () => {
  if (dropdownVisible.value) {
    updateMenuPosition()
  }
}

// 라이프사이클 훅
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('scroll', handleScroll, true)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', handleScroll, true)
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <CDropdown
    ref="dropdownRef"
    v-model="dropdownVisible"
    variant="btn-group"
    :auto-close="false"
    @show="onDropdownShow"
    style="width: 100%"
  >
    <CDropdownToggle class="form-select text-start" :class="{ 'text-muted': !selectedLabel }">
      {{ selectedLabel || placeholder }}
    </CDropdownToggle>

    <CDropdownMenu
      ref="menuRef"
      :style="{
        maxHeight: '300px',
        overflowY: 'auto',
        top: `${menuPosition.top}px`,
        left: `${menuPosition.left}px`,
        width: `${menuPosition.width}px`,
      }"
    >
      <!-- 검색 입력 -->
      <div class="p-2 border-bottom" @click.stop @mousedown.stop>
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
          'category-only': option.is_cate_only,
          'selected-item': option.value === modelValue,
          'keyboard-active': selectableOptions[selectedIndex]?.value === option.value,
        }"
        :disabled="option.is_cate_only"
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
</template>

<style lang="scss" scoped>
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

:deep(.dropdown-toggle) {
  border: 1px solid var(--border-color, #d8dbe0);
  background-color: var(--background-color, white);
  color: var(--text-color, inherit);
}

:deep(.dropdown-toggle:focus) {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(114, 114, 114, 0.25);
}
:deep(.keyboard-active) {
  background-color: rgba(27, 107, 100, 0.85) !important;
  font-weight: bold;
  color: white !important;
}

/* Dark theme support */
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
