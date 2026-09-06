<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { ContractSalesAgent } from '@/store/types/sales'
import { getToday } from '@/utils/baseMixins'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  project: { type: Number, required: true },
  contractOptions: { type: Array as () => { value: number; label: string }[], default: () => [] },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)

const personList = computed(() => salesStore.personList)
const teamList = computed(() => salesStore.teamList)
const policyList = computed(() => salesStore.policyList)

const form = reactive({
  contract: null as number | null,
  contract_info: '',
  sales_person: null as number | null,
  team: null as number | null,
  policy: null as number | null,
  contract_date: getToday(),
  mgm_name: '',
  mgm_phone: '',
  mgm_fee: 0,
  note: '',
})

// 상담사 선택 시 소속 팀 자동 설정
const onPersonChange = () => {
  if (form.sales_person) {
    const person = personList.value.find(p => p.id === form.sales_person)
    if (person) {
      form.team = person.team
    }
  }
}

const resetForm = () => {
  form.contract = null
  form.contract_info = ''
  form.sales_person = null
  form.team = null
  form.policy = null
  form.contract_date = getToday()
  form.mgm_name = ''
  form.mgm_phone = ''
  form.mgm_fee = 0
  form.note = ''
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
    form.sales_person = mapping.sales_person
    form.team = mapping.team
    form.policy = mapping.policy
    form.contract_date = mapping.contract_date || getToday()
    form.mgm_name = mapping.mgm_name || ''
    form.mgm_phone = mapping.mgm_phone || ''
    form.mgm_fee = mapping.mgm_fee || 0
    form.note = mapping.note || ''
  }
  modalRef.value.callModal()
}

const submit = async () => {
  if (!form.contract) {
    alert('계약을 선택해주세요.')
    return
  }
  if (!form.sales_person) {
    alert('담당 영업직원(상담사)을 선택해주세요.')
    return
  }
  if (!form.team) {
    alert('소속 팀을 선택해주세요.')
    return
  }

  const payload: Partial<ContractSalesAgent> = {
    contract: form.contract,
    sales_person: form.sales_person,
    team: form.team,
    policy: form.policy,
    contract_date: form.contract_date || null,
    mgm_name: form.mgm_name.trim(),
    mgm_phone: form.mgm_phone.trim(),
    mgm_fee: form.mgm_fee || 0,
    note: form.note.trim(),
  }

  if (isEdit.value && targetId.value) {
    await salesStore.updateContractAgent(targetId.value, payload)
  } else {
    await salesStore.createContractAgent(payload)
  }
  modalRef.value.close()
  emit('saved')
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
              <option v-for="c in contractOptions" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </CFormSelect>
          </CCol>

          <!-- 담당 영업직원 (상담사) -->
          <CCol md="6">
            <CFormLabel>담당 영업직원 (상담사) <span class="text-danger">*</span></CFormLabel>
            <CFormSelect v-model.number="form.sales_person" required @change="onPersonChange">
              <option :value="null">영업직원을 선택하세요</option>
              <option v-for="p in personList" :key="p.id" :value="p.id">
                [{{ p.duty_display }}] {{ p.name }} ({{ p.team_name }})
              </option>
            </CFormSelect>
          </CCol>

          <!-- 소속 팀 -->
          <CCol md="6">
            <CFormLabel>소속 팀 <span class="text-danger">*</span></CFormLabel>
            <CFormSelect v-model.number="form.team" required>
              <option :value="null">소속 팀 선택</option>
              <option v-for="t in teamList" :key="t.id" :value="t.id">
                {{ t.agency_name ? `[${t.agency_name}] ` : '' }}{{ t.parent_name ? `${t.parent_name} > ` : '' }}{{ t.name }}
              </option>
            </CFormSelect>
          </CCol>

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
            <CFormInput v-model="form.contract_date" type="date" />
          </CCol>

          <!-- MGM 및 소개 수수료 -->
          <CCol md="12" class="pt-2">
            <div class="border-bottom pb-1 text-primary fw-bold">
              <v-icon icon="mdi-handshake" size="small" class="mr-1" /> MGM / 소개 중개사 연계 정보 (선택)
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
        </CRow>
      </CModalBody>
      <CModalFooter>
        <v-btn color="primary" size="small" @click="submit">
          {{ isEdit ? '수정 저장' : '배정하기' }}
        </v-btn>
        <v-btn color="light" size="small" flat @click="modalRef.close()">취소</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>
