<script setup lang="ts">
import { computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { type SuitCase } from '@/store/types/docs'
import { cutString } from '@/utils/baseMixins'

const props = defineProps({
  suitCase: { type: Object as PropType<SuitCase>, default: null },
  viewRoute: { type: String, required: true },
})

const emit = defineEmits(['agency-filter', 'agency-search', 'related-filter'])

const suitCaseName = computed(() => {
  const sCase = props.suitCase
  return `${getCourt(sCase?.court_desc)} ${sCase?.case_number} ${sCase?.case_name}`
})

const store = useStore()
const sortName = computed(() => props.suitCase?.proj_name || '본사 문서')
const sortColor = computed(() => (props.suitCase?.proj_sort === '2' ? 'success' : 'info'))
const courtColor = computed(() => (store.theme !== 'dark' ? 'secondary' : 'default'))
const agencyName = computed(() => {
  const agency = props.suitCase?.court_desc || props.suitCase?.other_agency
  return agency ? getCourt(agency) : ''
})
const relatedCaseName = computed(() =>
  props.suitCase?.related_case_name ? props.suitCase?.related_case_name.split(' ')[1] : '',
)

const agencyFunc = () => {
  props.suitCase?.court_desc !== ''
    ? emit('agency-filter', props.suitCase?.court)
    : emit('agency-search', props.suitCase.other_agency)
}

const relatedFilter = () => emit('related-filter', props.suitCase?.related_case)
const getCourt = (court: string | undefined) =>
  court
    ? court
        .replace('지방법원', '지법')
        .replace('고등법원', '고법')
        .replace('대법원', '대법')
        .replace('재판부', '')
    : ''
</script>

<template>
  <CTableRow v-if="suitCase" class="text-center">
    <CTableDataCell class="text-left pl-4">
      <v-badge :color="sortColor" :content="sortName" offset-x="5" offset-y="-7" />
    </CTableDataCell>
    <CTableDataCell>{{ suitCase.sort_desc }}</CTableDataCell>
    <CTableDataCell>{{ suitCase.level_desc }}</CTableDataCell>
    <CTableDataCell class="text-left pl-4">
      <span v-if="suitCase.court_desc || suitCase.other_agency">
        <v-badge :content="agencyName" :color="courtColor" offset-y="-7" />
      </span>
    </CTableDataCell>
    <CTableDataCell>
      <CCol v-if="suitCase.related_case">
        [
        <a href="javascript:void(0);" @click="relatedFilter">
          {{ relatedCaseName }}
        </a>
        ]
      </CCol>
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <router-link :to="{ name: `${viewRoute} - 보기`, params: { caseId: suitCase.pk } }">
        {{ cutString(suitCaseName, 30) }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>{{ cutString(suitCase.plaintiff, 20) }}</CTableDataCell>
    <CTableDataCell>{{ cutString(suitCase.defendant, 20) }}</CTableDataCell>
    <CTableDataCell>{{ cutString(suitCase.related_debtor, 20) }}</CTableDataCell>
    <CTableDataCell>{{ suitCase.case_end_date }}</CTableDataCell>
  </CTableRow>
</template>
