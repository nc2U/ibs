<script lang="ts" setup>
import { computed, type ComputedRef, inject, nextTick, onBeforeMount, ref, watch } from 'vue'
import { bgLight } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'
import { useContract } from '@/store/pinia/contract.ts'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import type { DataFilter, ProjectBank } from '@/store/types/proLedger.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import LedgerAccount from '@/components/LedgerAccount/Index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'

interface Props {
  project?: number | null
  imprest?: boolean
  imprestOnly?: boolean
  dataFilter?: DataFilter
}

const props = withDefaults(defineProps<Props>(), {
  project: null,
  imprest: false,
  imprestOnly: false,
  dataFilter: () => ({}),
})

const emit = defineEmits(['list-filtering'])

const emptyFilter = (): DataFilter => ({
  page: 1,
  project: null,
  from_date: '',
  to_date: '',
  sort: null,
  account_category: '',
  account: null,
  bank_account: null,
  contract: null,
  search: '',
})

const form = ref<DataFilter>(emptyFilter())

const formsCheck = computed(() => {
  const a = !form.value.from_date
  const b = !form.value.to_date
  const c = !form.value.sort
  const d = !form.value.account_category
  const e = !form.value.account
  const f = !form.value.bank_account
  const g = !form.value.contract
  const h = !(form.value.search ?? '')?.trim()
  return a && b && c && d && e && f && g && h
})

const contStore = useContract()
const getContracts = computed(() => contStore.getContracts)

const proAccounts = inject<ComputedRef<AccountPicker[]>>('proAccounts')
const allProBankList = inject<ComputedRef<ProjectBank[]>>('allProBankList')
const proBankTransCount = inject<ComputedRef<number>>('proBankTransCount')

const selectableBanks = computed(() => {
  const list = allProBankList?.value ?? []
  return props.imprestOnly ? list.filter(acc => acc.is_imprest) : list
})

const sortType = computed(() => {
  if (form.value.sort === 1) return 'deposit' // 입금
  if (form.value.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

const listFiltering = (page = 1) => {
  form.value.page = page
  form.value.search = (form.value.search ?? '')?.trim()
  const is_imprest = props.imprestOnly ? 'true' : props.imprest ? 'all' : 'false'
  nextTick(() => {
    emit('list-filtering', { ...form.value, is_imprest })
  })
}

watch(
  () => props.project,
  () => {
    form.value = emptyFilter()
  },
)

watch(
  () => form.value.from_date,
  (val, oldVal) => {
    if (val !== oldVal) listFiltering(1)
  },
)
watch(
  () => form.value.to_date,
  (val, oldVal) => {
    if (val !== oldVal) listFiltering(1)
  },
)

const sortSelect = () => {
  form.value.account_category = ''
  form.value.account = null
  listFiltering(1)
}

const cateSelect = () => {
  form.value.account = null
  listFiltering(1)
}

const clearContractFilter = () => {
  form.value.contract = null
  listFiltering(1)
}

defineExpose({ listFiltering })

const resetForm = () => {
  form.value = emptyFilter()
  listFiltering(1)
}

onBeforeMount(() => {
  if (props.dataFilter) {
    form.value.from_date = props.dataFilter.from_date ?? ''
    form.value.to_date = props.dataFilter.to_date ?? ''
    form.value.sort = props.dataFilter.sort ?? null
    form.value.account_category = props.dataFilter.account_category ?? ''
    form.value.account = props.dataFilter.account ?? null
    form.value.bank_account = props.dataFilter.bank_account ?? null
    form.value.contract = props.dataFilter.contract ?? null
    form.value.search = props.dataFilter.search ?? ''
  }
})
</script>

<template>
  <CCallout color="success" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol lg="8">
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

              <CCol md="6" lg="2" class="mb-3">
                <CFormSelect v-model="form.account_category" @change="cateSelect">
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

              <CCol md="6" lg="5" class="mb-3">
                <LedgerAccount
                  v-model="form.account"
                  :options="proAccounts ?? []"
                  :is-search="true"
                  :cate-type="form.account_category || undefined"
                  :sort-type="sortType"
                  @update:modelValue="listFiltering(1)"
                />
              </CCol>

              <CCol md="6" lg="3" class="mb-3">
                <CFormSelect v-model.number="form.bank_account" @change="listFiltering(1)">
                  <option value="">거래계좌</option>
                  <option v-for="acc in selectableBanks" :key="acc.pk!" :value="acc.pk">
                    {{ acc.alias_name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="4">
        <CRow>
          <CCol md="6" lg="5" class="mb-3">
            <MultiSelect
              v-model.number="form.contract"
              mode="single"
              :options="getContracts"
              placeholder="계약 정보 선택"
              @select="listFiltering(1)"
              @clear="clearContractFilter"
            />
          </CCol>
          <CCol md="6" lg="7" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                placeholder="적요, 거래처 검색"
                aria-label="검색어"
                @keydown.enter="listFiltering(1)"
              />
              <CInputGroupText class="pointer" @click="listFiltering(1)">검색</CInputGroupText>
            </CInputGroup>
          </CCol>
        </CRow>
      </CCol>
    </CRow>

    <CRow>
      <CCol color="warning" class="p-2 ps-3">
        <strong> 거래 건수 조회 결과 : {{ numFormat(proBankTransCount ?? 0, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-end mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
