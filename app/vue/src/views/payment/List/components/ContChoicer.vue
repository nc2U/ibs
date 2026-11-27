<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useContract } from '@/store/pinia/contract.ts'
import type { Contract, ContFilter } from '@/store/types/contract.ts'
import type { ContractPaymentPatchPayload, PaymentList } from '@/store/types/payment.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

type PayMatchPayload = ContractPaymentPatchPayload & { trans_id: number | null }

const props = defineProps<{
  project: number
  payment: PaymentList
}>()

const emit = defineEmits<{
  (e: 'pay-match', payload: PayMatchPayload): void
  (e: 'close'): void
}>()

const { can, PERM } = usePerms()
const canPaymentCreate = computed(() => can(PERM.PAYMENT_CREATE))
const canPaymentUpdate = computed(() => can(PERM.PAYMENT_UPDATE))

const refAlertModal = ref()
const refConfirmModal = ref()

const form = ref({
  search: '',
})

const cont = ref<Contract | null>(null)
const msg = ref('')
const textClass = ref('')

onMounted(() => pageInit())

const contStore = useContract()
const contactList = computed(() => contStore.contractList)
const fetchContractList = (payload: ContFilter) => contStore.fetchContractList(payload)

const pageInit = () => {
  form.value.search = ''
  textClass.value = 'text-medium-emphasis'
  msg.value = '계약자 관련정보 또는 계약 일련번호를 입력하세요.'
  contStore.contractList = []
}

const searchCont = async () => {
  form.value.search = form.value.search.trim()
  if (form.value.search === '') {
    pageInit()
    return
  }
  await fetchContractList({ project: props.project, search: form.value.search })
  if (contactList.value.length === 0) {
    msg.value = '해당 검색어로 등록된 데이터가 없습니다.'
    textClass.value = 'text-danger'
  }
}

const contMatching = (contract: Contract) => {
  if (canPaymentCreate.value || canPaymentUpdate.value) {
    cont.value = contract
    refConfirmModal.value.callModal()
  } else refAlertModal.value.callModal()
}

const modalAction = () => {
  const trans_id = props.payment?.trans_id ?? null
  const pk = props.payment?.entry_id
  const contract = (cont.value as Contract | null)?.pk ?? null
  if (!trans_id || !pk || !contract) {
    refAlertModal.value?.callModal(null, '연결할 수납 거래 또는 계약 정보가 없습니다.')
    return
  }
  emit('pay-match', { trans_id, accounting_entries: [{ pk, contract }] })
  pageInit()
  emit('close')
}
</script>

<template>
  <CRow>
    <CCol class="ps-4 pe-4">
      <CCallout color="warning" class="pb-1 mb-4">
        <CRow>
          <CCol>
            <CRow>
              <CCol md="5" class="mb-3">
                <CInputGroup class="flex-nowrap">
                  <CFormInput
                    v-model="form.search"
                    placeholder="계약자, 비고, 계약 일련번호"
                    aria-label="Search"
                    aria-describedby="addon-wrapping"
                    @keydown.enter="searchCont"
                  />
                  <CInputGroupText @click="searchCont"> 계약 건 찾기</CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>
        </CRow>
        <CRow>
          <CCol v-if="contactList.length !== 0" color="warning" class="p-2 ps-3">
            <v-btn
              v-for="c in contactList"
              :key="c.pk"
              type="button"
              color="#546E7A"
              variant="outlined"
              size="small"
              @click="contMatching(c)"
            >
              {{ `${c.contractor?.name}(${c.serial_number})` }}
            </v-btn>
          </CCol>
          <CCol v-else class="mt-3 m-2" :class="textClass">
            {{ msg }}
          </CCol>
        </CRow>
      </CCallout>

      <CAlert v-if="contactList.length !== 0" color="light" class="pt-0 pb-0 text-primary">
        상기 계약 건 중 아래 수납 항목을 매칭 등록할 계약 건을 선택한 후 클릭하여 주십시오.
      </CAlert>

      <CAlert color="info">
        <span>
          {{
            `[입금자] : ${payment.trader}  | [입금액] : ${numFormat(
              payment.amount,
            )} | [입금계좌] : ${payment.bank_account} | [입금일] : ${payment.deal_date}`
          }}
        </span>
      </CAlert>
    </CCol>
  </CRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header>건별 수납 매칭</template>
    <template #default>
      해당 수납 항목을 &lt;<span class="text-primary fw-bold">
        {{ `${cont?.contractor?.name} [${cont?.serial_number}]` }} </span
      >&gt; 계약 건의 납부대금으로 등록합니다.
    </template>
    <template #footer>
      <v-btn color="primary" variant="flat" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
