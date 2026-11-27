<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContract } from '@/store/pinia/contract'

const props = defineProps<{
  project?: number | null
}>()

const route = useRoute()
const router = useRouter()
const contractStore = useContract()

const search = ref('')
const isSearched = ref(false)

const contractorList = computed(() => contractStore.contractorList)

const searchContractor = async () => {
  const query = search.value.trim()
  if (!query || !props.project) return
  isSearched.value = false
  try {
    await contractStore.fetchContractorList(props.project, query)
  } finally {
    isSearched.value = true
  }
}

watch(
  () => props.project,
  () => {
    search.value = ''
    isSearched.value = false
    contractStore.contractorList = []
  },
)

watch(search, () => {
  isSearched.value = false
})

const setContractor = (pk: number) => {
  router.push({ name: '계약 해지 보기', params: { contractorId: pk }, query: route.query })
  search.value = ''
  isSearched.value = false
  contractStore.contractorList = []
}
</script>

<template>
  <CCallout color="warning" class="pb-0 mb-4">
    <CRow>
      <CCol>
        <CRow>
          <CCol md="4" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="search"
                placeholder="계약자, 비고, 계약 일련번호"
                aria-label="Search"
                aria-describedby="addon-wrapping"
                :disabled="!project"
                @keydown.enter="searchContractor"
              />
              <CInputGroupText
                style="cursor: pointer"
                @click="searchContractor"
              >
                계약 건 찾기
              </CInputGroupText>
            </CInputGroup>
          </CCol>
          <CCol
            v-if="contractorList && contractorList.length > 0"
            color="warning"
            class="p-1 ps-3 mb-2"
          >
            <v-btn
              v-for="contractor in contractorList"
              :key="contractor.pk"
              type="button"
              color="blue-grey-darken-1"
              variant="outlined"
              size="small"
              class="me-1 mb-1"
              style="cursor: pointer"
              @click="setContractor(contractor.pk)"
            >
              {{ contractor.__str__ }}
            </v-btn>
          </CCol>
          <CCol
            v-else-if="isSearched"
            class="p-1 ps-3 mb-2 d-flex align-items-center text-muted"
          >
            <small>검색 결과가 없습니다.</small>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>
</template>
