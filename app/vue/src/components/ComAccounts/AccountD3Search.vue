<template>
  <Multiselect
    v-model="selectedD3"
    :options="d3Options"
    :searchable="true"
    :create-option="false"
    :close-on-select="true"
    placeholder="계정과목 검색..."
    label="name"
    track-by="pk"
    :classes="{
      container: 'multiselect-custom',
      search: 'form-control multiselect-search',
    }"
    @change="handleChange"
  >
    <template #singlelabel="{ value }">
      <div class="multiselect-single-label">
        <span class="text-muted small">{{ value.d1_name }} > {{ value.d2_name }} > </span>
        <strong>{{ value.name }}</strong>
      </div>
    </template>

    <template #option="{ option }">
      <div class="d-flex flex-column">
        <div>
          <strong>{{ option.name }}</strong>
          <span class="text-muted small ms-2">({{ option.code }})</span>
        </div>
        <div class="text-muted small">
          {{ option.d1_name }} > {{ option.d2_name }}
        </div>
      </div>
    </template>
  </Multiselect>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import Multiselect from '@vueform/multiselect'

interface AccountD3Option {
  pk: number
  name: string
  code: string
  d2: number
  d2_name: string
  d2_d1: number
  d1_name: string
}

interface Props {
  modelValue?: number | null
  getAllD3List: () => Promise<void>
  getD3List: () => AccountD3Option[]
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: number | null): void
  (e: 'update:hierarchy', d1: number | null, d2: number | null, d3: number | null): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  disabled: false,
})

const emit = defineEmits<Emits>()

const selectedD3 = ref<AccountD3Option | null>(null)

// D3 목록을 options 형태로 변환
const d3Options = computed(() => {
  return props.getD3List().map(d3 => ({
    pk: d3.pk,
    name: d3.name,
    code: d3.code,
    d2: d3.d2,
    d2_name: d3.d2_name || '',
    d2_d1: d3.d2_d1 || 0,
    d1_name: d3.d1_name || '',
  }))
})

const handleChange = (value: AccountD3Option | null) => {
  if (value) {
    emit('update:modelValue', value.pk)
    emit('update:hierarchy', value.d2_d1, value.d2, value.pk)
  } else {
    emit('update:modelValue', null)
    emit('update:hierarchy', null, null, null)
  }
}

// modelValue 변경 시 selectedD3 동기화
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      const found = d3Options.value.find(opt => opt.pk === newVal)
      if (found) {
        selectedD3.value = found
      }
    } else {
      selectedD3.value = null
    }
  },
)

onMounted(async () => {
  // 전체 D3 목록 로드
  await props.getAllD3List()

  // 초기값 설정
  if (props.modelValue) {
    const found = d3Options.value.find(opt => opt.pk === props.modelValue)
    if (found) {
      selectedD3.value = found
    }
  }
})
</script>

<style scoped>
.multiselect-custom {
  min-width: 250px;
}

.multiselect-single-label {
  display: flex;
  align-items: center;
}
</style>
