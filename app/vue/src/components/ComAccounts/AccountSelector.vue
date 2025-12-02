<template>
  <div class="account-selector-wrapper">
    <!-- 모드 토글 버튼 -->
    <div v-if="showToggle" class="mb-2 d-flex justify-content-end">
      <div class="btn-group btn-group-sm" role="group">
        <button
          type="button"
          class="btn"
          :class="currentMode === 'search' ? 'btn-primary' : 'btn-outline-secondary'"
          @click="currentMode = 'search'"
        >
          <v-icon icon="mdi-magnify" size="x-small" />
          검색
        </button>
        <button
          type="button"
          class="btn"
          :class="currentMode === 'hierarchy' ? 'btn-primary' : 'btn-outline-secondary'"
          @click="currentMode = 'hierarchy'"
        >
          <v-icon icon="mdi-format-list-bulleted-square" size="x-small" />
          상세
        </button>
      </div>
    </div>

    <!-- 검색 모드 -->
    <template v-if="currentMode === 'search'">
      <AccountD3Search
        :modelValue="account_d3"
        :getAllD3List="getAllD3List"
        :getD3List="getD3List"
        :disabled="disabled"
        @update:modelValue="val => emit('update:accountD3', val)"
        @update:hierarchy="handleHierarchyUpdate"
      />
    </template>

    <!-- 계층 모드 -->
    <template v-else>
      <AccountSelectorGroup
        :fetchD1List="fetchD1List"
        :fetchD2List="fetchD2List"
        :fetchD3List="fetchD3List"
        :getD1List="getD1List"
        :getD2List="getD2List"
        :getD3List="getD3List"
        :initialValues="{ sort, account_d1, account_d2, account_d3 }"
        :autoInitialize="autoInitialize"
        @update:sort="val => emit('update:sort', val)"
        @update:accountD1="val => emit('update:accountD1', val)"
        @update:accountD2="val => emit('update:accountD2', val)"
        @update:accountD3="val => emit('update:accountD3', val)"
      >
        <slot />
      </AccountSelectorGroup>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import AccountSelectorGroup from './AccountSelectorGroup.vue'
import AccountD3Search from './AccountD3Search.vue'

interface Props {
  // 현재 선택된 값들
  sort?: 1 | 2
  account_d1?: number | null
  account_d2?: number | null
  account_d3?: number | null

  // 계층 모드용 함수들
  fetchD1List: (sort: number) => Promise<void>
  fetchD2List: (d1: number) => Promise<void>
  fetchD3List: (d2: number) => Promise<void>
  getD1List: () => any[]
  getD2List: () => any[]
  getD3List: () => any[]

  // 검색 모드용 함수
  getAllD3List: () => Promise<void>

  // 옵션
  defaultMode?: 'search' | 'hierarchy'
  showToggle?: boolean
  autoInitialize?: boolean
  disabled?: boolean
}

interface Emits {
  (e: 'update:sort', value: 1 | 2): void
  (e: 'update:accountD1', value: number | null): void
  (e: 'update:accountD2', value: number | null): void
  (e: 'update:accountD3', value: number | null): void
}

const props = withDefaults(defineProps<Props>(), {
  sort: 1,
  account_d1: null,
  account_d2: null,
  account_d3: null,
  defaultMode: 'search',
  showToggle: true,
  autoInitialize: true,
  disabled: false,
})

const emit = defineEmits<Emits>()

const currentMode = ref<'search' | 'hierarchy'>(props.defaultMode)

// 검색 모드에서 계층 선택 시
const handleHierarchyUpdate = (d1: number | null, d2: number | null, d3: number | null) => {
  emit('update:accountD1', d1)
  emit('update:accountD2', d2)
  emit('update:accountD3', d3)
}

// 모드 변경 시 초기화 필요하면 처리
watch(currentMode, async newMode => {
  if (newMode === 'hierarchy' && props.autoInitialize) {
    // 계층 모드로 전환 시 필요한 초기화
    if (props.sort) {
      await props.fetchD1List(props.sort)
    }
    if (props.account_d1) {
      await props.fetchD2List(props.account_d1)
    }
    if (props.account_d2) {
      await props.fetchD3List(props.account_d2)
    }
  }
})
</script>

<style scoped>
.account-selector-wrapper {
  width: 100%;
}
</style>
