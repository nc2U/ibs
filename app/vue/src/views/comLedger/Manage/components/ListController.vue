<script lang="ts" setup>
import { computed, inject, nextTick, onBeforeMount, type PropType, ref, watch } from 'vue'
import { type DataFilter } from '@/store/pinia/comLedger.ts'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'

const props = defineProps({
  company: { type: Number, default: null },
  dataFilter: { type: Object as PropType<DataFilter>, default: () => {} },
})
watch(
  () => props.company,
  () => resetForm(),
)

const emit = defineEmits(['list-filtering'])

const form = ref<DataFilter>({
  page: 1,
  company: null,
  from_date: '',
  to_date: '',
  sort: null,
  account_category: '',
  account: null,
  bank_account: null,
  affiliate: '',
  search: '',
})

const formsCheck = computed(() => {
  const a = !form.value.from_date
  const b = !form.value.to_date
  const c = !form.value.sort
  const d = !form.value.account_category
  const e = !form.value.account
  const f = !form.value.bank_account
  const g = !form.value.affiliate
  const h = !(form.value.search ?? '')?.trim()
  return a && b && c && d && e && f && g && h
})

const comAccounts = inject<any[]>('comAccounts')
const affiliates = inject<any[]>('affiliates')
const allComBankList = inject<any[]>('allComBankList')
const bankTransactionCount = inject<any>('bankTransactionCount')

const affiliateList = computed(() =>
  ((affiliates as any).value as any[])?.filter(
    it => !((it as any).sort === 'company' && (it as any).id === props.company),
  ),
)

const sortType = computed(() => {
  if (form.value.sort === 1) return 'deposit' // 입금
  if (form.value.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

watch(
  () => form.value.from_date,
  () => listFiltering(1),
)
watch(
  () => form.value.to_date,
  () => listFiltering(1),
)

//   methods: {
const sortSelect = () => {
  listFiltering(1)
  form.value.account_category = ''
  form.value.account = null
}

const cateSelect = () => {
  listFiltering(1)
  form.value.account = null
}

const listFiltering = (page = 1) => {
  form.value.page = page
  form.value.search = (form.value.search ?? '')?.trim()
  nextTick(() => {
    emit('list-filtering', { ...form.value })
  })
}

defineExpose({ listFiltering })

const resetForm = () => {
  form.value.from_date = ''
  form.value.to_date = ''
  form.value.sort = null
  form.value.account_category = ''
  form.value.account = null
  form.value.bank_account = null
  form.value.affiliate = ''
  form.value.search = ''
  listFiltering(1)
}

onBeforeMount(() => {
  if (props.dataFilter) {
    form.value.from_date = props.dataFilter.from_date
    form.value.to_date = props.dataFilter.to_date
    form.value.sort = props.dataFilter.sort
    form.value.account_category = props.dataFilter.account_category
    form.value.account = props.dataFilter.account
    form.value.bank_account = props.dataFilter.bank_account
    form.value.affiliate = props.dataFilter.affiliate
    form.value.search = props.dataFilter.search
  }
})
</script>

<template>
  <CCallout color="primary" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol lg="9">
        <CRow>
          <CCol lg="4">
            <CRow>
              <CCol md="6" class="mb-3">
                <DatePicker
                  v-model="form.from_date"
                  placeholder="시작일 (From)"
                  @keydown.enter="listFiltering(1)"
                />
              </CCol>
              <CCol md="6" class="mb-3">
                <DatePicker
                  v-model="form.to_date"
                  placeholder="종료일 (To)"
                  @keydown.enter="listFiltering(1)"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol lg="8">
            <CRow>
              <CCol md="6" lg="2" class="mb-3">
                <CFormSelect v-model.number="form.sort" @change="sortSelect">
                  <option value="">구분</option>
                  <option :value="1">입금</option>
                  <option :value="2">출금</option>
                </CFormSelect>
              </CCol>

              <CCol md="6" lg="3" class="mb-3">
                <CFormSelect v-model.number="form.account_category" @change="cateSelect">
                  <option value="">계정분류</option>
                  <option value="asset">자산</option>
                  <option value="liability">부채</option>
                  <option value="equity">자본</option>
                  <option value="revenue">수익</option>
                  <option value="expense">비용</option>
                  <option value="transfer">대체</option>
                  <option value="cancel">취소</option>
                </CFormSelect>
              </CCol>

              <CCol md="6" lg="4" class="mb-3">
                <LedgerAccount
                  v-model="form.account"
                  :options="comAccounts ?? []"
                  :is-search="true"
                  :cate-type="form.account_category || undefined"
                  :sort-type="sortType"
                  @update:modelValue="listFiltering(1)"
                />
              </CCol>

              <CCol md="6" lg="3" class="mb-3">
                <CFormSelect v-model="form.bank_account" @change="listFiltering(1)">
                  <option value="">거래계좌</option>
                  <option v-for="acc in allComBankList" :key="acc.pk" :value="acc.pk">
                    {{ acc.alias_name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="3">
        <CRow>
          <CCol md="6" lg="5" class="mb-3">
            <CFormSelect v-model.number="form.affiliate" @change="listFiltering(1)">
              <option value="">투입 관계회사(프로젝트)</option>
              <option v-for="aff in affiliateList" :key="aff.value" :value="aff.value">
                {{ aff.label }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="7" class="mb-3">
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
        <strong> 거래 건수 조회 결과 : {{ numFormat(bankTransactionCount ?? 0, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
