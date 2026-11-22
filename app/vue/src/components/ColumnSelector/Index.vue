<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'

export interface ColumnOption {
  key: string
  label: string
  fixed?: boolean
}

const props = defineProps({
  modelValue: { type: Array as PropType<string[]>, required: true },
  allColumns: { type: Array as PropType<ColumnOption[]>, required: true },
  availableLabel: { type: String, default: '가능한 컬럼' },
  selectedLabel: { type: String, default: '선택된 컬럼' },
  size: { type: Number, default: 5 },
})

const emit = defineEmits(['update:modelValue'])

const availableSelected = ref<string[]>([])
const selectedSelected = ref<string[]>([])

const availableItems = computed(() =>
  props.allColumns.filter(c => !props.modelValue.includes(c.key)),
)

const selectedItems = computed(() =>
  props.modelValue
    .map(key => props.allColumns.find(c => c.key === key))
    .filter((c): c is ColumnOption => !!c),
)

const fixedKeys = computed(() => new Set(props.allColumns.filter(c => c.fixed).map(c => c.key)))

const selectedIndex = computed(() => {
  if (selectedSelected.value.length !== 1) return -1
  return props.modelValue.indexOf(selectedSelected.value[0])
})

const canRemove = computed(() => selectedSelected.value.some(k => !fixedKeys.value.has(k)))
const canMoveUp = computed(() => selectedIndex.value > 0)
const canMoveDown = computed(
  () => selectedIndex.value >= 0 && selectedIndex.value < props.modelValue.length - 1,
)

const addColumns = () => {
  if (!availableSelected.value.length) return
  const updated = [...props.modelValue, ...availableSelected.value]
  emit('update:modelValue', updated)
  availableSelected.value = []
}

const addSingleColumn = (key: string) => {
  if (!props.modelValue.includes(key)) {
    emit('update:modelValue', [...props.modelValue, key])
    availableSelected.value = availableSelected.value.filter(k => k !== key)
  }
}

const removeColumns = () => {
  if (!canRemove.value) return
  const toRemove = selectedSelected.value.filter(key => !fixedKeys.value.has(key))
  const updated = props.modelValue.filter(k => !toRemove.includes(k))
  emit('update:modelValue', updated)
  selectedSelected.value = []
}

const removeSingleColumn = (key: string) => {
  if (fixedKeys.value.has(key)) return
  emit(
    'update:modelValue',
    props.modelValue.filter(k => k !== key),
  )
  selectedSelected.value = selectedSelected.value.filter(k => k !== key)
}

const onAvailableDblClick = (event: MouseEvent) => {
  const target = event.target as HTMLOptionElement | null
  if (target && target.tagName === 'OPTION' && target.value) {
    addSingleColumn(target.value)
  } else if (availableSelected.value.length === 1) {
    addSingleColumn(availableSelected.value[0])
  }
}

const onSelectedDblClick = (event: MouseEvent) => {
  const target = event.target as HTMLOptionElement | null
  if (target && target.tagName === 'OPTION' && target.value) {
    removeSingleColumn(target.value)
  } else if (selectedSelected.value.length === 1) {
    removeSingleColumn(selectedSelected.value[0])
  }
}

const moveBy = (delta: -1 | 1) => {
  const idx = selectedIndex.value
  const targetIdx = idx + delta
  if (idx < 0 || targetIdx < 0 || targetIdx >= props.modelValue.length) return
  const updated = [...props.modelValue]
  ;[updated[idx], updated[targetIdx]] = [updated[targetIdx], updated[idx]]
  emit('update:modelValue', updated)
}

const moveToEdge = (edge: 'top' | 'bottom') => {
  const idx = selectedIndex.value
  if (idx < 0) return
  if (edge === 'top' && idx === 0) return
  if (edge === 'bottom' && idx === props.modelValue.length - 1) return
  const targetKey = props.modelValue[idx]
  const rest = props.modelValue.filter(k => k !== targetKey)
  emit('update:modelValue', edge === 'top' ? [targetKey, ...rest] : [...rest, targetKey])
}
</script>

<template>
  <CRow class="m-2 align-items-center">
    <!-- 가능한 컬럼 -->
    <CCol col="12" md="5" lg="4">
      <label class="form-label text-caption fw-bold text-muted mb-1">
        {{ availableLabel }}
      </label>
      <select
        v-model="availableSelected"
        multiple
        class="form-select text-caption"
        :size="size"
        @dblclick="onAvailableDblClick"
      >
        <option
          v-for="item in availableItems"
          :key="item.key"
          :value="item.key"
          @dblclick.stop="addSingleColumn(item.key)"
        >
          {{ item.label }}
        </option>
      </select>
    </CCol>

    <!-- 중앙 이동 버튼 -->
    <CCol
      col="12"
      md="2"
      lg="1"
      class="text-center d-flex flex-row flex-md-column justify-content-center align-items-center gap-1 my-2 my-md-0 pt-md-4"
    >
      <v-btn
        size="x-small"
        color="secondary"
        variant="outlined"
        icon="mdi-chevron-right"
        title="추가"
        :disabled="!availableSelected.length"
        @click="addColumns"
      />
      <v-btn
        size="x-small"
        color="secondary"
        variant="outlined"
        icon="mdi-chevron-left"
        title="제거"
        :disabled="!canRemove"
        @click="removeColumns"
      />
    </CCol>

    <!-- 선택된 컬럼 & 순서 이동 -->
    <CCol col="12" md="5" lg="4" class="d-flex align-items-center">
      <div class="flex-grow-1">
        <label class="form-label text-caption fw-bold text-indigo mb-1">
          {{ selectedLabel }}
        </label>
        <select
          v-model="selectedSelected"
          multiple
          class="form-select text-caption"
          :size="size"
          @dblclick="onSelectedDblClick"
        >
          <option
            v-for="item in selectedItems"
            :key="item.key"
            :value="item.key"
            :disabled="item.fixed"
            @dblclick.stop="removeSingleColumn(item.key)"
          >
            {{ item.label }} {{ item.fixed ? '(필수)' : '' }}
          </option>
        </select>
      </div>
      <div class="d-flex flex-column gap-1 ms-2 pt-4">
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-double-up"
          title="맨 위로 이동"
          :disabled="!canMoveUp"
          @click="moveToEdge('top')"
        />
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-up"
          title="위로 이동"
          :disabled="!canMoveUp"
          @click="moveBy(-1)"
        />
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-down"
          title="아래로 이동"
          :disabled="!canMoveDown"
          @click="moveBy(1)"
        />
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-double-down"
          title="맨 아래로 이동"
          :disabled="!canMoveDown"
          @click="moveToEdge('bottom')"
        />
      </div>
    </CCol>
  </CRow>
</template>

<style scoped lang="scss">
select {
  min-height: 9rem;
}
</style>
