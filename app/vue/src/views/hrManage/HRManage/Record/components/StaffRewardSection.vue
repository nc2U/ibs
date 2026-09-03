<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { type StaffRewardPunishment } from '@/store/types/company.ts'
import { TableSecondary, AlertSecondary } from '@/utils/cssMixins.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import Pagination from '@/components/Pagination'
import TableTitleRow from '@/components/TableTitleRow.vue'

const props = defineProps({
  company: { type: String, default: null },
  excelUrl: { type: String, default: '' },
  excelFilename: { type: String, default: '' },
  selectedStaff: { type: Number, default: null },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'page-select'])

const { can, canGlobal, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkDelete = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_DELETE))
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

const refFormModal = ref()
const refDelModal = ref()
const refAlertModal = ref()

const form = ref<StaffRewardPunishment>({
  pk: undefined,
  company: undefined,
  staff: null as any,
  sort: 'reward',
  type_name: '',
  action_date: '',
  expire_date: null,
  reason: '',
  organization: '',
  note: '',
})

const isEdit = ref(false)

const openCreateModal = () => {
  if (!canHrWorkCreate.value) return refAlertModal.value.callModal()
  isEdit.value = false
  form.value = {
    pk: undefined,
    company: props.company || undefined,
    staff: props.selectedStaff || (allStaffList.value[0]?.pk as number) || (null as any),
    sort: 'reward',
    type_name: '',
    action_date: '',
    expire_date: null,
    reason: '',
    organization: '',
    note: '',
  }
  refFormModal.value.callModal()
}

const openEditModal = (item: StaffRewardPunishment) => {
  isEdit.value = true
  form.value = { ...item }
  refFormModal.value.callModal()
}

const onSubmit = () => {
  if (!form.value.staff || !form.value.type_name || !form.value.action_date || !form.value.reason)
    return
  emit('multi-submit', { ...form.value })
  refFormModal.value.close()
}

const deleteObject = () => {
  if (form.value.pk) {
    emit('on-delete', form.value.pk)
    refDelModal.value.close()
    refFormModal.value.close()
  }
}

const deleteConfirm = () => {
  if (canHrWorkDelete.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

defineExpose({ openCreateModal })
</script>

<template>
  <CAlert v-if="canHrWorkCreate" :color="AlertSecondary" class="text-right">
    <v-btn color="primary" :disabled="!company" @click="openCreateModal">
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
          <a href="javascript:void(0);" @click="openEditModal(item)">{{ item.staff_name }}</a>
        </CTableDataCell>
        <CTableDataCell>
          <CBadge :color="item.sort === 'reward' ? 'success' : 'danger'">
            {{ item.sort_desc || (item.sort === 'reward' ? '포상/표창' : '징계/문책') }}
          </CBadge>
        </CTableDataCell>
        <CTableDataCell class="fw-semibold text-left">{{ item.type_name }}</CTableDataCell>
        <CTableDataCell class="small">{{ item.action_date }}</CTableDataCell>
        <CTableDataCell class="small text-muted">{{ item.expire_date || '-' }}</CTableDataCell>
        <CTableDataCell>{{ item.organization || '-' }}</CTableDataCell>
        <CTableDataCell class="text-left small">{{ item.reason }}</CTableDataCell>
        <CTableDataCell v-if="canHrWorkManage">
          <v-btn color="info" size="x-small" @click="openEditModal(item)">확인</v-btn>
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
    :active-page="1"
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
      <CForm class="p-3" @submit.prevent="onSubmit">
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
          <v-btn type="submit" size="small" :color="isEdit ? 'success' : 'primary'"> 저장 </v-btn>
          <v-btn v-if="isEdit" type="button" size="small" color="warning" @click="deleteConfirm">
            삭제
          </v-btn>
          <v-btn type="button" size="small" color="light" @click="refFormModal.close()" flat>
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
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
