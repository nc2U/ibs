<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { isValidate } from '@/utils/helper.ts'
import { type StaffCareer } from '@/store/types/company.ts'
import { TableSecondary, AlertSecondary } from '@/utils/cssMixins.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import Pagination from '@/components/Pagination'
import TableTitleRow from '@/components/TableTitleRow.vue'

const props = withDefaults(
  defineProps<{
    company?: string | null
    excelUrl?: string
    excelFilename?: string
    selectedStaff?: number | null
    activePage?: number
  }>(),
  {
    company: null,
    excelUrl: '',
    excelFilename: '',
    selectedStaff: null,
    activePage: 1,
  },
)

const emit = defineEmits<{
  (e: 'multi-submit', payload: StaffCareer, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'page-select', page: number): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const comStore = useCompany()
const staffCareerList = computed(() => comStore.staffCareerList)
const staffCareersCount = computed(() => comStore.staffCareersCount)
const allStaffList = computed(() => comStore.allStaffList)

const getPkStaffs = computed(() =>
  allStaffList.value.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'})`,
  })),
)

const refFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

type StaffCareerFormState = Omit<StaffCareer, 'staff'> & { staff: number | null }

const form = ref<StaffCareerFormState>({
  pk: undefined,
  company: undefined,
  staff: null,
  company_name: '',
  department_name: '',
  position_title: '',
  assigned_tasks: '',
  start_date: '',
  end_date: null,
  recognized_ratio: 100,
  note: '',
})

const origForm = ref<StaffCareer | null>(null)
const isEdit = ref(false)
const validated = ref(false)
const submitting = ref(false)

const canSubmit = computed(() => (isEdit.value ? canHrWorkUpdate.value : canHrWorkCreate.value))

const formsCheck = computed(() => {
  if (!isEdit.value || !origForm.value) return false
  const o = origForm.value
  return (
    (form.value.staff ?? null) === (o.staff ?? null) &&
    form.value.company_name === o.company_name &&
    (form.value.department_name ?? '') === (o.department_name ?? '') &&
    (form.value.position_title ?? '') === (o.position_title ?? '') &&
    (form.value.assigned_tasks ?? '') === (o.assigned_tasks ?? '') &&
    form.value.start_date === o.start_date &&
    (form.value.end_date ?? null) === (o.end_date ?? null) &&
    Number(form.value.recognized_ratio ?? 100) === Number(o.recognized_ratio ?? 100) &&
    (form.value.note ?? '') === (o.note ?? '')
  )
})

const openCreateModal = () => {
  if (!canHrWorkCreate.value) return refAlertModal.value?.callModal()
  isEdit.value = false
  origForm.value = null
  validated.value = false
  form.value = {
    pk: undefined,
    company: props.company || undefined,
    staff: props.selectedStaff || allStaffList.value[0]?.pk || null,
    company_name: '',
    department_name: '',
    position_title: '',
    assigned_tasks: '',
    start_date: '',
    end_date: null,
    recognized_ratio: 100,
    note: '',
  }
  refFormModal.value?.callModal()
}

const openEditModal = (item: StaffCareer) => {
  isEdit.value = true
  validated.value = false
  origForm.value = { ...item }
  form.value = { ...item }
  refFormModal.value?.callModal()
}

const onSubmit = (event: Event) => {
  if (
    isValidate(event) ||
    form.value.staff === null ||
    !form.value.company_name ||
    !form.value.start_date
  ) {
    validated.value = true
    return
  }
  if (!canSubmit.value) return refAlertModal.value?.callModal()
  submitting.value = true
  emit('multi-submit', { ...form.value, staff: form.value.staff }, ok => {
    submitting.value = false
    if (ok) refFormModal.value?.close()
  })
}

const deleteObject = () => {
  if (form.value.pk) {
    submitting.value = true
    emit('on-delete', form.value.pk, ok => {
      submitting.value = false
      refDelModal.value?.close()
      if (ok) refFormModal.value?.close()
    })
  }
}

const deleteConfirm = () => {
  if (canHrWorkDelete.value) refDelModal.value?.callModal()
  else refAlertModal.value?.callModal()
}

defineExpose({ openCreateModal })
</script>

<template>
  <CAlert v-if="canHrWorkCreate" :color="AlertSecondary" class="text-end">
    <v-btn color="primary" variant="flat" :disabled="!company" @click="openCreateModal">
      직원 경력 사항 등록
    </v-btn>
  </CAlert>

  <TableTitleRow
    title="직원 경력 이력 목록"
    excel
    :url="excelUrl"
    :filename="excelFilename"
    :disabled="!company"
  />

  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 12%" />
      <col style="width: 16%" />
      <col style="width: 12%" />
      <col style="width: 10%" />
      <col style="width: 18%" />
      <col style="width: 14%" />
      <col style="width: 8%" />
      <col v-if="canHrWorkManage" style="width: 10%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">대상직원</CTableHeaderCell>
        <CTableHeaderCell scope="col">근무처/기관명</CTableHeaderCell>
        <CTableHeaderCell scope="col">부서</CTableHeaderCell>
        <CTableHeaderCell scope="col">직위/직급</CTableHeaderCell>
        <CTableHeaderCell scope="col">담당업무</CTableHeaderCell>
        <CTableHeaderCell scope="col">근무기간</CTableHeaderCell>
        <CTableHeaderCell scope="col">인정률</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="item in staffCareerList" :key="item.pk" class="text-center">
        <CTableDataCell>
          <a href="#" role="button" @click.prevent="openEditModal(item)">{{ item.staff_name }}</a>
        </CTableDataCell>
        <CTableDataCell class="fw-semibold text-start">{{ item.company_name }}</CTableDataCell>
        <CTableDataCell>{{ item.department_name || '-' }}</CTableDataCell>
        <CTableDataCell>{{ item.position_title || '-' }}</CTableDataCell>
        <CTableDataCell class="text-start small">{{ item.assigned_tasks || '-' }}</CTableDataCell>
        <CTableDataCell class="small">
          {{ item.start_date }} ~ {{ item.end_date || '재직' }}
        </CTableDataCell>
        <CTableDataCell>
          <v-chip color="info" variant="flat" size="x-small">{{ item.recognized_ratio }}%</v-chip>
        </CTableDataCell>
        <CTableDataCell v-if="canHrWorkManage">
          <v-btn color="info" variant="flat" size="x-small" @click="openEditModal(item)">확인</v-btn>
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="staffCareerList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 8 : 7" class="text-center text-muted py-4">
          등록된 이전 경력 사항이 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="staffCareersCount > 10"
    :active-page="activePage"
    :limit="8"
    :pages="comStore.staffCareerPages(10)"
    class="mt-3"
    @active-page-change="(p: number) => emit('page-select', p)"
  />

  <FormModal ref="refFormModal" size="lg">
    <template #header>
      {{ isEdit ? '직원 경력 사항 수정' : '직원 경력 사항 등록' }}
    </template>
    <template #default>
      <CForm
        class="needs-validation p-3"
        novalidate
        :validated="validated"
        @submit.prevent="onSubmit"
      >
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">대상 직원</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.staff"
                  :options="getPkStaffs"
                  :disabled="isEdit"
                  required
                  placeholder="대상 직원 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">근무처/기관명</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.company_name" required placeholder="회사/기관명" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">부서/조직명</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.department_name" placeholder="부서명" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">직위/직급</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.position_title" placeholder="직위/직급" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">시작일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.start_date" required placeholder="시작일" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">종료일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.end_date" placeholder="종료일(퇴사일)" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">경력 인정률(%)</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.recognized_ratio"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="인정률"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">비고/퇴사사유</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.note" placeholder="비고" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">담당 업무 요약</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.assigned_tasks" placeholder="담당 주요 직무 요약" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <div class="d-flex justify-content-end gap-2 mt-4">
          <v-btn
            v-if="canSubmit"
            type="submit"
            size="small"
            variant="flat"
            :color="isEdit ? 'success' : 'primary'"
            :disabled="formsCheck || submitting"
          >
            저장
          </v-btn>
          <v-btn
            v-if="isEdit && canHrWorkDelete"
            type="button"
            size="small"
            variant="flat"
            color="warning"
            :disabled="submitting"
            @click="deleteConfirm"
          >
            삭제
          </v-btn>
          <v-btn
            type="button"
            size="small"
            variant="flat"
            color="light"
            @click="refFormModal?.close()"
          >
            닫기
          </v-btn>
        </div>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="refDelModal">
    <template #header>직원 경력 사항 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 경력 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn
        color="warning"
        size="small"
        variant="flat"
        :disabled="submitting"
        @click="deleteObject"
      >
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
