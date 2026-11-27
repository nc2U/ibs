<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { isValidate } from '@/utils/helper.ts'
import { type StaffRewardPunishment } from '@/store/types/company.ts'
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
  (e: 'multi-submit', payload: StaffRewardPunishment, done?: (ok: boolean) => void): void
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
const staffRewardPunishmentList = computed(() => comStore.staffRewardPunishmentList)
const staffRewardPunishmentsCount = computed(() => comStore.staffRewardPunishmentsCount)
const allStaffList = computed(() => comStore.allStaffList)

const getPkStaffs = computed(() =>
  allStaffList.value.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'})`,
  })),
)

const sorts = [
  { value: 'reward', label: '포상/표창' },
  { value: 'punish', label: '징계/문책' },
]

const refFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

type StaffRewardFormState = Omit<StaffRewardPunishment, 'staff'> & { staff: number | null }

const form = ref<StaffRewardFormState>({
  pk: undefined,
  company: undefined,
  staff: null,
  sort: 'reward',
  type_name: '',
  action_date: '',
  expire_date: null,
  reason: '',
  organization: '',
  note: '',
})

const origForm = ref<StaffRewardPunishment | null>(null)
const isEdit = ref(false)
const validated = ref(false)
const submitting = ref(false)

const canSubmit = computed(() => (isEdit.value ? canHrWorkUpdate.value : canHrWorkCreate.value))

const formsCheck = computed(() => {
  if (!isEdit.value || !origForm.value) return false
  const o = origForm.value
  return (
    (form.value.staff ?? null) === (o.staff ?? null) &&
    form.value.sort === o.sort &&
    form.value.type_name === o.type_name &&
    form.value.action_date === o.action_date &&
    (form.value.expire_date ?? null) === (o.expire_date ?? null) &&
    form.value.reason === o.reason &&
    (form.value.organization ?? '') === (o.organization ?? '') &&
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
    sort: 'reward',
    type_name: '',
    action_date: '',
    expire_date: null,
    reason: '',
    organization: '',
    note: '',
  }
  refFormModal.value?.callModal()
}

const openEditModal = (item: StaffRewardPunishment) => {
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
    !form.value.type_name ||
    !form.value.action_date ||
    !form.value.reason
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
      직원 상벌 내역 등록
    </v-btn>
  </CAlert>

  <TableTitleRow
    title="직원 상벌 이력 목록"
    excel
    :url="excelUrl"
    :filename="excelFilename"
    :disabled="!company"
  />

  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 15%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 14%" />
      <col style="width: 19%" />
      <col v-if="canHrWorkManage" style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">대상직원</CTableHeaderCell>
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">포상/징계 항목명</CTableHeaderCell>
        <CTableHeaderCell scope="col">처분/수여일</CTableHeaderCell>
        <CTableHeaderCell scope="col">효력만료일</CTableHeaderCell>
        <CTableHeaderCell scope="col">수여/처분기관</CTableHeaderCell>
        <CTableHeaderCell scope="col">사유/근거</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="item in staffRewardPunishmentList" :key="item.pk" class="text-center">
        <CTableDataCell>
          <a href="#" role="button" @click.prevent="openEditModal(item)">{{ item.staff_name }}</a>
        </CTableDataCell>
        <CTableDataCell>
          <v-chip
            :color="item.sort === 'reward' ? 'success' : 'error'"
            variant="flat"
            size="x-small"
          >
            {{ item.sort_desc || (item.sort === 'reward' ? '포상/표창' : '징계/문책') }}
          </v-chip>
        </CTableDataCell>
        <CTableDataCell class="fw-semibold text-start">{{ item.type_name }}</CTableDataCell>
        <CTableDataCell class="small">{{ item.action_date }}</CTableDataCell>
        <CTableDataCell class="small text-muted">{{ item.expire_date || '-' }}</CTableDataCell>
        <CTableDataCell>{{ item.organization || '-' }}</CTableDataCell>
        <CTableDataCell class="text-start small">{{ item.reason }}</CTableDataCell>
        <CTableDataCell v-if="canHrWorkManage">
          <v-btn color="info" variant="flat" size="x-small" @click="openEditModal(item)">확인</v-btn>
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="staffRewardPunishmentList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 8 : 7" class="text-center text-muted py-4">
          등록된 상벌 이력이 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="staffRewardPunishmentsCount > 10"
    :active-page="activePage"
    :limit="8"
    :pages="comStore.staffRewardPunishmentPages(10)"
    class="mt-3"
    @active-page-change="(p: number) => emit('page-select', p)"
  />

  <FormModal ref="refFormModal" size="lg">
    <template #header>
      {{ isEdit ? '직원 상벌 이력 수정' : '직원 상벌 이력 등록' }}
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
              <CFormLabel class="col-sm-4 col-form-label required">구분</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.sort"
                  :options="sorts"
                  required
                  placeholder="상벌 구분"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">포상/징계명</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.type_name"
                  required
                  placeholder="예: 우수사원상, 표창, 견책, 감봉"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">처분/수여일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.action_date" required placeholder="수여/처분일자" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">효력 만료일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.expire_date" placeholder="징계 효력 만료일" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">수여/처분기관</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.organization" placeholder="예: 대표이사, 인사위원회" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">사유 / 근거</CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.reason"
                  rows="3"
                  required
                  placeholder="구체적인 공적 내용 또는 징계 사유/근거"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.note" placeholder="비고 및 관리 메모" />
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
    <template #header>직원 상벌 이력 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 상벌 이력을 삭제하시겠습니까?
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
