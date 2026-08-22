<script setup lang="ts">
import { computed, onMounted } from 'vue'

interface AppointmentTarget {
  name: string
  current_dept: string
  current_position: string
  new_dept: string
  new_position: string
  type_desc: string
  note?: string
}

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const targetsList = computed<AppointmentTarget[]>(() => {
  return Array.isArray(props.modelValue.targets) ? props.modelValue.targets : []
})

const appointmentTypes = [
  { value: 'PROMOTION', label: '승진 / 승격' },
  { value: 'TRANSFER', label: '부서이동 / 전보' },
  { value: 'APPOINT', label: '보직 임명 / 해임' },
  { value: 'HIRE', label: '신규 채용 / 입사' },
  { value: 'LEAVE_RETURN', label: '휴직 / 복직' },
  { value: 'RETIRE', label: '퇴직 / 면직' },
  { value: 'DISPATCH', label: '현장 파견 / 복귀' },
  { value: 'ORGANIZATION', label: '조직 개편 발령' },
  { value: 'OTHER', label: '기타 발령' },
]

const updateField = (key: string, val: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: val,
  })
}

const addTarget = () => {
  const targets: AppointmentTarget[] = [...(props.modelValue.targets || [])]
  targets.push({
    name: '',
    current_dept: '',
    current_position: '',
    new_dept: '',
    new_position: '',
    type_desc: '승진 및 전보',
    note: '',
  })
  updateField('targets', targets)
}

const removeTarget = (index: number | string) => {
  const i = typeof index === 'string' ? parseInt(index, 10) : index
  const targets: AppointmentTarget[] = [...(props.modelValue.targets || [])]
  targets.splice(i, 1)
  updateField('targets', targets)
}

const updateTarget = (index: number | string, field: keyof AppointmentTarget, val: string) => {
  const i = typeof index === 'string' ? parseInt(index, 10) : index
  const targets: AppointmentTarget[] = [...(props.modelValue.targets || [])]
  if (targets[i]) {
    targets[i] = {
      ...targets[i],
      [field]: val,
    }
    updateField('targets', targets)
  }
}

onMounted(() => {
  const initial = { ...props.modelValue }
  let changed = false

  if (!initial.appointment_type) {
    initial.appointment_type = 'PROMOTION'
    changed = true
  }
  if (!initial.effective_date) {
    initial.effective_date = new Date().toISOString().substring(0, 10)
    changed = true
  }
  if (!initial.targets || !initial.targets.length) {
    initial.targets = [
      {
        name: '',
        current_dept: '',
        current_position: '',
        new_dept: '',
        new_position: '',
        type_desc: '승진',
        note: '',
      },
    ]
    changed = true
  }
  if (initial.is_public_notice === undefined) {
    initial.is_public_notice = true
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="hr-appointment-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilUserFollow" class="me-1" />
      인사발령 기본 정보
    </h6>

    <!-- 발령 구분 & 발령 시행일 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">발령 구분</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="modelValue.appointment_type ?? 'PROMOTION'"
          required
          @change="updateField('appointment_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in appointmentTypes" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">발령 시행일</CFormLabel>
      <CCol sm="4">
        <CFormInput
          type="date"
          :value="modelValue.effective_date ?? ''"
          required
          @input="updateField('effective_date', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 발령 사유 및 배경 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">발령 사유 / 배경</CFormLabel>
      <CCol sm="10">
        <CFormTextarea
          :value="modelValue.reason ?? ''"
          rows="3"
          placeholder="인사발령을 시행하는 사유 및 기대 효과를 기술해 주세요. (예: 2026년 하반기 조직개편에 따른 신규 부서 편제 및 적재적소 인재 배치)"
          required
          @input="updateField('reason', ($event.target as HTMLTextAreaElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 발령 대상자 목록 카드 -->
    <div class="card mb-3 border">
      <div class="card-header d-flex justify-content-between align-items-center bg-more-white py-2">
        <span class="fw-bold text-body">
          <CIcon name="cilPeople" class="me-1 text-primary" />
          발령 대상자 명단 (총 {{ targetsList.length }}명)
        </span>
        <CButton color="primary" size="sm" variant="outline" @click="addTarget">
          + 대상자 추가
        </CButton>
      </div>
      <div class="card-body p-2">
        <div class="table-responsive">
          <table class="table table-bordered table-sm mb-0 align-middle">
            <thead class="table-light text-center small">
              <tr>
                <th style="width: 40px">#</th>
                <th style="width: 100px">성명</th>
                <th style="width: 150px">현 소속(부서)</th>
                <th style="width: 120px">현 직급/직책</th>
                <th style="width: 150px" class="text-primary">발령 소속(부서)</th>
                <th style="width: 120px" class="text-primary">발령 직급/직책</th>
                <th style="width: 110px">발령 구분</th>
                <th>비고</th>
                <th style="width: 40px">삭제</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in targetsList" :key="idx">
                <td class="text-center text-muted small">{{ idx + 1 }}</td>
                <td>
                  <CFormInput
                    size="sm"
                    :value="item.name"
                    placeholder="성명"
                    @input="updateTarget(idx, 'name', ($event.target as HTMLInputElement).value)"
                  />
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    :value="item.current_dept"
                    placeholder="예: 개발기획팀"
                    @input="
                      updateTarget(idx, 'current_dept', ($event.target as HTMLInputElement).value)
                    "
                  />
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    :value="item.current_position"
                    placeholder="예: 과장 / 팀원"
                    @input="
                      updateTarget(
                        idx,
                        'current_position',
                        ($event.target as HTMLInputElement).value,
                      )
                    "
                  />
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    class="border-primary"
                    :value="item.new_dept"
                    placeholder="예: 전략사업본부"
                    @input="
                      updateTarget(idx, 'new_dept', ($event.target as HTMLInputElement).value)
                    "
                  />
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    class="border-primary"
                    :value="item.new_position"
                    placeholder="예: 차장 / 팀장"
                    @input="
                      updateTarget(idx, 'new_position', ($event.target as HTMLInputElement).value)
                    "
                  />
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    :value="item.type_desc"
                    placeholder="예: 승진/전보"
                    @input="
                      updateTarget(idx, 'type_desc', ($event.target as HTMLInputElement).value)
                    "
                  />
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    :value="item.note"
                    placeholder="비고"
                    @input="updateTarget(idx, 'note', ($event.target as HTMLInputElement).value)"
                  />
                </td>
                <td class="text-center">
                  <CButton
                    color="danger"
                    size="sm"
                    variant="ghost"
                    class="p-0"
                    :disabled="targetsList.length <= 1"
                    @click="removeTarget(idx)"
                  >
                    ×
                  </CButton>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 공지 설정 & 특이사항 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">전사 공지</CFormLabel>
      <CCol sm="4" class="d-flex align-items-center">
        <CFormCheck
          id="publicNoticeCheck"
          label="결재 완료 시 전사 임직원 공지사항 게시"
          :checked="modelValue.is_public_notice ?? true"
          @change="updateField('is_public_notice', ($event.target as HTMLInputElement).checked)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">특이사항 / 비고</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.note ?? ''"
          placeholder="인사위원회 심의 결과 또는 추가 참고사항"
          @input="updateField('note', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
