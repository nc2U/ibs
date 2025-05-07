<script lang="ts" setup>
import { reactive, computed, nextTick } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { useCompany } from '@/store/pinia/company'
import { bgLight } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'

const emit = defineEmits(['list-filtering'])

const form = reactive({
  upp: '',
  q: '',
})

const formsCheck = computed(() => form.upp === '' && form.q.trim() === '')

const comStore = useCompany()
const departmentsCount = computed(() => comStore.departmentsCount)
const getPkDeparts = computed(() => comStore.getPkDeparts)
const uppers = computed(() => comStore.getUpperDeps)
const getUpperDeps = computed(() =>
  getPkDeparts.value.filter((d: { value?: number }) => uppers.value.includes(d.value || null)),
)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      page,
      upp: form.upp || '',
      q: form.q.trim(),
    })
  })
}

const resetForm = () => {
  form.upp = ''
  form.q = ''
  listFiltering(1)
}

defineExpose({ listFiltering })
</script>

<template>
  <CCallout color="success" class="pb-0 mb-3" :class="bgLight">
    <CRow>
      <CCol md="6">
        <CRow>
          <CCol md="4" class="mb-3">
            <Multiselect
              v-model="form.upp"
              :options="getUpperDeps"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              placeholder="상위부서"
              @change="listFiltering(1)"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol md="6">
        <CRow class="justify-content-end">
          <CCol md="5" class="mb-3">
            <CInputGroup>
              <CFormInput
                v-model="form.q"
                placeholder="부서명, 주요 업무 검색"
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
        <strong> 부서 수 조회 결과 : {{ numFormat(departmentsCount) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
