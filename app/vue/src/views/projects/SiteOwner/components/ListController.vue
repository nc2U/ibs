<script lang="ts" setup>
import { computed, reactive, nextTick } from 'vue'
import { useSite } from '@/store/pinia/project_site'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'

const props = defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['list-filtering'])

const form = reactive({
  limit: '' as '' | number,
  sort: '',
  search: '',
})

const sort_select = [
  { val: '1', text: '개인' },
  { val: '2', text: '법인' },
  { val: '3', text: '국공유지' },
]

const siteStore = useSite()
const siteOwnerCount = computed(() => siteStore.siteOwnerCount)

const formsCheck = computed(
  () => form.limit === '' && form.sort === '' && form.search.trim() === '',
)

const listFiltering = (page = 1) => {
  nextTick(() => {
    emit('list-filtering', {
      project: props.project,
      page,
      limit: form.limit,
      sort: form.sort,
      search: form.search.trim(),
    })
  })
}

const resetForm = () => {
  form.limit = ''
  form.sort = ''
  form.search = ''
  listFiltering(1)
}

defineExpose({ listFiltering })
</script>

<template>
  <CCallout color="warning" class="pb-0 mb-3" :class="bgLight">
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
          <CCol md="6" lg="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.sort" :disabled="!project" @change="listFiltering(1)">
              <option value="">소유구분</option>
              <option v-for="sort in sort_select" :key="sort.val" :value="sort.val">
                {{ sort.text }}
              </option>
            </CFormSelect>
          </CCol>
          <CCol md="12" lg="4" xl="3" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                placeholder="소유자, 연락처, 지번, 상담기록 검색"
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
        <strong> 소유자 수 조회 결과 : {{ numFormat(siteOwnerCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
