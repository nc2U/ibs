<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { bgLight } from '@/utils/cssMixins.ts'
import { type ComFilter } from '@/store/types/company.ts'

const emit = defineEmits<{
  (e: 'list-filtering', filter: ComFilter): void
}>()

const form = reactive({
  q: '',
})

const formsCheck = computed(() => form.q.trim() === '')

const comStore = useCompany()
const executiveRanksCount = computed(() => comStore.executiveRanksCount)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      q: form.q.trim(),
    })
  })
}

const clearFilter = () => {
  form.q = ''
}

const resetForm = () => {
  clearFilter()
  listFiltering(1)
}

defineExpose({ listFiltering, resetForm, clearFilter })
</script>

<template>
  <CCallout color="warning" class="pb-0 mb-3" :class="bgLight">
    <CRow>
      <CCol md="12">
        <CRow class="justify-content-end">
          <CCol md="4" class="mb-3">
            <CInputGroup>
              <CFormInput
                v-model="form.q"
                placeholder="임원 직위명 검색"
                aria-label="search"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText
                role="button"
                style="cursor: pointer"
                @click="listFiltering(1)"
              >
                검색
              </CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol class="p-2 ps-3">
        <strong> 임원 직위 수 조회 결과 : {{ numFormat(executiveRanksCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-end mb-0">
        <v-btn color="info" size="small" variant="flat" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
