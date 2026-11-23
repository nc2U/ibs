<script lang="ts" setup>
import { computed, reactive, ref } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { useContract } from '@/store/pinia/contract'
import { bgLight } from '@/utils/cssMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { message } from '@/utils/helper'
import { timeFormat } from '@/utils/baseMixins.ts'
import type {
  Contract,
  Contractor,
  ContractorAddress,
  ContractorRevealResult,
} from '@/store/types/contract'
import AddressForm from '@/views/contracts/List/components/AddressForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = withDefaults(
  defineProps<{
    contract: Contract
    contractor: Contractor
    currentAddress?: ContractorAddress | null
    pastAddresses?: ContractorAddress[]
  }>(),
  {
    currentAddress: null,
    pastAddresses: () => [],
  },
)

const { can, PERM } = usePerms()
const canContractUpdate = computed(() => can(PERM.CONTRACT_UPDATE))

const store = useStore()
const isDark = computed(() => store.theme === 'dark')
const accountStore = useAccount()
const isWorkManager = computed(() => !!accountStore.workManager)
const contStore = useContract()

// 주민등록번호 등록/갱신/파기 및 열람 모달 상태
const refRrnEditModal = ref<InstanceType<typeof FormModal> | null>(null)
const refRrnRevealModal = ref<InstanceType<typeof FormModal> | null>(null)
const refRrnPurgeConfirm = ref<InstanceType<typeof ConfirmModal> | null>(null)
const rrnForm = reactive({
  rrn: '',
  legal_basis: '1' as '1' | '2' | '3',
  purpose: '계약자 식별정보 등록/갱신',
})
const isSavingRrn = ref(false)
const revealPurpose = ref('')
const isRevealingRrn = ref(false)
const revealedResult = ref<ContractorRevealResult | null>(null)

const canCollectContractorRrn = computed(() => props.contractor.status !== '1')

const openRrnEditModal = () => {
  rrnForm.rrn = ''
  rrnForm.legal_basis = (props.contractor.rrn_legal_basis as '1' | '2' | '3') || '1'
  rrnForm.purpose = '계약자 식별정보 등록/갱신'
  refRrnEditModal.value?.callModal()
}

const submitRrnEdit = async () => {
  if (!props.contractor?.pk || !rrnForm.rrn.trim()) return
  isSavingRrn.value = true
  try {
    await contStore.upsertContractorSensitiveInfo(props.contractor.pk, {
      rrn: rrnForm.rrn,
      legal_basis: rrnForm.legal_basis,
      purpose: rrnForm.purpose,
    })
    emit('file-uploaded')
    refRrnEditModal.value?.close()
  } finally {
    rrnForm.rrn = ''
    isSavingRrn.value = false
  }
}

const requestRrnPurge = () => {
  refRrnPurgeConfirm.value?.callModal(
    '주민등록번호 파기',
    `${props.contractor.name} 계약자의 암호화된 주민등록번호를 즉시 파기하시겠습니까? (파기 이력은 감사 로그에 보존됩니다)`,
    'mdi-shield-remove',
    'warning',
  )
}

const confirmRrnPurge = async () => {
  if (!props.contractor?.pk) return
  await contStore.purgeContractorSensitiveInfo(props.contractor.pk, '관리 화면에서 수동 파기')
  refRrnPurgeConfirm.value?.close()
  refRrnEditModal.value?.close()
  emit('file-uploaded')
}

const openRrnRevealModal = () => {
  revealPurpose.value = ''
  revealedResult.value = null
  refRrnRevealModal.value?.callModal()
}

const clearRevealedRrn = () => {
  revealedResult.value = null
  revealPurpose.value = ''
}

const submitRevealRrn = async () => {
  if (!props.contractor?.pk || !revealPurpose.value.trim()) return
  isRevealingRrn.value = true
  try {
    revealedResult.value = await contStore.revealContractorRrn(
      props.contractor.pk,
      revealPurpose.value.trim(),
    )
  } finally {
    isRevealingRrn.value = false
  }
}

const copyRevealedRrn = async () => {
  if (!revealedResult.value?.rrn || typeof navigator === 'undefined' || !navigator.clipboard) return
  await navigator.clipboard.writeText(revealedResult.value.rrn)
  message('info', '알림', '주민등록번호가 클립보드에 복사되었습니다.')
}

// 과거 주소 히스토리 표시 토글
const showPastAddresses = ref(false)

// 주소 탭 선택 (id: 주민등록 주소, dm: 우편물 수령 주소)
const selectedAddressTab = ref('id')

const refChangeAddr = ref() // 주소변경 모달
const address = computed(() => props.contract?.contractor?.contractoraddress)

// 파일 업로드 관련
const emit = defineEmits(['file-uploaded'])
const selectedFile = ref<File | null>(null)
const isUploading = ref(false)

// 파일 변경 관련
const editingFileId = ref<number | null>(null)
const editFile = ref<File | null>(null)
const isUpdating = ref(false)

// ConfirmModal ref
const confirmModal = ref()
const fileToDelete = ref<number | null>(null)

// 메모 인라인 수정 관련
const isEditingNote = ref(false)
const noteText = ref('')
const isSavingNote = ref(false)

const enableEditNote = () => {
  if (!canContractUpdate.value) return // 권한 검사
  noteText.value = props.contractor.note || ''
  isEditingNote.value = true
}

const cancelEditNote = () => {
  isEditingNote.value = false
  noteText.value = ''
}

const updateNote = async () => {
  if (!props.contractor?.pk) return
  isSavingNote.value = true
  try {
    await contStore.patchContractor(props.contractor.pk, { note: noteText.value })
    isEditingNote.value = false
    emit('file-uploaded') // 부모 컴포넌트 데이터 갱신 유도 (동일한 갱신 흐름 재활용)
  } catch (error) {
    console.error('메모 수정 실패:', error)
  } finally {
    isSavingNote.value = false
  }
}

// 파일 업로드 실행
const uploadFile = async () => {
  if (!selectedFile.value || !props.contractor?.pk) return

  isUploading.value = true
  try {
    await contStore.createContractFile(
      props.contractor.pk,
      selectedFile.value,
      props.contract?.pk as number,
    )
    selectedFile.value = null
    emit('file-uploaded') // 부모 컴포넌트에 업로드 완료 알림
  } catch (error) {
    console.error('파일 업로드 실패:', error)
  } finally {
    isUploading.value = false
  }
}

// 파일 변경 모드 토글
const toggleEditMode = (filePk: number) => {
  if (editingFileId.value === filePk) {
    // 이미 수정 모드인 경우 취소
    editingFileId.value = null
    editFile.value = null
  } else {
    // 새로운 파일을 수정 모드로 설정
    editingFileId.value = filePk
    editFile.value = null
  }
}

// 파일 변경 실행
const updateFile = async (filePk: number) => {
  if (!editFile.value) return

  isUpdating.value = true
  try {
    await contStore.updateContractFile(filePk, editFile.value, props.contract?.pk as number)
    editingFileId.value = null
    editFile.value = null
    emit('file-uploaded') // 부모 컴포넌트에 파일 변경 알림
  } catch (error) {
    console.error('파일 변경 실패:', error)
  } finally {
    isUpdating.value = false
  }
}

// 파일 삭제 확인
const confirmDeleteFile = (filePk: number, fileName: string) => {
  fileToDelete.value = filePk
  confirmModal.value?.callModal(
    '계약서 파일 삭제',
    `"${fileName}" 파일을 삭제하시겠습니까?`,
    'mdi-delete-alert',
    'danger',
  )
}

// 파일 삭제 실행
const deleteFile = async () => {
  if (!fileToDelete.value) return

  try {
    await contStore.removeContractFile(fileToDelete.value, props.contract?.pk as number)
    emit('file-uploaded') // 부모 컴포넌트에 파일 변경 알림
    confirmModal.value?.close()
  } catch (error) {
    console.error('파일 삭제 실패:', error)
  } finally {
    fileToDelete.value = null
  }
}

// 자격구분 색상
const getQualificationColor = (q: '1' | '2' | '3' | '') => {
  if (!q) return 'secondary'
  return { '1': 'info', '2': 'warning', '3': 'success' }[q]
}
</script>

<template>
  <!-- 계약 기본 정보 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>계약 기본 정보</strong>
    </CCardHeader>
    <CCardBody>
      <CRow class="mb-2">
        <CCol :sm="6">
          <strong>계약번호 :</strong>
          <span class="ml-2">{{ contract.serial_number }}</span>
        </CCol>
        <CCol :sm="6">
          <strong>분양차수 :</strong>
          <span class="ml-2">{{ contract.order_group_desc.name }}</span>
        </CCol>
      </CRow>
      <CRow class="mb-2">
        <CCol :sm="6">
          <strong>타입 :</strong>
          <template v-if="contract.unit_type_desc">
            <CIcon
              name="cibDiscover"
              :style="'color:' + contract.unit_type_desc.color"
              size="sm"
              class="ml-2 mr-1"
            />
            <span>{{ contract.unit_type_desc.name }}</span>
          </template>
          <span v-else class="ml-2 text-medium-emphasis">미정</span>
        </CCol>
        <CCol :sm="6">
          <strong>호수 :</strong>
          <span class="ml-2" :class="contract.key_unit?.houseunit ? 'text-success' : 'text-danger'">
            {{ contract.key_unit?.houseunit?.__str__ || '미정' }}
          </span>
        </CCol>
      </CRow>
      <CRow class="mb-2">
        <CCol :sm="6">
          <strong>계약일 :</strong>
          <span class="ml-2">{{ contractor.contract_date || '-' }}</span>
        </CCol>
        <CCol :sm="6">
          <strong>공급계약일 :</strong>
          <span class="ml-2">{{ contract.sup_cont_date || '-' }}</span>
        </CCol>
      </CRow>
      <CRow>
        <CCol :sm="4">
          <strong>활성화 :</strong>
          <v-chip
            :color="contract.is_active ? 'success' : 'secondary'"
            variant="flat"
            size="x-small"
            class="ml-2"
          >
            {{ contract.is_active ? '활성' : '비활성' }}
          </v-chip>
        </CCol>
        <CCol :sm="4">
          <strong>공급계약 :</strong>
          <v-chip
            :color="contract.is_sup_cont ? 'success' : 'secondary'"
            variant="flat"
            size="x-small"
            class="ml-2"
          >
            {{ contract.is_sup_cont ? '완료' : '미완료' }}
          </v-chip>
        </CCol>
        <CCol :sm="4">
          <strong>계약종결 :</strong>
          <v-chip
            :color="contract.is_completed ? 'success' : 'info'"
            variant="flat"
            size="x-small"
            class="ml-2"
          >
            {{ contract.is_completed ? '종결' : '진행중' }}
          </v-chip>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>

  <!-- 계약자 상세 정보 카드 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>계약자 상세 정보</strong>
    </CCardHeader>
    <CCardBody>
      <!-- 기본 정보 -->
      <div class="mb-3 pb-3 border-bottom">
        <h6 class="mb-2">기본 정보</h6>
        <CRow class="mb-2">
          <CCol :sm="6">
            <strong>이름 :</strong>
            <span class="ml-2 text-info strong">{{ contractor.name }}</span>
          </CCol>
          <CCol :sm="6">
            <strong>생년월일 :</strong>
            <span class="ml-2">{{ contractor.birth_date }}</span>
          </CCol>
        </CRow>
        <CRow class="mb-2">
          <CCol :sm="6">
            <strong>성별 :</strong>
            <span class="ml-2">{{ contractor.gender === 'M' ? '남성' : '여성' }}</span>
          </CCol>
          <CCol :sm="6">
            <strong>자격구분 :</strong>
            <v-chip
              :color="getQualificationColor(contractor.qualification)"
              variant="flat"
              size="x-small"
              class="ml-2"
            >
              {{ contractor.qualifi_display }}
            </v-chip>
          </CCol>
        </CRow>
        <CRow class="mb-2">
          <CCol :sm="6">
            <strong>상태 :</strong>
            <span
              class="ms-2 strong"
              :class="contractor.status !== '1' ? 'text-muted underline' : 'text-primary'"
            >
              {{ contractor.status_display }}
            </span>
            <v-chip
              v-if="contractor.change_type"
              color="danger"
              variant="flat"
              size="x-small"
              class="ms-2"
            >
              {{ contractor.change_type_display }}
            </v-chip>
          </CCol>
          <CCol :sm="6">
            <strong>청약일 :</strong>
            <span class="ms-2">{{ contractor.reservation_date || '-' }}</span>
          </CCol>
        </CRow>
        <CRow v-if="canCollectContractorRrn || contractor.has_rrn" class="align-items-center">
          <CCol :sm="12" class="d-flex flex-wrap align-items-center gap-2">
            <strong>주민등록번호 :</strong>
            <span v-if="contractor.has_rrn" class="font-monospace">
              {{ contractor.rrn_masked }}
            </span>
            <span v-else class="text-medium-emphasis">미등록</span>
            <v-chip
              v-if="contractor.has_rrn"
              color="success"
              variant="tonal"
              size="x-small"
              prepend-icon="mdi-shield-lock-outline"
            >
              암호화 보관
            </v-chip>
            <v-btn
              v-if="canContractUpdate && canCollectContractorRrn"
              size="x-small"
              color="primary"
              variant="tonal"
              @click="openRrnEditModal"
            >
              {{ contractor.has_rrn ? '변경 / 파기' : '등록' }}
            </v-btn>
            <v-btn
              v-if="isWorkManager && contractor.has_rrn"
              size="x-small"
              color="warning"
              variant="tonal"
              prepend-icon="mdi-eye-outline"
              @click="openRrnRevealModal"
            >
              전체 열람
            </v-btn>
          </CCol>
        </CRow>
      </div>

      <!-- 연락처 정보 -->
      <div v-if="contract.contractor?.contractorcontact" class="mb-3 pb-3 border-bottom">
        <h6 class="mb-2">연락처</h6>
        <CRow class="mb-2">
          <CCol :sm="6">
            <strong>휴대폰 :</strong>
            <span class="ml-2">
              {{ contract.contractor?.contractorcontact.cell_phone || '-' }}
            </span>
          </CCol>
          <CCol :sm="6">
            <strong>집전화 :</strong>
            <span class="ml-2">
              {{ contract.contractor?.contractorcontact.home_phone || '-' }}
            </span>
          </CCol>
        </CRow>
        <CRow class="mb-2">
          <CCol :sm="6">
            <strong>기타전화 :</strong>
            <span class="ml-2">
              {{ contract.contractor?.contractorcontact.other_phone || '-' }}
            </span>
          </CCol>
          <CCol :sm="6">
            <strong>이메일 :</strong>
            <span class="ml-2">
              {{ contract.contractor?.contractorcontact.email || '-' }}
            </span>
          </CCol>
        </CRow>
      </div>

      <!-- 주소 정보 -->
      <div v-if="currentAddress || contract.contractor?.contractoraddress" class="mb-3">
        <div class="d-flex justify-content-between align-items-center">
          <v-btn-toggle v-model="selectedAddressTab" mandatory density="compact" rounded="0">
            <v-btn value="id" size="small">
              <v-icon icon="mdi-home" size="small" class="mr-1" />
              주민등록 주소
            </v-btn>
            <v-btn value="dm" size="small">
              <v-icon icon="mdi-email" size="small" class="mr-1" />
              우편물 수령 주소
            </v-btn>
          </v-btn-toggle>
          <v-btn
            v-if="canContractUpdate"
            color="primary"
            variant="outlined"
            size="small"
            @click="refChangeAddr.callModal()"
          >
            주소변경 등록
          </v-btn>
        </div>

        <!-- 주소 컨텐츠 영역 (트랜지션 적용) -->
        <transition name="slide-fade" mode="out-in">
          <!-- 주민등록 주소 -->
          <div v-if="selectedAddressTab === 'id'" key="id-address" class="p-3 border mt-0">
            <div
              v-if="
                (currentAddress && currentAddress.id_address1) ||
                contract.contractor?.contractoraddress?.id_address1
              "
            >
              <div>
                ({{
                  currentAddress?.id_zipcode || contract.contractor?.contractoraddress?.id_zipcode
                }})
                {{
                  currentAddress?.id_address1 || contract.contractor?.contractoraddress?.id_address1
                }}
              </div>
              <div>
                {{
                  currentAddress?.id_address2 || contract.contractor?.contractoraddress?.id_address2
                }}
                {{
                  currentAddress?.id_address3 || contract.contractor?.contractoraddress?.id_address3
                }}
              </div>
            </div>
            <div v-else class="text-grey">주민등록 주소 정보가 없습니다.</div>
          </div>

          <!-- 우편물 수령 주소 -->
          <div
            v-else-if="selectedAddressTab === 'dm'"
            key="dm-address"
            class="p-3 border mt-0 bg-yellow-lighten-5"
          >
            <div
              v-if="
                (currentAddress && currentAddress.dm_address1) ||
                contract.contractor?.contractoraddress?.dm_address1
              "
            >
              <div>
                ({{
                  currentAddress?.dm_zipcode || contract.contractor?.contractoraddress?.dm_zipcode
                }})
                {{
                  currentAddress?.dm_address1 || contract.contractor?.contractoraddress?.dm_address1
                }}
              </div>
              <div>
                {{
                  currentAddress?.dm_address2 || contract.contractor?.contractoraddress?.dm_address2
                }}
                {{
                  currentAddress?.dm_address3 || contract.contractor?.contractoraddress?.dm_address3
                }}
              </div>
            </div>
            <div v-else class="text-grey">우편물 수령 주소 정보가 없습니다.</div>
          </div>
        </transition>
      </div>

      <!-- 과거 주소 히스토리 -->
      <div class="mb-3 pb-3 border-bottom">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6 class="mb-0">과거 주소 내역</h6>
          <v-btn size="x-small" variant="outlined" @click="showPastAddresses = !showPastAddresses">
            <v-icon :icon="showPastAddresses ? 'mdi-chevron-up' : 'mdi-chevron-down'" />
            {{ showPastAddresses ? '숨기기' : '보기' }}
          </v-btn>
        </div>

        <div v-if="showPastAddresses" class="mt-3">
          <div v-if="pastAddresses.length > 0">
            <div
              v-for="(address, index) in pastAddresses"
              :key="address.pk"
              class="mb-3 p-2 border rounded"
              :class="isDark ? '' : 'bg-light'"
            >
              <div class="d-flex justify-content-between align-items-start mb-2">
                <strong class="text-primary">변경 #{{ pastAddresses.length - index }}</strong>
                <small class="text-grey">{{ address.created }}</small>
              </div>

              <div v-if="address.id_address1" class="mb-2">
                <div class="text-grey small">주민등록 주소</div>
                <div>({{ address.id_zipcode }}) {{ address.id_address1 }}</div>
                <div>{{ address.id_address2 }} {{ address.id_address3 }}</div>
              </div>

              <div v-if="address.dm_address1">
                <div class="text-grey small">우편물 수령 주소</div>
                <div>({{ address.dm_zipcode }}) {{ address.dm_address1 }}</div>
                <div>{{ address.dm_address2 }} {{ address.dm_address3 }}</div>
              </div>
            </div>
          </div>
          <div v-else class="text-center text-grey py-3">
            <v-icon icon="mdi-history" size="large" class="mb-2" />
            <div>과거 주소 히스토리가 없습니다.</div>
          </div>
        </div>
      </div>

      <!-- 메모 -->
      <div>
        <h6 class="mb-2">
          메모
          <span v-if="canContractUpdate" class="text-caption text-grey ml-1">
            (더블클릭하여 수정)
          </span>
        </h6>

        <div v-if="!isEditingNote" @dblclick="enableEditNote" class="pointer-cursor-container">
          <div
            class="text-muted p-2 border rounded border-dashed"
            style="min-height: 48px; cursor: pointer"
          >
            {{ contractor.note || '메모가 없습니다.' }}
          </div>
        </div>

        <div v-else class="mt-2">
          <v-textarea
            v-model="noteText"
            density="compact"
            rows="3"
            label="계약자 관련 메모"
            variant="outlined"
            hide-details
            :disabled="isSavingNote"
            class="mb-2 bg-transparent"
          />
          <div class="text-right">
            <v-btn
              color="success"
              size="small"
              :disabled="isSavingNote"
              :loading="isSavingNote"
              @click="updateNote"
            >
              저장
            </v-btn>
            <v-btn color="light" size="small" :disabled="isSavingNote" @click="cancelEditNote" flat>
              취소
            </v-btn>
          </div>
        </div>
      </div>
    </CCardBody>
  </CCard>

  <!-- 계약서 파일 관리 -->
  <CCard class="mb-3">
    <CCardHeader>
      <strong>계약서 파일</strong>
    </CCardHeader>
    <CCardBody>
      <div v-if="contract.contract_files && contract.contract_files.length > 0">
        <div v-for="file in contract.contract_files" :key="file.pk" class="mb-3">
          <div class="d-flex justify-content-between align-items-center p-2 border rounded">
            <div class="flex-grow-1">
              <div>
                <v-icon icon="mdi-file-document" size="small" class="mr-1" />
                <strong class="mr-2">{{ file.file_name }}</strong>
                <a :href="file.file" target="_blank" class="text-decoration-none">
                  <v-icon icon="mdi-download" color="primary" />
                </a>
              </div>
              <small class="text-grey">
                {{ ((file.file_size || 0) / 1024).toFixed(2) }} KB
                <span class="mx-1">|</span>
                {{ timeFormat(file.created) }}
                <span class="mx-1">|</span>
                {{ file.creator?.username || '미지정' }}
              </small>
            </div>
            <div>
              <v-icon
                v-if="canContractUpdate"
                icon="mdi-pencil"
                :color="editingFileId === file.pk ? 'warning' : 'success'"
                size="x-small"
                class="ml-3 pointer"
                @click="toggleEditMode(file.pk)"
              />
              <v-icon
                v-if="canContractUpdate"
                icon="mdi-delete"
                color="grey"
                size="x-small"
                class="ml-1 pointer"
                @click="confirmDeleteFile(file.pk, file.file_name)"
              />
            </div>
          </div>

          <!-- 파일 변경 폼 -->
          <div v-if="editingFileId === file.pk" class="mt-2 p-3 border rounded bg-more-light">
            <div class="mb-2">
              <strong class="text-primary">파일 변경</strong>
              <small class="text-grey ml-2">새 파일을 선택하여 기존 파일을 교체합니다.</small>
            </div>
            <v-file-input
              v-model="editFile"
              density="compact"
              label="새 파일 선택"
              clearable
              :disabled="isUpdating"
              class="mb-2"
            />
            <div class="text-right">
              <v-btn
                color="success"
                size="small"
                :disabled="!editFile || isUpdating"
                :loading="isUpdating"
                @click="updateFile(file.pk)"
              >
                {{ isUpdating ? '변경 중...' : '파일변경' }}
              </v-btn>
              <v-btn
                color="light"
                size="small"
                :disabled="isUpdating"
                @click="toggleEditMode(file.pk)"
                flat
              >
                취소
              </v-btn>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-grey">
        <CRow>
          <CCol class="p-3 text-center text-grey" :class="bgLight"> 등록된 파일이 없습니다. </CCol>
        </CRow>

        <CRow class="text-right mt-3">
          <CCol v-if="canContractUpdate" :sm="12">
            <v-file-input
              v-model="selectedFile"
              density="compact"
              label="계약서 파일"
              clearable
              :disabled="isUploading"
            />
            <v-btn
              color="primary"
              size="small"
              :disabled="!selectedFile || isUploading"
              :loading="isUploading"
              @click="uploadFile"
            >
              {{ isUploading ? '업로드 중...' : '파일 업로드' }}
            </v-btn>
          </CCol>
        </CRow>
      </div>
    </CCardBody>
  </CCard>

  <FormModal ref="refChangeAddr" size="xl">
    <template #header>주소변경 등록</template>
    <template #default>
      <AddressForm
        :contractor="contractor?.pk as number"
        :address="address"
        @close="refChangeAddr.close()"
      />
    </template>
  </FormModal>

  <ConfirmModal ref="confirmModal">
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteFile">
        <v-icon icon="mdi-delete" size="small" class="me-1" />
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <!-- 주민등록번호 등록/변경 모달 (담당자 Write-Only) -->
  <FormModal ref="refRrnEditModal" @close="rrnForm.rrn = ''">
    <template #icon>
      <v-icon icon="mdi-shield-lock-outline" size="small" color="primary" class="me-2" />
    </template>
    <template #header>계약자 주민등록번호 {{ contractor.has_rrn ? '변경' : '등록' }}</template>
    <template #default>
      <CForm @submit.prevent="submitRrnEdit">
        <CModalBody class="text-body">
          <div class="mb-3">
            <CFormLabel class="required">주민등록번호 (새 번호 입력)</CFormLabel>
            <input
              v-model="rrnForm.rrn"
              v-maska
              data-maska="######-#######"
              class="form-control"
              maxlength="14"
              autocomplete="off"
              required
              :placeholder="
                contractor.has_rrn
                  ? `기존: ${contractor.rrn_masked} (재입력 시 덮어쓰기)`
                  : '000000-0000000'
              "
            />
            <div class="form-text text-muted">
              보안을 위해 기존 번호는 조회되지 않으며, 저장 즉시 암호화 및 마스킹 처리됩니다.
            </div>
          </div>
          <div class="mb-3">
            <CFormLabel>수집 법적 근거</CFormLabel>
            <CFormSelect v-model="rrnForm.legal_basis">
              <option value="1">조합설립·변경인가 제출 (주택법)</option>
              <option value="2">부동산 거래신고 (부동산거래신고법)</option>
              <option value="3">세무신고·환불지급 (소득세법 등)</option>
            </CFormSelect>
          </div>
          <div>
            <CFormLabel>처리 사유</CFormLabel>
            <CFormInput v-model="rrnForm.purpose" maxlength="150" placeholder="등록/변경 사유" />
          </div>
        </CModalBody>
        <CModalFooter>
          <v-btn
            v-if="contractor.has_rrn"
            color="error"
            variant="tonal"
            size="small"
            class="me-auto"
            @click="requestRrnPurge"
          >
            즉시 파기
          </v-btn>
          <v-btn
            color="primary"
            size="small"
            type="submit"
            :disabled="!rrnForm.rrn.trim() || isSavingRrn"
            :loading="isSavingRrn"
          >
            암호화 저장
          </v-btn>
          <v-btn color="light" size="small" flat @click="refRrnEditModal?.close()">닫기</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <!-- 주민등록번호 전체 열람 모달 (슈퍼유저 / 업무관리자 전용) -->
  <FormModal ref="refRrnRevealModal" @close="clearRevealedRrn">
    <template #icon>
      <v-icon icon="mdi-shield-key-outline" size="small" color="warning" class="me-2" />
    </template>
    <template #header>주민등록번호 전체 열람 (책임자 전용)</template>
    <template #default>
      <CForm @submit.prevent="submitRevealRrn">
        <CModalBody class="text-body">
          <CAlert color="warning" class="py-2 text-xs">
            열람 내역(사용자·일시·IP·열람 사유)은 개인정보보호법 안전성 확보조치에 따라 감사 로그에
            영구 기록됩니다.
          </CAlert>

          <div v-if="!revealedResult" class="mb-2">
            <CFormLabel class="required">열람 사유</CFormLabel>
            <CFormInput
              v-model="revealPurpose"
              maxlength="150"
              required
              placeholder="예: 조합설립 변경인가 명부 대조 확인"
            />
          </div>

          <div v-else class="p-3 rounded border text-center">
            <div class="text-xs text-medium-emphasis mb-1">
              {{ contractor.name }} ({{ revealedResult.legal_basis_display }})
            </div>
            <div class="fs-5 fw-bold font-monospace mb-2">
              {{ revealedResult.rrn }}
            </div>
            <v-btn
              size="x-small"
              color="secondary"
              variant="tonal"
              prepend-icon="mdi-content-copy"
              @click="copyRevealedRrn"
            >
              복사
            </v-btn>
          </div>
        </CModalBody>
        <CModalFooter>
          <v-btn
            v-if="!revealedResult"
            color="warning"
            size="small"
            type="submit"
            :disabled="!revealPurpose.trim() || isRevealingRrn"
            :loading="isRevealingRrn"
          >
            감사로그 기록 후 열람
          </v-btn>
          <v-btn color="light" size="small" flat @click="refRrnRevealModal?.close()">닫기</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="refRrnPurgeConfirm">
    <template #footer>
      <v-btn color="error" size="small" @click="confirmRrnPurge">파기 확인</v-btn>
    </template>
  </ConfirmModal>
</template>

<style scoped>
/* 주소 슬라이드 트랜지션 */
.slide-fade-enter-active {
  transition: all 0.4s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.15s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(15px);
  opacity: 0;
}
</style>
