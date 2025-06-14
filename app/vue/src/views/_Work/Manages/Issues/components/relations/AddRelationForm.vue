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
  issue: props.issuePk as number,
  issue_to: null,
  relation_type: 'relates',
  delay: null,
})

const addFormCtl = (bool: boolean) => emit('add-form-ctl', bool)

const addRelIssue = (event: Event) => {
  if (isValidate(event)) validated.value = true
  else emit('add-rel-issue', { ...relIssue.value })
  relIssue.value.issue_to = null
  relIssue.value.relation_type = 'relates'
  relIssue.value.delay = null
}
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="addRelIssue">
    <CRow class="mt-2">
      <CCol sm="4" md="3" lg="2">
        <CFormSelect v-model="relIssue.relation_type">
          <option value="relates">다음 업무와 관련됨 :</option>
          <option value="duplicates">다음 업무에 중복됨 :</option>
          <option value="duplicated">중복된 업무 :</option>
          <option value="blocks">다음 업무의 해결을 막고 있음 :</option>
          <option value="blocked">다음 업무에게 막혀 있음 :</option>
          <option value="precedes">다음에 진행할 업무 :</option>
          <option value="follows">다음 업무를 우선 진행 :</option>
          <option value="copied_to">다음 업무로 복사됨 :</option>
          <option value="copied_from">다음 업무로부터 복사됨 :</option>
        </CFormSelect>
      </CCol>
      <CFormLabel for="colFormLabel" class="col-sm-1 col-form-label text-right">
        업무 #
      </CFormLabel>
      <CCol sm="4" md="3" lg="2">
        <Multiselect
          v-model="relIssue.issue_to"
          :options="getIssues"
          :classes="{
            caret: 'multiselect-caret mr-4',
            search: 'form-control multiselect-search',
            tagsSearch: 'form-control multiselect-tags-search',
          }"
          :attrs="relIssue.issue_to ? {} : { required: true }"
          placeholder="업무 검색"
          :add-option-on="['enter', 'tab']"
          searchable
        />
      </CCol>
      <template
        v-if="relIssue.relation_type === 'precedes' || relIssue.relation_type === 'follows'"
      >
        <CFormLabel for="colFormLabel" class="col-sm-1 col-form-label text-right">
          지연 :
        </CFormLabel>
        <CCol sm="3" md="2" lg="1">
          <CFormInput v-model="relIssue.delay" />
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
