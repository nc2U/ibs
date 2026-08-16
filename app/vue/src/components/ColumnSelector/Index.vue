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
  if (!selectedSelected.value.length) return
  const toRemove = selectedSelected.value.filter(
    key => !props.allColumns.find(c => c.key === key)?.fixed,
  )
  const updated = props.modelValue.filter(k => !toRemove.includes(k))
  emit('update:modelValue', updated)
  selectedSelected.value = []
}

const removeSingleColumn = (key: string) => {
  const col = props.allColumns.find(c => c.key === key)
  if (col?.fixed) return
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

const moveTop = () => {
  if (selectedSelected.value.length !== 1) return
  const targetKey = selectedSelected.value[0]
  const idx = props.modelValue.indexOf(targetKey)
  if (idx > 0) {
    const updated = props.modelValue.filter(k => k !== targetKey)
    updated.unshift(targetKey)
    emit('update:modelValue', updated)
  }
}

const moveUp = () => {
  if (selectedSelected.value.length !== 1) return
  const targetKey = selectedSelected.value[0]
  const idx = props.modelValue.indexOf(targetKey)
  if (idx > 0) {
    const updated = [...props.modelValue]
    const temp = updated[idx - 1]
    updated[idx - 1] = updated[idx]
    updated[idx] = temp
    emit('update:modelValue', updated)
  }
}

const moveDown = () => {
  if (selectedSelected.value.length !== 1) return
  const targetKey = selectedSelected.value[0]
  const idx = props.modelValue.indexOf(targetKey)
  if (idx >= 0 && idx < props.modelValue.length - 1) {
    const updated = [...props.modelValue]
    const temp = updated[idx + 1]
    updated[idx + 1] = updated[idx]
    updated[idx] = temp
    emit('update:modelValue', updated)
  }
}

const moveBottom = () => {
  if (selectedSelected.value.length !== 1) return
  const targetKey = selectedSelected.value[0]
  const idx = props.modelValue.indexOf(targetKey)
  if (idx >= 0 && idx < props.modelValue.length - 1) {
    const updated = props.modelValue.filter(k => k !== targetKey)
    updated.push(targetKey)
    emit('update:modelValue', updated)
  }
}
</script>

<template>
  <CRow class="m-2 align-items-center" color="light">
    <!-- 가능한 컬럼 -->
    <CCol col="12" md="5" lg="4">
      <label class="form-label text-caption font-weight-bold text-muted mb-1">
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
      class="text-center d-flex flex-row flex-md-column justify-content-center align-items-center gap-1 my-2 my-md-0 pt-4"
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
        :disabled="!selectedSelected.length"
        @click="removeColumns"
      />
    </CCol>

    <!-- 선택된 컬럼 & 순서 이동 -->
    <CCol col="12" md="5" lg="4" class="d-flex align-items-center">
      <div class="flex-grow-1">
        <label class="form-label text-caption font-weight-bold text-indigo mb-1">
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
      <div class="d-flex flex-column gap-1 ml-2 pt-4">
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-double-up"
          title="맨 위로 이동"
          :disabled="selectedSelected.length !== 1"
          @click="moveTop"
        />
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-up"
          title="위로 이동"
          :disabled="selectedSelected.length !== 1"
          @click="moveUp"
        />
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-down"
          title="아래로 이동"
          :disabled="selectedSelected.length !== 1"
          @click="moveDown"
        />
        <v-btn
          size="x-small"
          color="indigo"
          variant="outlined"
          icon="mdi-chevron-double-down"
          title="맨 아래로 이동"
          :disabled="selectedSelected.length !== 1"
          @click="moveBottom"
        />
      </div>
    </CCol>
  </CRow>
</template>

<style scoped lang="scss">
select {
  height: 9rem;
}
</style>
