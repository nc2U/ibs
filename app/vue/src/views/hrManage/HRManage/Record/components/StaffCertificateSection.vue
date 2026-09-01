<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { type StaffCertificate } from '@/store/types/company.ts'
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
const staffCertificateList = computed(() => comStore.staffCertificateList)
const staffCertificatesCount = computed(() => comStore.staffCertificatesCount)
const allStaffList = computed(() => comStore.allStaffList)

const getPkStaffs = computed(() =>
  allStaffList.value.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'})`,
  })),
)

const refFormModal = ref()
const refDelModal = ref()
const refAlertModal = ref()

const form = ref<StaffCertificate>({
  pk: undefined,
  company: undefined,
  staff: null as any,
  name: '',
  grade: '',
  cert_number: '',
  issuer: '',
  acquired_date: '',
  expire_date: null,
  has_allowance: false,
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
    name: '',
    grade: '',
    cert_number: '',
    issuer: '',
    acquired_date: '',
    expire_date: null,
    has_allowance: false,
    note: '',
  }
  refFormModal.value.callModal()
}

const openEditModal = (item: StaffCertificate) => {
  isEdit.value = true
  form.value = { ...item }
  refFormModal.value.callModal()
}

const onSubmit = () => {
  if (!form.value.staff || !form.value.name || !form.value.acquired_date) return
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
      직원 자격/면허 등록
    </v-btn>
  </CAlert>

  <TableTitleRow
    title="직원 자격 및 면허 목록"
    excel
    :url="excelUrl"
    :filename="excelFilename"
    :disabled="!company"
  />

  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 12%" />
      <col style="width: 18%" />
      <col style="width: 12%" />
      <col style="width: 16%" />
      <col style="width: 14%" />
      <col style="width: 12%" />
      <col style="width: 8%" />
      <col v-if="canHrWorkManage" style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">대상직원</CTableHeaderCell>
        <CTableHeaderCell scope="col">자격/면허명</CTableHeaderCell>
        <CTableHeaderCell scope="col">등급/급수</CTableHeaderCell>
        <CTableHeaderCell scope="col">자격/등록번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">발급기관</CTableHeaderCell>
        <CTableHeaderCell scope="col">취득일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">수당여부</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="item in staffCertificateList" :key="item.pk" class="text-center">
        <CTableDataCell>
          <a href="javascript:void(0);" @click="openEditModal(item)">{{ item.staff_name }}</a>
        </CTableDataCell>
        <CTableDataCell class="fw-semibold text-left">{{ item.name }}</CTableDataCell>
        <CTableDataCell>{{ item.grade || '-' }}</CTableDataCell>
        <CTableDataCell class="text-muted small">{{ item.cert_number || '-' }}</CTableDataCell>
        <CTableDataCell>{{ item.issuer || '-' }}</CTableDataCell>
        <CTableDataCell class="small">{{ item.acquired_date }}</CTableDataCell>
        <CTableDataCell>
          <CBadge :color="item.has_allowance ? 'success' : 'secondary'">
            {{ item.has_allowance ? '지급' : '미지급' }}
          </CBadge>
        </CTableDataCell>
        <CTableDataCell v-if="canHrWorkManage">
          <v-btn color="info" size="x-small" @click="openEditModal(item)">확인</v-btn>
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="staffCertificateList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 8 : 7" class="text-center text-muted py-4">
          등록된 자격/면허 사항이 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="staffCertificatesCount > 10"
    :active-page="1"
    :limit="8"
    :pages="comStore.staffCertificatePages(10)"
    class="mt-3"
    @active-page-change="(p: number) => emit('page-select', p)"
  />

  <FormModal ref="refFormModal" size="lg">
    <template #header>
      {{ isEdit ? '직원 자격/면허 수정' : '직원 자격/면허 등록' }}
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
              <CFormLabel class="col-sm-4 col-form-label required">자격/면허명</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.name" required placeholder="예: 건설기술인, 공인중개사" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">등급/급수</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.grade" placeholder="예: 특급, 1급, 일반" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">등록/자격번호</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.cert_number" placeholder="자격 등록 번호" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">취득일자</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.acquired_date" required placeholder="취득일자" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">만료/갱신일자</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.expire_date" placeholder="만료일자" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">발급 기관</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.issuer" placeholder="예: 한국건설기술인협회" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">수당 지급</CFormLabel>
              <CCol sm="8" class="pt-1">
                <CFormCheck
                  id="has_allowance"
                  v-model="form.has_allowance"
                  label="자격 수당 지급 대상"
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
          <v-btn type="submit" size="small" :color="isEdit ? 'success' : 'primary'">
            저장
          </v-btn>
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
    <template #header>직원 자격/면허 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 자격/면허 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
