<script setup lang="ts">
import type { ApprovalContent, FormField } from '@/store/types/approval'
import { asStr } from '../utils/approvalMeta'

const props = defineProps<{
  modelValue: ApprovalContent
  schema: FormField[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ApprovalContent): void
}>()

const updateField = (key: string, val: unknown) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: val,
  })
}
</script>

<template>
  <div class="dynamic-schema-form">
    <CRow v-for="field in schema" :key="field.key" class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label">
        {{ field.label }}
        <span v-if="field.required" class="text-danger">*</span>
      </CFormLabel>
      <CCol sm="9">
        <CFormTextarea
          v-if="field.type === 'textarea'"
          :value="asStr(modelValue[field.key])"
          :required="field.required"
          rows="4"
          :placeholder="`${field.label}을(를) 입력하세요.`"
          @input="updateField(field.key, ($event.target as HTMLInputElement).value)"
        />
        <CFormSelect
          v-else-if="field.type === 'select'"
          :value="asStr(modelValue[field.key])"
          :required="field.required"
          @change="updateField(field.key, ($event.target as HTMLSelectElement).value)"
        >
          <option value="">-- 선택하세요 --</option>
          <option v-for="opt in field.options ?? []" :key="opt" :value="opt">
            {{ opt }}
          </option>
        </CFormSelect>
        <CFormInput
          v-else
          :type="field.type"
          :value="asStr(modelValue[field.key])"
          :required="field.required"
          :placeholder="`${field.label}을(를) 입력하세요.`"
          @input="updateField(field.key, ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
