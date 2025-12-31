<script lang="ts" setup>
import { computed, reactive, ref, nextTick, watch } from 'vue'
import { bgLight } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins.ts'
import { usePayment } from '@/store/pinia/payment'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import Multiselect from '@vueform/multiselect'

const props = defineProps({ byCont: { type: Boolean, default: false } })
const emit = defineEmits(['payment-filtering'])

const from_date = ref('')
const to_date = ref('')

const form = reactive({
  order_group: '',
  unit_type: '',
  pay_order: '',
  pay_account: '',
  no_contract: false,
  no_install: false,
  search: '',
})

const contStore = useContract()
const getOrderGroups = computed(() => contStore.getOrderGroups)

const projectDataStore = useProjectData()
const getTypes = computed(() => projectDataStore.getTypes)

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)
const paymentsCount = computed(() => paymentStore.ledgerPaymentsCount)

const proLedgerStore = useProLedger()
const allProBankList = computed(() => proLedgerStore.allProBankList)

const formsCheck = computed(() => {
  const a = !from_date.value
  const b = !to_date.value
  const c = !form.order_group
  const d = !form.unit_type
  const e = !form.pay_order
  const f = !form.pay_account
  const g = !form.no_contract
  const h = !form.no_install
  const i = form.search.trim() === ''
  return a && b && c && d && e && f && g && h && i
})

watch(props, nVal => {
  if (nVal.byCont) {
    from_date.value = ''
    form.order_group = ''
    form.unit_type = ''
    form.pay_order = ''
    form.pay_account = ''
    form.no_contract = false
    form.no_install = false
    form.search = ''
    listFiltering(1)
  }
})

watch(from_date, () => listFiltering(1))
watch(to_date, () => listFiltering(1))

const listFiltering = (page = 1) => {
  nextTick(() => {
    form.search = form.search.trim()
    emit('payment-filtering', {
      ...{ page, from_date: from_date.value, to_date: to_date.value },
      ...form,
    })
  })
}

const noContractFn = () => {
  nextTick(() => {
    if (form.no_contract) form.no_install = false
  })
  listFiltering(1)
}

const noInstallFn = () => {
  nextTick(() => {
    if (form.no_install) form.no_contract = false
  })
  listFiltering(1)
}

const resetForm = () => {
  from_date.value = ''
  to_date.value = ''
  form.order_group = ''
  form.unit_type = ''
  form.pay_order = ''
  form.pay_account = ''
  form.no_contract = false
  form.no_install = false
  form.search = ''
  listFiltering(1)
}
defineExpose({ listFiltering })
</script>

<template>
  <CCallout color="warning" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol xl="8">
        <CRow>
          <CCol lg="6" xl="2" class="mb-3">
            <DatePicker
              v-model="from_date"
              placeholder="납부일자 (From)"
              :disabled="byCont"
              @keydown.enter="listFiltering(1)"
            />
          </CCol>

          <CCol lg="6" xl="2" class="mb-3">
            <DatePicker
              v-model="to_date"
              placeholder="납부일자 (To)"
              @keydown.enter="listFiltering(1)"
            />
          </CCol>

          <CCol lg="6" xl="2" class="mb-3">
            <Multiselect
              v-model="form.order_group"
              :options="getOrderGroups"
              placeholder="차수"
              :disabled="byCont"
              @change="listFiltering(1)"
            />
          </CCol>

          <CCol lg="6" xl="2" class="mb-3">
            <Multiselect
              v-model="form.unit_type"
              :options="getTypes"
              placeholder="타입"
              :disabled="byCont"
              @change="listFiltering(1)"
            />
          </CCol>

          <CCol lg="6" xl="2" class="mb-3">
            <CFormSelect v-model="form.pay_order" :disabled="byCont" @change="listFiltering(1)">
              <option value="">납부회차 선택</option>
              <option v-for="po in payOrderList" :key="po.pk as number" :value="po.pk">
                {{ po.__str__ }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol lg="6" xl="2" class="mb-3">
            <CFormSelect v-model="form.pay_account" :disabled="byCont" @change="listFiltering(1)">
              <option value="">납부계좌 선택</option>
              <option v-for="ba in allProBankList" :key="ba.pk as number" :value="ba.pk">
                {{ ba.alias_name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>
      <CCol xl="4">
        <CRow>
          <CCol md="6" lg="3" class="mb-3 pl-4 pt-2">
            <CFormSwitch
              id="no_contract"
              v-model="form.no_contract"
              label="계약 미등록"
              :disabled="byCont"
              @change="noContractFn"
            />
          </CCol>

          <CCol md="6" lg="3" class="mb-3 pl-4 pt-2">
            <CFormSwitch
              id="no_install"
              v-model="form.no_install"
              label="회차 미등록"
              :disabled="byCont"
              @change="noInstallFn"
            />
          </CCol>

          <CCol lg="6" xl="6" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                :disabled="byCont"
                placeholder="계약자, 입금자, 적요, 비고"
                aria-label="Username"
                aria-describedby="addon-wrapping"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
    <CRow>
      <CCol color="warning" class="p-2 pl-3">
        <strong>납부 건수 조회 결과 : {{ numFormat(paymentsCount, 0, 0) }} 건</strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
