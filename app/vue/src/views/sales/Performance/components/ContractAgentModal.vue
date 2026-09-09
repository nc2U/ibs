<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { ContractSalesAgent } from '@/store/types/sales'
import { getToday } from '@/utils/baseMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({
  project: { type: Number, required: true },
  contractOptions: { type: Array as () => { value: number; label: string }[], default: () => [] },
  mappedContractIds: { type: Array as () => number[], default: () => [] },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)

const personList = computed(() => salesStore.personList)
const agencyList = computed(() => salesStore.agencyList)
// 외주 대행사 목록 (is_direct_managed === false)
const outsourcedAgencies = computed(() =>
  agencyList.value.filter(a => !a.is_direct_managed && a.is_active),
)
const policyList = computed(() => salesStore.policyList)

// 이미 다른 담당자가 배정된 계약은 신규 등록 시 제외 (현재 편집 중인 계약은 포함)
const availableContractOptions = computed(() => {
  if (isEdit.value) return props.contractOptions
  const mappedSet = new Set(props.mappedContractIds)
  return props.contractOptions.filter(c => !mappedSet.has(c.value) || c.value === form.contract)
})

// 배정 유형: 'direct' (직영/인력 배정) vs 'agency' (외주 대행사 직배정)
const assignmentType = ref<'direct' | 'agency'>('direct')

const form = reactive({
  contract: null as number | null,
  contract_info: '',
  agency: null as number | null,
  sales_person: null as number | null,
  policy: null as number | null,
  contract_date: getToday(),
  mgm_name: '',
  mgm_phone: '',
  mgm_fee: 0,
  note: '',
  is_settlement_approved: true,
  approval_note: '',
})

// 선택된 상담사의 소속 정보 표시용 (읽기 전용)
const selectedPerson = computed(() => {
  if (!form.sales_person) return null
  return personList.value.find(item => item.id === form.sales_person) || null
})

const selectedPersonTeamInfo = computed(() => {
  if (!selectedPerson.value) return ''
  const p = selectedPerson.value
  const agencyName = p.agency_name ? `[${p.agency_name}] ` : ''
  return `${agencyName}${p.team_name || ''}`
})

// 상담사 소속 팀의 팀장 존재 여부 진단
const selectedPersonTeamWarning = computed(() => {
  if (assignmentType.value !== 'direct' || !selectedPerson.value) return null
  const p = selectedPerson.value
  // duty='1'(상담사) 또는 지원직인 경우 팀장 부재 여부 체크
  if (p.duty === '1' || p.duty === '5') {
    const hasLeader = personList.value.some(
      other => other.team === p.team && other.duty === '2' && other.status === '1',
    )
    if (!hasLeader) {
      return '소속 팀에 재직 중인 팀장이 없습니다. 정산 시 상위 본부장에게 합산 배정되거나 대행사 이익으로 귀속됩니다.'
    }
  }
  return null
})

const resetForm = () => {
  assignmentType.value = 'direct'
  form.contract = null
  form.contract_info = ''
  form.agency = null
  form.sales_person = null
  form.policy = null
  form.contract_date = getToday()
  form.mgm_name = ''
  form.mgm_phone = ''
  form.mgm_fee = 0
  form.note = ''
  form.is_settlement_approved = true
  form.approval_note = ''
  targetId.value = null
  isEdit.value = false
}

const open = (mapping?: ContractSalesAgent, defaultContractId?: number) => {
  resetForm()
  if (defaultContractId) {
    form.contract = defaultContractId
  }
  if (mapping) {
    isEdit.value = true
    targetId.value = mapping.id
    form.contract = mapping.contract
    form.contract_info = `${mapping.contract_serial || ''} (${mapping.contractor_name || ''} - ${mapping.unit_info || ''})`
    form.agency = mapping.agency || null
    form.sales_person = mapping.sales_person || null
    form.policy = mapping.policy
    form.contract_date = mapping.contract_date || getToday()
    form.mgm_name = mapping.mgm_name || ''
    form.mgm_phone = mapping.mgm_phone || ''
    form.mgm_fee = mapping.mgm_fee || 0
    form.note = mapping.note || ''
    form.is_settlement_approved = mapping.is_settlement_approved ?? true
    form.approval_note = mapping.approval_note || ''

    // 외주 대행사 직배정 건인지 판별
    if (mapping.agency && !mapping.sales_person) {
      assignmentType.value = 'agency'
    } else {
      assignmentType.value = 'direct'
    }
  }
  modalRef.value.callModal()
}

const submit = async () => {
  if (!form.contract) {
    alert('계약을 선택해주세요.')
    return
  }

  if (assignmentType.value === 'agency') {
    if (!form.agency) {
      alert('외주 대행사를 선택해주세요.')
      return
    }
  } else {
    if (!form.sales_person) {
      alert('담당 영업직원(상담사)을 선택해주세요.')
      return
    }
  }

  const payload: Partial<ContractSalesAgent> = {
    contract: form.contract,
    agency: assignmentType.value === 'agency' ? form.agency : null,
    sales_person: assignmentType.value === 'direct' ? form.sales_person : null,
    team: null, // 백엔드 save()에서 sales_person 소속으로 자동 세팅됨
    policy: form.policy,
    contract_date: form.contract_date || null,
    mgm_name: form.mgm_name.trim(),
    mgm_phone: form.mgm_phone.trim(),
    mgm_fee: form.mgm_fee || 0,
    note: form.note.trim(),
    is_settlement_approved: form.is_settlement_approved,
    approval_note: form.approval_note.trim(),
  }

  if (isEdit.value && targetId.value) {
    await salesStore.updateContractAgent(targetId.value, payload)
  } else {
    await salesStore.createContractAgent(payload)
  }
  modalRef.value.close()
  emit('saved')
}

const removeMapping = async () => {
  if (!targetId.value) return
  if (confirm('담당자 배정을 해제하시겠습니까?')) {
    await salesStore.deleteContractAgent(targetId.value)
    modalRef.value.close()
    emit('saved')
  }
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '계약 영업 담당자 수정' : '계약 영업 담당자 지정' }}</template>
    <template #default>
      <CModalBody>
        <CRow class="g-3">
          <!-- 대상 계약 선택 -->
          <CCol md="12">
            <CFormLabel>대상 분양 계약 <span class="text-danger">*</span></CFormLabel>
            <div v-if="isEdit" class="form-control bg-light font-weight-bold">
              {{ form.contract_info || `계약 번호 #${form.contract}` }}
            </div>
            <CFormSelect v-else v-model.number="form.contract" required>
              <option :value="null">배정할 계약을 선택하세요</option>
              <option v-for="c in availableContractOptions" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </CFormSelect>
          </CCol>

          <!-- 배정 방식 선택 (직영 영업직원 vs 외주 대행사 직배정) -->
          <CCol md="12">
            <CFormLabel class="fw-bold">배정 방식 <span class="text-danger">*</span></CFormLabel>
            <div class="d-flex gap-4 p-2 bg-light rounded border">
              <CFormCheck
                id="assignDirectRadio"
                v-model="assignmentType"
                type="radio"
                name="assignmentType"
                value="direct"
                label="직영 영업인력 배정 (상담사 직접 배정)"
              />
              <CFormCheck
                id="assignAgencyRadio"
                v-model="assignmentType"
                type="radio"
                name="assignmentType"
                value="agency"
                label="외주 대행사 직배정 (대행사 단위 배정)"
              />
            </div>
          </CCol>

          <!-- [외주 대행사 직배정] 외주 대행사 선택 -->
          <template v-if="assignmentType === 'agency'">
            <CCol md="12">
              <CFormLabel>외주 분양대행사 <span class="text-danger">*</span></CFormLabel>
              <CFormSelect v-model.number="form.agency" required>
                <option :value="null">외주 분양대행사를 선택하세요</option>
                <option v-for="a in outsourcedAgencies" :key="a.id" :value="a.id">
                  {{ a.name }}
                </option>
              </CFormSelect>
              <div class="form-text text-muted small">
                * 외주 대행사의 경우 상담사 및 팀을 개별 관리하지 않고 대행사에 계약 건을 직접 배정합니다.
              </div>
            </CCol>
          </template>

          <!-- [직영/인력 배정] 담당 영업직원 (상담사) 선택 -->
          <template v-else>
            <CCol md="12">
              <CFormLabel>담당 영업직원 (상담사) <span class="text-danger">*</span></CFormLabel>
              <CFormSelect v-model.number="form.sales_person" required>
                <option :value="null">담당 상담사를 선택하세요</option>
                <option v-for="p in personList" :key="p.id" :value="p.id">
                  [{{ p.duty_display }}] {{ p.name }} ({{ p.team_name || '팀 미지정' }})
                </option>
              </CFormSelect>
              <div v-if="selectedPersonTeamInfo" class="mt-1 d-flex align-items-center gap-2">
                <CBadge color="info" shape="rounded-pill">
                  소속: {{ selectedPersonTeamInfo }}
                </CBadge>
              </div>
              <div v-if="selectedPersonTeamWarning" class="mt-1">
                <CAlert color="warning" class="py-1 px-2 mb-0 small text-body-secondary border-warning">
                  <v-icon icon="mdi-alert" size="small" class="text-warning mr-1" />
                  {{ selectedPersonTeamWarning }}
                </CAlert>
              </div>
            </CCol>
          </template>

          <!-- 적용 수수료 정책 -->
          <CCol md="6">
            <CFormLabel>적용 수수료 정책</CFormLabel>
            <CFormSelect v-model.number="form.policy">
              <option :value="null">기본 유니트 정책 자동 적용</option>
              <option v-for="pol in policyList" :key="pol.id" :value="pol.id">
                {{ pol.name }} (건당: {{ pol.agent_fee.toLocaleString() }}원)
              </option>
            </CFormSelect>
          </CCol>

          <!-- 성과 인정일 -->
          <CCol md="6">
            <CFormLabel>영업 성과 인정일</CFormLabel>
            <DatePicker v-model="form.contract_date" placeholder="성과 인정일" />
          </CCol>

          <!-- MGM 및 소개 수수료 -->
          <CCol md="12" class="pt-2">
            <div class="border-bottom pb-1 text-primary fw-bold">
              <v-icon icon="mdi-handshake" size="small" class="mr-1" /> MGM / 소개 중개사 연계 정보
              (선택)
            </div>
          </CCol>

          <CCol md="4">
            <CFormLabel>MGM / 소개자 성명</CFormLabel>
            <CFormInput v-model="form.mgm_name" placeholder="예: OO공인중개사 / 김철수" />
          </CCol>

          <CCol md="4">
            <CFormLabel>MGM 연락처</CFormLabel>
            <CFormInput v-model="form.mgm_phone" placeholder="010-0000-0000" />
          </CCol>

          <CCol md="4">
            <CFormLabel>MGM 수수료 (원)</CFormLabel>
            <CInputGroup>
              <CFormInput v-model.number="form.mgm_fee" type="number" step="10000" min="0" />
              <CInputGroupText>원</CInputGroupText>
            </CInputGroup>
          </CCol>

          <CCol md="12">
            <CFormLabel>비고 / 특이사항</CFormLabel>
            <CFormInput v-model="form.note" placeholder="계약 체결 경위, 특약 메모 등" />
          </CCol>

          <!-- 수수료 정산 승인 / 보류 관리 -->
          <CCol md="12" class="pt-2">
            <div
              class="border-bottom pb-1 text-primary fw-bold d-flex justify-content-between align-items-center"
            >
              <span>
                <v-icon icon="mdi-check-decagram-outline" size="small" class="mr-1" />
                수수료 정산 승인 관리
              </span>
              <CBadge :color="form.is_settlement_approved ? 'success' : 'warning'">
                {{ form.is_settlement_approved ? '정산 승인 완료' : '정산 보류 (미승인)' }}
              </CBadge>
            </div>
          </CCol>

          <CCol md="12">
            <div class="p-3 border rounded bg-more-light">
              <CFormCheck
                id="isSettlementApprovedCheck"
                v-model="form.is_settlement_approved"
                label="이 계약을 수수료 정산 대상 건으로 최종 승인합니다."
                class="fw-bold text-body mb-2"
              />
              <div class="small text-muted mb-2">
                * 체크 해제 시: 담당자는 배정되지만
                <strong>수수료 정산 계산 대상에서 자동으로 제외</strong>됩니다.<br />
                * 서류 완비 및 계약금 완납이 확인된 후 언제든지 승인으로 전환할 수 있습니다.
              </div>
              <div v-if="!form.is_settlement_approved" class="mt-2">
                <CFormLabel class="text-danger fw-bold small">
                  정산 보류 사유 (필수 권장)
                </CFormLabel>
                <CFormInput
                  v-model="form.approval_note"
                  placeholder="예: 계약금 2차 분납 500만원 미납, 인감증명서 미징구 등"
                />
              </div>
            </div>
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter class="d-flex justify-content-between">
        <div>
          <v-btn v-if="isEdit" color="danger" variant="text" size="small" @click="removeMapping">
            <v-icon icon="mdi-account-remove" size="small" class="mr-1" />
            배정 해제
          </v-btn>
        </div>
        <div class="d-flex gap-2">
          <v-btn color="primary" size="small" @click="submit">
            {{ isEdit ? '수정 저장' : '배정하기' }}
          </v-btn>
          <v-btn color="light" size="small" flat @click="modalRef.close()">취소</v-btn>
        </div>
      </CModalFooter>
    </template>
  </FormModal>
</template>
