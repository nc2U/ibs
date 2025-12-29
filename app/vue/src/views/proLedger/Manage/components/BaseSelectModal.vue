<script lang="ts" setup>
import { ref, watch, computed, type ComputedRef, inject } from 'vue'
import MultiSelect from '@/components/MultiSelect/index.vue'

interface Props {
  modelValue: boolean
  type?: 'contract' | 'contractor'
  contract?: number | null
  contractor?: number | null
  accountName?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'contract',
  contract: null,
  contractor: null,
  accountName: '',
})

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', id: number | null): void
}

const emit = defineEmits<Emits>()

// 동적 설정
const config = computed(
  () =>
    ({
      contract: {
        title: '관련 계약정보 선택',
        placeholder: '계약 정보 선택',
        helpText: '이 계정은 관련 계약 정보가 필요합니다.',
        label: '관련 계약정보',
        color: 'success',
        icon: 'mdi-book-open',
      },
      contractor: {
        title: '관련 계약자 선택',
        placeholder: '계약자 선택',
        helpText: '이 계정은 관련 계약자 정보가 필요합니다.',
        label: '관련 계약자',
        color: 'purple',
        icon: 'mdi-account-cog',
      },
    })[props.type],
)

const getContracts = inject<ComputedRef<{ value: number; label: string }[]>>('getContracts')
const getContractors = inject<ComputedRef<{ value: number; label: string }[]>>('getAllContractors')

const options = computed(() =>
  props.type === 'contract' ? getContracts?.value : getContractors?.value,
)

const selectedId = ref<number | null>(props.type === 'contract' ? props.contract : props.contractor)

watch(
  () => [props.contract, props.contractor, props.type],
  () => {
    selectedId.value = props.type === 'contract' ? props.contract : props.contractor
  },
)

const closeModal = () => {
  emit('update:modelValue', false)
}

const handleSelect = () => {
  emit('select', selectedId.value)
  closeModal()
}

const handleCancel = () => {
  selectedId.value = props.type === 'contract' ? props.contract : props.contractor
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
      <v-card-title
        class="d-flex justify-space-between align-center text-white"
        :class="`bg-${config.color}`"
      >
        <div class="d-flex align-items-center">
          <v-icon :icon="config.icon" size="20" class="mr-2" />
          <span>{{ config.title }}</span>
        </div>
        <v-btn icon="mdi-close" variant="text" size="small" @click="handleCancel" />
      </v-card-title>

      <v-card-text class="pt-4">
        <div v-if="accountName" class="mb-3">
          <div class="text-caption text-grey">계정</div>
          <div class="text-body-1 font-weight-medium">{{ accountName }}</div>
        </div>

        <div>
          <div class="text-caption text-grey mb-2">{{ config.label }}</div>
          <MultiSelect
            v-model.number="selectedId"
            mode="single"
            :options="options"
            :placeholder="config.placeholder"
          />
          <div class="text-caption text-grey-darken-1">{{ config.helpText }}</div>
        </div>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-spacer />
        <v-btn color="grey" variant="text" @click="handleCancel">취소</v-btn>
        <v-btn :color="config.color" variant="elevated" @click="handleSelect">확인</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.v-card-title {
  padding: 12px 16px;
}
</style>
