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

const removeColumns = () => {
  if (!selectedSelected.value.length) return
  const toRemove = selectedSelected.value.filter(
    key => !props.allColumns.find(c => c.key === key)?.fixed,
  )
  const updated = props.modelValue.filter(k => !toRemove.includes(k))
  emit('update:modelValue', updated)
  selectedSelected.value = []
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
</script>

<template>
  <CRow class="m-2 align-items-center" color="light">
    <!-- 가능한 컬럼 -->
    <CCol col="12" md="5" lg="4">
      <label class="form-label text-caption font-weight-bold text-muted mb-1">
        {{ availableLabel }}
      </label>
      <select v-model="availableSelected" multiple class="form-select text-caption" :size="size">
        <option v-for="item in availableItems" :key="item.key" :value="item.key">
          {{ item.label }}
        </option>
      </select>
    </CCol>

    <!-- 중앙 이동 버튼 -->
    <CCol
      col="12"
      md="2"
      lg="1"
      class="text-center d-flex flex-row flex-md-column justify-content-center align-items-center gap-1 my-2 my-md-0"
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
        <select v-model="selectedSelected" multiple class="form-select text-caption" :size="size">
          <option
            v-for="item in selectedItems"
            :key="item.key"
            :value="item.key"
            :disabled="item.fixed"
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
      </div>
    </CCol>
  </CRow>
</template>
