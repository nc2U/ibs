<script lang="ts" setup>
import Multiselect from '@vueform/multiselect'
import { type PropType, ref } from 'vue'
import { isValidate } from '@/utils/helper'
import { btnLight } from '@/utils/cssMixins.ts'
import type { IssueRelation } from '@/store/types/work_issue.ts'

const props = defineProps({
  issuePk: { type: Number, required: true },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['add-rel-issue', 'add-form-ctl'])

const validated = ref(false)

const relIssue = ref<IssueRelation>({
  issue: null,
  delay: null,
})

const direction = ref<'predecessor' | 'successor'>('successor')

const addFormCtl = (bool: boolean) => emit('add-form-ctl', bool)

const addRelIssue = (event: Event) => {
  if (isValidate(event)) validated.value = true
  else {
    // If predecessor, swap issue and issue_to logic
    const payload = { ...relIssue.value }
    if (direction.value === 'predecessor') {
      // Logic for backend to handle swap or send specific payload
      // For now, assuming backend handles the 'precedes' as issue->issue_to
      // So swapping is needed for the payload if creating a 'blocked-by' relation
      // Payload needs to be handled by backend, but here we just pass it
    }
    emit('add-rel-issue', { ...payload, direction: direction.value })
  }
  relIssue.value.issue = null
  relIssue.value.delay = null
}
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="addRelIssue">
    <CRow class="mt-2">
      <CCol sm="4" md="3" lg="2">
        <CFormSelect v-model="direction">
          <option value="successor">후속 업무 (이 업무보다 나중에 시작할 업무)</option>
          <option value="predecessor">선행 업무 (이 업무보다 먼저 완료할 업무)</option>
        </CFormSelect>
      </CCol>
      <CFormLabel for="colFormLabel" class="col-sm-1 col-form-label text-right">
        업무 #
      </CFormLabel>
      <CCol sm="4" md="3" lg="2">
        <Multiselect
          v-model="relIssue.issue"
          :options="getIssues"
          :classes="{
            caret: 'multiselect-caret mr-4',
            search: 'form-control multiselect-search',
            tagsSearch: 'form-control multiselect-tags-search',
          }"
          :attrs="relIssue.issue ? {} : { required: true }"
          placeholder="업무 검색"
          :add-option-on="['enter', 'tab']"
          searchable
        />
      </CCol>
      <template>
        <CFormLabel for="colFormLabel" class="col-sm-1 col-form-label text-right">
          [예정]대기 :
        </CFormLabel>
        <CCol sm="3" md="2" lg="1">
          <CFormInput
            v-model.number="relIssue.delay"
            type="number"
            min="0"
            placeholder="대기일수"
          />
        </CCol>
        <CFormLabel class="col-sm-1 col-form-label"> 일</CFormLabel>
      </template>
      <CCol class="pt-1">
        <v-btn type="submit" color="primary" size="small">추가</v-btn>
        <v-btn :color="btnLight" size="small" @click="addFormCtl(false)">취소</v-btn>
      </CCol>
    </CRow>
  </CForm>
</template>
