<script lang="ts" setup>
import { ref, watch, type ComputedRef, inject } from 'vue'
import MultiSelect from '@/components/MultiSelect/index.vue'

interface Props {
  modelValue: boolean
  contract?: number | null
  accountName?: string
}

const props = withDefaults(defineProps<Props>(), {
  contract: null,
  accountName: '',
})

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', contractId: number | null): void
}

const emit = defineEmits<Emits>()

const getContracts = inject<ComputedRef<{ value: number; label: string }[]>>('getContracts')
const selectedContract = ref<number | null>(props.contract)

watch(
  () => props.contract,
  newValue => {
    selectedContract.value = newValue
  },
)

const closeModal = () => {
  emit('update:modelValue', false)
}

const handleSelect = () => {
  emit('select', selectedContract.value)
  closeModal()
}

const handleCancel = () => {
  selectedContract.value = props.contract
  closeModal()
}
</script>

<template>
  <v-dialog
    :model-value="modelValue"
    max-width="500"
    persistent
    z-index="10100"
    @update:model-value="closeModal"
  >
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center bg-success text-white">
        <span>관련 계약정보 선택</span>
        <v-btn icon="mdi-close" variant="text" size="small" @click="handleCancel" />
      </v-card-title>

      <v-card-text class="pt-4">
        <div v-if="accountName" class="mb-3">
          <div class="text-caption text-grey">계정</div>
          <div class="text-body-1 font-weight-medium">{{ accountName }}</div>
        </div>

        <div>
          <div class="text-caption text-grey mb-2">관련 계약정보</div>
          <MultiSelect
            v-model.number="selectedContract"
            mode="single"
            :options="getContracts"
            placeholder="계약 정보 선택"
          />
          <div class="text-caption text-grey-darken-1">이 계정은 관련 계약 정보가 필요합니다.</div>
        </div>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-spacer />
        <v-btn color="grey" variant="text" @click="handleCancel">취소</v-btn>
        <v-btn color="success" variant="elevated" @click="handleSelect">확인</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.v-card-title {
  padding: 12px 16px;
}
</style>
