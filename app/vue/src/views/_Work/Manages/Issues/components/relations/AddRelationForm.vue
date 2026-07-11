<script lang="ts" setup>
import Multiselect from '@vueform/multiselect'
import { type PropType, ref } from 'vue'
import { isValidate } from '@/utils/helper'
import { btnLight } from '@/utils/cssMixins.ts'

const props = defineProps({
  issuePk: { type: Number, required: true },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['add-rel-issue', 'add-form-ctl'])

const validated = ref(false)

const relIssue = ref({
  target: null as number | null,
  delay: null as number | null,
})

const direction = ref<'predecessor' | 'successor'>('predecessor')

const addFormCtl = (bool: boolean) => emit('add-form-ctl', bool)

const addRelIssue = (event: Event) => {
  if (isValidate(event)) validated.value = true
  else {
    let payload = {
      source: props.issuePk,
      target: relIssue.value.target,
      delay: relIssue.value.delay,
    }

    if (direction.value === 'predecessor') {
      // If it's a predecessor, the current issue is the target
      payload = {
        source: relIssue.value.target as number,
        target: props.issuePk,
        delay: relIssue.value.delay,
      }
    }
    emit('add-rel-issue', payload)
  }
  relIssue.value.target = null
  relIssue.value.delay = null
}
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="addRelIssue">
    <CRow class="mt-2">
      <CCol sm="4" md="3" lg="2">
        <CFormSelect v-model="direction">
          <option value="successor">후속 업무 (이 업무를 다음에 진행)</option>
          <option value="predecessor">선행 업무 (이 업무를 우선 진행)</option>
        </CFormSelect>
      </CCol>
      <CFormLabel for="colFormLabel" class="col-sm-1 col-form-label text-right">
        업무 :
      </CFormLabel>
      <CCol sm="4" md="3" lg="2">
        <Multiselect
          v-model="relIssue.target"
          :options="getIssues"
          :classes="{
            caret: 'multiselect-caret mr-4',
            search: 'form-control multiselect-search',
            tagsSearch: 'form-control multiselect-tags-search',
          }"
          :attrs="relIssue.target ? {} : { required: true }"
          placeholder="업무 검색"
          :add-option-on="['enter', 'tab']"
          searchable
        />
      </CCol>
      <CFormLabel for="colFormLabel" class="col-sm-1 col-form-label text-right">
        [예정]대기 :
      </CFormLabel>
      <CCol sm="3" md="2" lg="1">
        <CFormInput v-model.number="relIssue.delay" type="number" min="0" placeholder="대기일수" />
      </CCol>
      <CFormLabel class="col-sm-1 col-form-label"> 일</CFormLabel>
      <CCol class="pt-1">
        <v-btn type="submit" color="primary" size="small">추가</v-btn>
        <v-btn :color="btnLight" size="small" @click="addFormCtl(false)">취소</v-btn>
      </CCol>
    </CRow>
  </CForm>
</template>
