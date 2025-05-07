<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { useCompany } from '@/store/pinia/company'
import { bgLight } from '@/utils/cssMixins'

const emit = defineEmits(['list-filtering'])

const form = reactive({
  q: '',
})

const formsCheck = computed(() => form.q.trim() === '')

const comStore = useCompany()
const dutysCount = computed(() => comStore.dutysCount)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      q: form.q.trim(),
    })
  })
}

const resetForm = () => {
  form.q = ''
  listFiltering(1)
}

defineExpose({ listFiltering })
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
                placeholder="직책명 검색"
                aria-label="search"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol class="p-2 pl-3">
        <strong> 직책 수 조회 결과 : {{ numFormat(dutysCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
