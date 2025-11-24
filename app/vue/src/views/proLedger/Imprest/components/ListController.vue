<script lang="ts" setup>
import { computed, reactive, ref, watch, nextTick } from 'vue'
import { useProCash } from '@/store/pinia/proCash'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import { useContract } from '@/store/pinia/contract'
import { useComCash } from '@/store/pinia/comCash'

const emit = defineEmits(['list-filtering'])

const from_date = ref('')
const to_date = ref('')

const form = reactive({
  page: 1,
  sort: '',
  account_d1: '',
  pro_acc_d2: '',
  pro_acc_d3: '',
  bank_account: '',
  contract: '',
  search: '',
})

const useComCashStore = useComCash()
const formAccD1List = computed(() => useComCashStore.formAccD1List)

const proCashStore = useProCash()
const sortList = computed(() => proCashStore.sortList)
const formAccD2List = computed(() => proCashStore.formAccD2List)
const formAccD3List = computed(() => proCashStore.formAccD3List)
const imprestBAccount = computed(() => proCashStore.imprestBAccount)
const proImprestCount = computed(() => proCashStore.proImprestCount)

const contStore = useContract()
const getContracts = computed(() => contStore.getContracts)

const formsCheck = computed(() => {
  const a = !from_date.value
  const b = !to_date.value
  const c = !form.sort
  const d = !form.account_d1
  const e = !form.pro_acc_d2
  const f = !form.pro_acc_d3
  const g = !form.bank_account
  const h = !form.contract
  const i = form.search.trim() === ''
  return a && b && c && d && e && f && g && h && i
})

watch(from_date, () => listFiltering(1))
watch(to_date, () => listFiltering(1))

const sortSelect = () => {
  listFiltering(1)
  form.account_d1 = ''
  form.pro_acc_d2 = ''
  form.pro_acc_d3 = ''
}

const accountD1Select = () => {
  listFiltering(1)
  form.pro_acc_d2 = ''
  form.pro_acc_d3 = ''
}

const proAccD2Select = () => {
  listFiltering(1)
  form.pro_acc_d3 = ''
}

const listFiltering = (page = 1) => {
  nextTick(() => {
    form.page = page
    form.search = form.search.trim()

    emit('list-filtering', {
      ...{ page, from_date: from_date.value, to_date: to_date.value },
      ...form,
    })
  })
}

defineExpose({ listFiltering })

const resetForm = () => {
  from_date.value = ''
  to_date.value = ''
  form.sort = ''
  form.account_d1 = ''
  form.pro_acc_d2 = ''
  form.pro_acc_d3 = ''
  form.bank_account = ''
  form.contract = ''
  form.search = ''
  listFiltering(1)
}
</script>

<template>
  <CCallout color="warning" class="pb-0 mb-3" :class="bgLight">
    <CRow>
      <CCol lg="8">
        <CRow>
          <CCol md="6" lg="2" class="mb-3">
            <DatePicker
              v-model="from_date"
              placeholder="시작일 (From)"
              @keydown.enter="listFiltering(1)"
            />
          </CCol>

          <CCol md="6" lg="2" class="mb-3">
            <DatePicker
              v-model="to_date"
              placeholder="종료일 (To)"
              @keydown.enter="listFiltering(1)"
            />
          </CCol>

          <CCol md="6" lg="2" class="mb-3">
            <CFormSelect v-model="form.sort" @change="sortSelect">
              <option value="">거래구분</option>
              <option v-for="sort in sortList" :key="sort.pk" :value="sort.pk">
                {{ sort.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="2" class="mb-3">
            <CFormSelect v-model="form.account_d1" @change="accountD1Select">
              <option value="">계정[대분류]</option>
              <option v-for="acc1 in formAccD1List" :key="acc1.pk" :value="acc1.pk">
                {{ acc1.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="2" class="mb-3">
            <CFormSelect v-model="form.pro_acc_d2" @change="proAccD2Select">
              <option value="">상위 항목</option>
              <option v-for="d1 in formAccD2List" :key="d1.pk" :value="d1.pk">
                {{ d1.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="2" class="mb-3">
            <CFormSelect v-model="form.pro_acc_d3" @change="listFiltering(1)">
              <option value="">하위 항목</option>
              <option v-for="d2 in formAccD3List" :key="d2.pk" :value="d2.pk">
                {{ d2.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="4">
        <CRow>
          <CCol md="6" lg="4" class="mb-3">
            <CFormSelect v-model="form.bank_account" @change="listFiltering(1)">
              <option value="">거래계좌</option>
              <option v-for="acc in imprestBAccount" :key="acc.pk as number" :value="acc.pk">
                {{ acc.alias_name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="4" class="mb-3">
            <MultiSelect
              v-model.number="form.contract"
              mode="single"
              :options="getContracts"
              placeholder="계약 정보 선택"
              @select="listFiltering(1)"
              @clear="resetForm"
            />
          </CCol>

          <CCol md="12" lg="4" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                placeholder="적요, 거래처 검색"
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
        <strong> 거래 건수 조회 결과 : {{ numFormat(proImprestCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
