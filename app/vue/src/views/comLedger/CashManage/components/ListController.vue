<script lang="ts" setup>
import { ref, computed, watch, nextTick, type PropType } from 'vue'
import type { Project } from '@/store/types/project'
import { useComCash, type DataFilter } from '@/store/pinia/comCash'
import { numFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

defineProps({ projects: { type: Array as PropType<Project[]>, default: () => [] } })
const emit = defineEmits(['list-filtering'])

const from_date = ref('')
const to_date = ref('')

const form = ref<DataFilter>({
  page: 1,
  company: null,
  sort: null,
  account_d1: null,
  account_d2: null,
  account_d3: null,
  project: null,
  is_return: false,
  bank_account: null,
  search: '',
})

const formsCheck = computed(() => {
  const a = !from_date.value
  const b = !to_date.value
  const c = !form.value.sort
  const d = !form.value.account_d1
  const e = !form.value.account_d2
  const f = !form.value.account_d3
  const g = !form.value.bank_account
  const h = !form.value.search?.trim()
  return a && b && c && d && e && f && g && h
})

const useComCashStore = useComCash()
const formAccD1List = computed(() => useComCashStore.formAccD1List)
const formAccD2List = computed(() => useComCashStore.formAccD2List)
const formAccD3List = computed(() => useComCashStore.formAccD3List)
const allComBankList = computed(() => useComCashStore.allComBankList)
const cashBookCount = computed(() => useComCashStore.cashBookCount)

watch(from_date, () => listFiltering(1))
watch(to_date, () => listFiltering(1))

//   methods: {
const sortSelect = () => {
  listFiltering(1)
  form.value.account_d1 = null
  form.value.account_d2 = null
  form.value.account_d3 = null
}
const accountD1Select = () => {
  listFiltering(1)
  form.value.account_d2 = null
  form.value.account_d3 = null
}
const accountD2Select = () => {
  listFiltering(1)
  form.value.account_d3 = null
}

const listFiltering = (page = 1) => {
  form.value.page = page
  form.value.search = form.value.search?.trim()
  form.value.from_date = from_date.value
  form.value.to_date = to_date.value
  nextTick(() => {
    emit('list-filtering', { ...form.value })
  })
}

defineExpose({ listFiltering })

const resetForm = () => {
  from_date.value = ''
  to_date.value = ''
  form.value.sort = null
  form.value.account_d1 = null
  form.value.account_d2 = null
  form.value.account_d3 = null
  form.value.project = null
  form.value.is_return = false
  form.value.bank_account = null
  form.value.search = ''
  listFiltering(1)
}
</script>

<template>
  <CCallout color="primary" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol lg="9">
        <CRow>
          <CCol lg="3">
            <CRow>
              <CCol md="6" class="mb-3">
                <DatePicker
                  v-model="from_date"
                  placeholder="시작일 (From)"
                  @keydown.enter="listFiltering(1)"
                />
              </CCol>
              <CCol md="6" class="mb-3">
                <DatePicker
                  v-model="to_date"
                  placeholder="종료일 (To)"
                  @keydown.enter="listFiltering(1)"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol lg="9">
            <CRow>
              <CCol md="6" lg="2" class="mb-3">
                <CFormSelect v-model="form.sort" @change="sortSelect">
                  <option value="">구분</option>
                  <option value="1">입금</option>
                  <option value="2">출금</option>
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
                <CFormSelect
                  v-model="form.account_d2"
                  :disabled="!form.account_d1"
                  @change="accountD2Select"
                >
                  <option value="">계정[중분류]</option>
                  <option v-for="acc2 in formAccD2List" :key="acc2.pk" :value="acc2.pk">
                    {{ acc2.name }}
                  </option>
                </CFormSelect>
              </CCol>

              <CCol md="6" lg="2" class="mb-3">
                <CFormSelect
                  v-model="form.account_d3"
                  :disabled="!form.account_d1"
                  @change="listFiltering(1)"
                >
                  <option value="">계정[소분류]</option>
                  <option v-for="acc3 in formAccD3List" :key="acc3.pk" :value="acc3.pk">
                    {{ acc3.name }}
                  </option>
                </CFormSelect>
              </CCol>

              <CCol md="6" lg="2" class="mb-3">
                <CFormSelect
                  v-model.number="form.project"
                  :disabled="!form.account_d3"
                  @change="listFiltering(1)"
                >
                  <option value="">투입 프로젝트</option>
                  <option v-for="proj in projects" :key="proj.pk" :value="proj.pk">
                    {{ proj.name }}
                  </option>
                </CFormSelect>
              </CCol>

              <CCol md="6" lg="2" class="pt-2 mb-3">
                <CFormSwitch
                  v-model="form.is_return"
                  label="반환 정산 여부"
                  id="form-is-return"
                  :disabled="!form.account_d3"
                  @change="listFiltering(1)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="3">
        <CRow>
          <CCol md="6" lg="5" class="mb-3">
            <CFormSelect v-model="form.bank_account" @change="listFiltering(1)">
              <option value="">거래계좌</option>
              <option v-for="acc in allComBankList" :key="acc.pk" :value="acc.pk">
                {{ acc.alias_name }}
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
        <strong> 거래 건수 조회 결과 : {{ numFormat(cashBookCount, 0, 0) }} 건 </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
