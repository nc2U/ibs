<script lang="ts" setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'
import { bgLight } from '@/utils/cssMixins'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import type { ContFilter } from '@/store/types/contract'
import { numFormat } from '@/utils/baseMixins'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({ status: { type: String, default: '2' } })
const emit = defineEmits(['cont-filtering'])

const from_date = ref('')
const to_date = ref('')

const form = reactive<ContFilter>({
  limit: '',
  status: props.status,
  order_group: '',
  unit_type: '',
  null_unit: false,
  building: '',
  qualification: '',
  is_sup_cont: '',
  ordering: '-created',
  search: '',
})

const formsCheck = computed(() => {
  const a = form.limit === ''
  const b = form.status === '2'
  const c = form.order_group === ''
  const d = form.unit_type === ''
  const e = form.null_unit === false
  const f = form.building === ''
  const g = form.qualification === ''
  const h = !from_date.value
  const i = !to_date.value
  const j = form.ordering === '-created'
  const k = (form.search as string)?.trim() === ''
  const groupA = a && b && c && d && e
  const groupB = f && g && h && i && j && k
  return groupA && groupB
})

const contractStore = useContract()
const projectDataStore = useProjectData()

const orderGroupList = computed(() => contractStore.orderGroupList)
const contractsCount = computed(() => contractStore.contractsCount)
const buildingList = computed(() => projectDataStore.buildingList)
const simpleTypes = computed(() => projectDataStore.simpleTypes)

watch(from_date, () => listFiltering(1))

watch(to_date, () => listFiltering(1))

watch(
  () => props.status,
  newStatus => {
    form.status = newStatus
  },
)

const listFiltering = (page = 1) => {
  form.search = (form.search as string)?.trim()
  form.from_date = from_date.value
  form.to_date = to_date.value
  nextTick(() => {
    emit('cont-filtering', {
      ...{ page },
      ...form,
    })
  })
}

defineExpose({ listFiltering })

const resetForm = () => {
  form.limit = ''
  form.status = '2'
  form.order_group = ''
  form.unit_type = ''
  form.null_unit = false
  form.building = ''
  form.qualification = ''
  from_date.value = ''
  to_date.value = ''
  form.ordering = '-created'
  form.search = ''
  listFiltering(1)
}

onMounted(() => {
  if (props.status === '1') listFiltering(1)
})
</script>

<template>
  <CCallout color="info" class="pb-0 mb-4" :class="bgLight">
    <CRow>
      <CCol lg="6">
        <CRow>
          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model.number="form.limit" @change="listFiltering(1)">
              <option value="">표시 개수</option>
              <option :value="10" :disabled="form.limit === '' || form.limit === 10">10 개</option>
              <option :value="30" :disabled="form.limit === 30">30 개</option>
              <option :value="50" :disabled="form.limit === 50">50 개</option>
              <!--              <option value="100">100 개</option>-->
            </CFormSelect>
          </CCol>
          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.ordering" @change="listFiltering(1)">
              <option value="-created">등록일시 내림차순</option>
              <option value="created">등록일시 올림차순</option>
              <option value="-contractor__contract_date">계약일자 내림차순</option>
              <option value="contractor__contract_date">계약일자 올림차순</option>
              <option value="-serial_number">일련번호 내림차순</option>
              <option value="serial_number">일련번호 올림차순</option>
              <option value="-contractor__name">계약자명 내림차순</option>
              <option value="contractor__name">계약자명 올림차순</option>
            </CFormSelect>
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.qualification" @change="listFiltering(1)">
              <option value="">등록상태</option>
              <option value="1">일반분양</option>
              <option value="2">미인가조합원</option>
              <option value="3">인가조합원</option>
              <option value="4">부적격조합원</option>
            </CFormSelect>
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.status" @change="listFiltering(1)">
              <option value="1">청약 현황</option>
              <option value="2">계약 현황</option>
            </CFormSelect>
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.order_group" @change="listFiltering(1)">
              <option value="">차수선택</option>
              <option v-for="order in orderGroupList" :key="order.pk" :value="order.pk">
                {{ order.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.unit_type" @change="listFiltering(1)">
              <option value="">타입선택</option>
              <option v-for="type in simpleTypes" :key="type.pk" :value="type.pk">
                {{ type.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="6">
        <CRow>
          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.is_sup_cont" @change="listFiltering(1)">
              <option value="">공급계약 (전체)</option>
              <option value="true">체결</option>
              <option value="false">미체결</option>
            </CFormSelect>
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <CFormSelect v-model="form.building" @change="listFiltering(1)">
              <option value="">동 선택</option>
              <option v-for="bldg in buildingList" :key="bldg.pk" :value="bldg.pk">
                {{ bldg.name }}동
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="4" xl="2" class="pt-2 mb-3 col-form-label">
            <CFormSwitch
              id="null_unit"
              v-model="form.null_unit"
              label="동호 미지정"
              @change="listFiltering(1)"
            />
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <DatePicker
              v-model="from_date"
              placeholder="계약일 (From)"
              @keydown.enter="listFiltering(1)"
            />
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <DatePicker
              v-model="to_date"
              placeholder="계약일 (To)"
              @keydown.enter="listFiltering(1)"
            />
          </CCol>

          <CCol md="4" xl="2" class="mb-3">
            <CInputGroup class="flex-nowrap">
              <CFormInput
                v-model="form.search"
                placeholder="계약자, 전화번호, 일련번호, 비고"
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
        <strong>
          계약 건수 조회 결과 :
          {{ numFormat(contractsCount, 0, 0) }} 건
        </strong>
      </CCol>
      <CCol v-if="!formsCheck" class="text-right mb-0">
        <v-btn color="info" size="small" @click="resetForm"> 검색조건 초기화</v-btn>
      </CCol>
    </CRow>
  </CCallout>
</template>
