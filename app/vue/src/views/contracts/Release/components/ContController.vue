<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useContract } from '@/store/pinia/contract'

const props = defineProps({ project: { type: Number, default: null } })
const emit = defineEmits(['search-contractor', 'get-release'])

const search = ref('')

const contractStore = useContract()
const contractorList = computed(() => contractStore.contractorList)

const searchContractor = () => emit('search-contractor', search.value.trim())

watch(props, nVal => {
  if (nVal.project) searchContractor()
})

const router = useRouter()
const setContractor = (pk: number, release: number | null) => {
  router.push({ name: '계약 해지 보기', params: { contractorId: pk } })
  if (release !== null) emit('get-release', release)
  else contractStore.contRelease = null

  search.value = ''
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
              <CInputGroupText @click="searchContractor"> 계약 건 찾기</CInputGroupText>
            </CInputGroup>
          </CCol>
          <CCol
            v-if="contractorList && contractorList.length > 0"
            color="warning"
            class="p-1 pl-3 mb-2"
          >
            <v-btn
              v-for="contractor in contractorList"
              :key="contractor.pk"
              type="button"
              color="blue-grey-darken-1"
              variant="outlined"
              size="small"
              @click="setContractor(contractor.pk, contractor.contractorrelease)"
            >
              {{ contractor.__str__ }}
            </v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CCallout>
</template>
