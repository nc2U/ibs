<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { CommissionPolicy } from '@/store/types/sales'
import { getToday } from '@/utils/baseMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({
  project: { type: Number, required: true },
  orderGroupList: { type: Array as () => any[], default: () => [] },
  unitTypeList: { type: Array as () => any[], default: () => [] },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)

const form = reactive({
  name: '',
  order_group: null as number | null,
  unit_type: null as number | null,
  agent_fee: 0,
  leader_fee: 0,
  director_fee: 0,
  agency_fee: 0,
  pay_condition: '1' as '1' | '2' | '3' | '4',
  start_date: getToday(),
  end_date: '' as string,
  is_active: true,
})

const totalFee = computed(() => {
  return (
    (form.agent_fee || 0) +
    (form.leader_fee || 0) +
    (form.director_fee || 0) +
    (form.agency_fee || 0)
  )
})

const resetForm = () => {
  form.name = ''
  form.order_group = null
  form.unit_type = null
  form.agent_fee = 0
  form.leader_fee = 0
  form.director_fee = 0
  form.agency_fee = 0
  form.pay_condition = '1'
  form.start_date = getToday()
  form.end_date = ''
  form.is_active = true
  targetId.value = null
  isEdit.value = false
}

const open = (policy?: CommissionPolicy) => {
  resetForm()
  if (policy) {
    isEdit.value = true
    targetId.value = policy.id
    form.name = policy.name
    form.order_group = policy.order_group
    form.unit_type = policy.unit_type
    form.agent_fee = policy.agent_fee
    form.leader_fee = policy.leader_fee
    form.director_fee = policy.director_fee
    form.agency_fee = policy.agency_fee
    form.pay_condition = policy.pay_condition
    form.start_date = policy.start_date
    form.end_date = policy.end_date || ''
    form.is_active = policy.is_active
  }
  modalRef.value.callModal()
}

const submit = async () => {
  if (!form.name.trim()) {
    alert('수수료 정책명을 입력해주세요.')
    return
  }
  if (!form.start_date) {
    alert('적용 시작일을 입력해주세요.')
    return
  }

  const payload: Partial<CommissionPolicy> = {
    project: props.project,
    name: form.name.trim(),
    order_group: form.order_group || null,
    unit_type: form.unit_type || null,
    agent_fee: form.agent_fee || 0,
    leader_fee: form.leader_fee || 0,
    director_fee: form.director_fee || 0,
    agency_fee: form.agency_fee || 0,
    pay_condition: form.pay_condition,
    start_date: form.start_date,
    end_date: form.end_date || null,
    is_active: form.is_active,
  }

  if (isEdit.value && targetId.value) {
    await salesStore.updatePolicy(targetId.value, payload)
  } else {
    await salesStore.createPolicy(payload)
  }
  modalRef.value.close()
  emit('saved')
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '수수료 정책 수정' : '신규 수수료 정책 등록' }}</template>
    <template #default>
      <CModalBody>
        <CRow class="g-3">
          <CCol md="12">
            <CFormLabel>정책명 <span class="text-danger">*</span></CFormLabel>
            <CFormInput
              v-model="form.name"
              placeholder="예: 84A타입 정규 분양 수수료 기준표"
              required
              @keydown.enter="submit"
            />
          </CCol>

          <CCol md="6">
            <CFormLabel>적용 차수</CFormLabel>
            <CFormSelect v-model.number="form.order_group">
              <option :value="null">전체 차수 공통 적용</option>
              <option v-for="og in orderGroupList" :key="og.pk" :value="og.pk">
                {{ og.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="6">
            <CFormLabel>적용 유니트 타입</CFormLabel>
            <CFormSelect v-model.number="form.unit_type">
              <option :value="null">전체 타입 공통 적용</option>
              <option v-for="t in unitTypeList" :key="t.pk" :value="t.pk">
                {{ t.name }} ({{ t.color }})
              </option>
            </CFormSelect>
          </CCol>

          <!-- 직급별 건당 수수료 금액 -->
          <CCol md="12" class="pt-2">
            <div
              class="border-bottom pb-1 text-primary fw-bold d-flex justify-content-between align-items-center"
            >
              <span
                ><v-icon icon="mdi-cash-multiple" size="small" class="mr-1" /> 직급별 건당 수수료
                (원)</span
              >
              <span class="text-danger fw-bold fs-6">
                건당 총액: {{ totalFee.toLocaleString() }} 원
              </span>
            </div>
          </CCol>

          <CCol md="6" lg="3">
            <CFormLabel>상담사 수수료</CFormLabel>
            <CInputGroup>
              <CFormInput
                v-model.number="form.agent_fee"
                type="number"
                step="10000"
                min="0"
                @keydown.enter="submit"
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>

          <CCol md="6" lg="3">
            <CFormLabel>팀장 수수료</CFormLabel>
            <CInputGroup>
              <CFormInput
                v-model.number="form.leader_fee"
                type="number"
                step="10000"
                min="0"
                @keydown.enter="submit"
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>

          <CCol md="6" lg="3">
            <CFormLabel>본부장 수수료</CFormLabel>
            <CInputGroup>
              <CFormInput
                v-model.number="form.director_fee"
                type="number"
                step="10000"
                min="0"
                @keydown.enter="submit"
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>

          <CCol md="6" lg="3">
            <CFormLabel>대행사 수수료 (본사몫)</CFormLabel>
            <CInputGroup>
              <CFormInput
                v-model.number="form.agency_fee"
                type="number"
                step="10000"
                min="0"
                @keydown.enter="submit"
              />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>

          <!-- 지급 조건 및 기간 -->
          <CCol md="12" class="pt-2">
            <div class="border-bottom pb-1 text-primary fw-bold">
              <v-icon icon="mdi-clock-check-outline" size="small" class="mr-1" /> 지급 조건 및 적용
              기간
            </div>
          </CCol>

          <CCol md="6">
            <CFormLabel>수수료 지급 조건</CFormLabel>
            <CFormSelect v-model="form.pay_condition">
              <option value="1">계약금 100% 완납 시 전액 지급</option>
              <option value="2">계약금 1차 납부 시 50%, 2차 완납 시 50% 분할</option>
              <option value="3">공급계약 체결 시 지급</option>
              <option value="4">청약/가계약금 납부 시 선지급</option>
            </CFormSelect>
          </CCol>

          <CCol md="3">
            <CFormLabel>적용 시작일 <span class="text-danger">*</span></CFormLabel>
            <DatePicker v-model="form.start_date" required placeholder="적용 시작일" />
          </CCol>

          <CCol md="3">
            <CFormLabel>적용 종료일</CFormLabel>
            <DatePicker v-model="form.end_date" placeholder="종료일 없을 시 미지정" />
          </CCol>

          <CCol md="12" class="d-flex align-items-center pt-2">
            <CFormCheck
              id="policy_is_active"
              v-model="form.is_active"
              label="이 정책을 현재 활성화하여 적용 (활성 상태)"
            />
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <v-btn color="primary" size="small" @click="submit">
          {{ isEdit ? '수정 저장' : '등록하기' }}
        </v-btn>
        <v-btn color="light" size="small" flat @click="modalRef.close()">취소</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>
