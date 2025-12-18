<script lang="ts" setup>
import { ref, watch, type ComputedRef, inject } from 'vue'

interface Props {
  modelValue: boolean
  affiliate?: number | null
  accountName?: string
}

const props = withDefaults(defineProps<Props>(), {
  affiliate: null,
  accountName: '',
})

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', affiliateId: number | null): void
}

const emit = defineEmits<Emits>()

const affiliates = inject<ComputedRef<{ value: number; label: string }[]>>('affiliates')
const selectedAffiliate = ref<number | null>(props.affiliate)

watch(
  () => props.affiliate,
  newValue => {
    selectedAffiliate.value = newValue
  },
)

const closeModal = () => {
  emit('update:modelValue', false)
}

const handleSelect = () => {
  emit('select', selectedAffiliate.value)
  closeModal()
}

const handleCancel = () => {
  selectedAffiliate.value = props.affiliate
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
      <v-card-title class="d-flex justify-space-between align-center bg-primary text-white">
        <span>관계회사/프로젝트 선택</span>
        <v-btn icon="mdi-close" variant="text" size="small" @click="handleCancel" />
      </v-card-title>

      <v-card-text class="pt-4">
        <div v-if="accountName" class="mb-3">
          <div class="text-caption text-grey">계정</div>
          <div class="text-body-1 font-weight-medium">{{ accountName }}</div>
        </div>

        <div>
          <div class="text-caption text-grey mb-2">관계회사/프로젝트</div>
          <CFormSelect
            v-model.number="selectedAffiliate"
            placeholder="관계회사를 선택하세요"
            class="mb-2"
          >
            <option :value="null">선택 안 함</option>
            <option v-for="aff in affiliates" :value="aff.value" :key="aff.value">
              {{ aff.label }}
            </option>
          </CFormSelect>
          <div class="text-caption text-grey-darken-1">이 계정은 관계회사 정보가 필요합니다.</div>
        </div>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-spacer />
        <v-btn color="grey" variant="text" @click="handleCancel">취소</v-btn>
        <v-btn color="primary" variant="elevated" @click="handleSelect">확인</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.v-card-title {
  padding: 12px 16px;
}
</style>
