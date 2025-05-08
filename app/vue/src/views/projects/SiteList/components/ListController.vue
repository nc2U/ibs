<script lang="ts" setup>
import { computed, reactive, nextTick } from 'vue'
import { useSite } from '@/store/pinia/project_site'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'

defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['list-filtering'])

const form = reactive({ limit: '' as '' | number, search: '' })

const siteStore = useSite()

const siteCount = computed(() => siteStore.siteCount)

const formsCheck = computed(() => form.limit === '' && form.search.trim() === '')

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', { page, limit: form.limit, search: form.search.trim() })
  })
}

defineExpose({ listFiltering })

const resetForm = () => {
  form.limit = ''
  form.search = ''
  listFiltering(1)
}
</script>

<template>
  <CCallout color="info" class="pb-0 mb-3" :class="bgLight">
    <CRow>
      <CCol md="12" lg="8" xl="6">
        <CRow>
          <CCol md="6" lg="4" xl="2" class="mb-3">
            <CFormSelect v-model.number="form.limit" @change="listFiltering(1)">
              <option value="">표시 개수</option>
              <option :value="10" :disabled="form.limit === '' || form.limit === 10">10 개</option>
              <option :value="30" :disabled="form.limit === 30">30 개</option>
              <option :value="50" :disabled="form.limit === 50">50 개</option>
              <option :value="100" :disabled="form.limit === 100">100 개</option>
            </CFormSelect>
          </CCol>
          <CCol md="6" lg="5" xl="3" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                placeholder="행정동, 지번, 소유자, 지목 검색"
                aria-label="search"
                :disabled="!project"
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
        <strong> 필지 건 수 조회 결과 : {{ numFormat(siteCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
