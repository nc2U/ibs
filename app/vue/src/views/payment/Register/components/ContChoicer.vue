<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { downloadFile } from '@/utils/helper.ts'
import { type Contract } from '@/store/types/contract.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { usePayment } from '@/store/pinia/payment.ts'

const props = withDefaults(
  defineProps<{
    project?: number | null
    contract?: Contract | null
    paymentUrl?: string
  }>(),
  {
    project: null,
    contract: null,
    paymentUrl: '',
  },
)

const emit = defineEmits<{
  (e: 'get-contract', cont: number): void
}>()

const route = useRoute()
const router = useRouter()
const form = reactive({ search: '' })
const msg = ref('')
const textClass = ref('')

const contractStore = useContract()
const contractList = computed(() => contractStore.contractList)

const pageInit = () => {
  form.search = ''
  textClass.value = 'text-medium-emphasis'
  msg.value = '계약자 관련정보 또는 계약 일련번호를 입력하세요.'
  contractStore.contractList = []
}

const listFiltering = async (page = 1) => {
  form.search = form.search.trim()
  if (form.search === '') {
    pageInit()
    return
  }
  if (!props.project) return
  await contractStore.fetchContractList({
    project: props.project,
    search: form.search,
    page,
  })
  if (contractList.value.length === 0) {
    msg.value = '해당 검색어로 등록된 데이터가 없습니다.'
    textClass.value = 'text-danger'
  }
}

const getContract = (cont: number) => {
  emit('get-contract', cont)
  pageInit()
}

const downloadPaymentStatement = () => {
  if (props.paymentUrl) downloadFile(props.paymentUrl, '납부_확인서.pdf')
}

const paymentStore = usePayment()
const removeContract = () => {
  contractStore.contract = null
  paymentStore.ledgerAllPaymentList = []
  paymentStore.ledgerPaymentsCount = 0
  if (route.params.contractId) {
    router.replace({ name: '건별 납부 관리' })
  }
}

onMounted(() => pageInit())
</script>

<template>
  <CCallout color="warning" class="pb-0 mb-4">
    <CRow>
      <CCol>
        <CRow>
          <CCol md="4" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                placeholder="계약자, 비고, 계약 일련번호"
                aria-label="Search"
                aria-describedby="addon-wrapping"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText @click="listFiltering(1)"> 계약 건 찾기</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
    <CRow>
      <CCol v-if="contractList.length !== 0" color="warning" class="p-2 ps-3">
        <v-btn
          v-for="cont in contractList"
          :key="cont.pk"
          type="button"
          color="#546E7A"
          variant="outlined"
          size="small"
          @click="getContract(cont.pk)"
        >
          {{ `${cont.contractor?.name}(${cont.serial_number})` }}
        </v-btn>
      </CCol>
      <CCol v-else class="mt-3 m-2" :class="textClass">
        {{ msg }}
      </CCol>
    </CRow>
  </CCallout>

  <CAlert v-if="contract" color="info">
    <CRow>
      <CCol xs="10">
        <strong v-if="contract">
          [일련번호 :
          <router-link
            v-c-tooltip="'계약 상세 관리'"
            :to="{ name: '계약 상세 보기', params: { contractorId: contract.contractor?.pk } }"
          >
            {{ contract.serial_number }}
          </router-link>
          ] (타입 :
          {{ contract.unit_type_desc?.name ?? '미정' }}
          {{
            contract.key_unit?.houseunit
              ? contract.key_unit.houseunit.__str__
              : '--- 동호수 현재 미정 ---'
          }}
          |
          <router-link
            v-c-tooltip="'계약 상세 관리'"
            :to="{ name: '계약 상세 보기', params: { contractorId: contract.contractor?.pk } }"
          >
            계약자 : {{ contract.contractor?.name }})
          </router-link>
          (
          <a href="#" class="text-decoration-none" @click.prevent="downloadPaymentStatement">
            납부내역서 출력
          </a>
          )
        </strong>
      </CCol>
      <CCol v-if="contract" class="text-end">
        <a href="#" class="text-reset" aria-label="계약 선택 해제" @click.prevent="removeContract">
          <CIcon name="cilX" />
        </a>
      </CCol>
    </CRow>
  </CAlert>
</template>
