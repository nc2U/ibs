<script lang="ts" setup>
import { computed } from 'vue'
import Multiselect from '@vueform/multiselect'

interface Props {
  options: Array<{
    value: number
    label: string
    parent: number | null
    is_cate: boolean
    depth?: number
    direction?: string
  }>
  modelValue?: number
  placeholder?: string
  filterType?: 'deposit' | 'withdraw' | null
}

interface Emits {
  (e: 'update:modelValue', value: number): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '회계 계정',
})

const emit = defineEmits<Emits>()

// 필터링된 옵션 생성
const filteredOptions = computed(() => {
  let filtered = props.options

  // filterType에 따른 필터링
  if (props.filterType) {
    const targetDirection = props.filterType === 'deposit' ? '입금' : '출금'

    // 1. 조건에 맞는 실제 계정들만 필터링
    const matchingAccounts = filtered.filter(
      option => !option.is_cate && option.direction === targetDirection,
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
          currentParent = currentOption.parent
          currentOption = filtered.find(opt => opt.value === currentParent)
        }
      }
    })

    // 3. 매칭된 계정들 + 필요한 부모들만 포함
    filtered = filtered.filter(
      option =>
        !props.filterType || // 필터 없으면 전체
        (!option.is_cate && option.direction === targetDirection) || // 조건 맞는 실제 계정
        (option.is_cate && neededParents.has(option.value)), // 필요한 부모 카테고리만
    )
  }

  return filtered
})

// Tree 구조로 변환된 옵션 생성
const treeOptions = computed(() => {
  return filteredOptions.value.map(option => ({
    value: option.value,
    label: '　'.repeat((option.depth || 0) - 1) + option.label, // 들여쓰기
    disabled: option.is_cate, // 카테고리는 disabled
    $isLabel: option.is_cate, // 카테고리 표시용
  }))
})

const value = computed({
  get: () => props.modelValue,
  set: val => emit('update:modelValue', val),
})
</script>

<template>
  <Multiselect
    v-model="value"
    mode="single"
    :placeholder="placeholder"
    :options="treeOptions"
    :classes="{
      option: 'multiselect-option',
      optionDisabled: 'multiselect-option-disabled',
      search: 'form-control multiselect-search',
    }"
    searchable
  />
</template>

<style scoped>
:deep(.multiselect-option-disabled) {
  color: #6c757d;
  font-weight: 500;
  cursor: auto;
  background-color: #f8f9fa;
}

:deep(.multiselect-option-disabled:hover) {
  background-color: #f8f9fa;
}

/* Dark theme support */
:global(body.dark-theme) :deep(.multiselect-option-disabled) {
  color: #adb5bd;
  background-color: #343a40;
}

:global(body.dark-theme) :deep(.multiselect-option-disabled:hover) {
  background-color: #343a40;
}
</style>
