<script lang="ts" setup>
import { computed, inject, type PropType, ref } from 'vue'
import { write_contract } from '@/utils/pageAuth'
import { useContract } from '@/store/pinia/contract'
import { bgLight } from '@/utils/cssMixins.ts'
import type { Contract, Contractor } from '@/store/types/contract'
import AddressForm from '@/views/contracts/List/components/AddressForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
  contractor: { type: Object as PropType<Contractor>, required: true },
  currentAddress: { type: Object as PropType<any>, default: null },
  pastAddresses: { type: Array as PropType<any[]>, default: () => [] },
})

const isDark = inject('isDark')
const contStore = useContract()

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

// 파일 수정 관련
const editingFileId = ref<number | null>(null)
const editFile = ref<File | null>(null)
const isUpdating = ref(false)

// ConfirmModal ref
const confirmModal = ref()
const fileToDelete = ref<number | null>(null)

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

// 파일 수정 모드 토글
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

// 파일 수정 실행
const updateFile = async (filePk: number) => {
  if (!editFile.value) return

  isUpdating.value = true
  try {
    await contStore.updateContractFile(filePk, editFile.value, props.contract?.pk as number)
    editingFileId.value = null
    editFile.value = null
    emit('file-uploaded') // 부모 컴포넌트에 파일 변경 알림
  } catch (error) {
    console.error('파일 수정 실패:', error)
  } finally {
    isUpdating.value = false
  }
}

// 파일 삭제 확인
const confirmDeleteFile = (filePk: number, fileName: string) => {
  fileToDelete.value = filePk
  confirmModal.value?.callModal(
    '계약서 파일 삭제',
    `"${fileName}" 파일을 삭제하시겠습니까?\n삭제된 파일은 복구할 수 없습니다.`,
    'mdi-delete-alert',
    'red-darken-2',
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
const getQualificationColor = (q: '1' | '2' | '3' | '4' | '') => {
  if (!q) return 'secondary'
  return { '1': 'info', '2': 'warning', '3': 'success', '4': 'danger' }[q]
}

// 계약자 상태 텍스트
const getStatusText = (status: '1' | '2' | '3' | '4' | '5' | '') => {
  if (!status) return '-'
  return {
    '1': '청약',
    '2': '계약',
    '3': '해지',
    '4': '승계(매도)',
    '5': '승계(매수)',
  }[status]
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
          <CIcon
            name="cibDiscover"
            :style="'color:' + contract.unit_type_desc.color"
            size="sm"
            class="ml-2 mr-1"
          />
          <span>{{ contract.unit_type_desc.name }}</span>
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
        <CCol :sm="6">
          <strong>활성화 :</strong>
          <CBadge :color="contract.activation ? 'success' : 'secondary'" class="ml-2">
            {{ contract.activation ? '활성' : '비활성' }}
          </CBadge>
        </CCol>
        <CCol :sm="6">
          <strong>공급계약 :</strong>
          <CBadge :color="contract.is_sup_cont ? 'success' : 'secondary'" class="ml-2">
            {{ contract.is_sup_cont ? '완료' : '미완료' }}
          </CBadge>
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
            <CBadge :color="getQualificationColor(contractor.qualification)" class="ml-2">
              {{ contractor.qualifi_display }}
            </CBadge>
          </CCol>
        </CRow>
        <CRow>
          <CCol :sm="6">
            <strong>상태 :</strong>
            <span class="ml-2">{{ getStatusText(contractor.status) }}</span>
          </CCol>
          <CCol :sm="6">
            <strong>청약일 :</strong>
            <span class="ml-2">{{ contractor.reservation_date || '-' }}</span>
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
          <v-btn color="primary" variant="outlined" size="small" @click="refChangeAddr.callModal()">
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
        <h6 class="mb-2">메모</h6>
        <div class="text-grey">{{ contractor.note || '메모가 없습니다.' }}</div>
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
                {{ (file.file_size / 1024).toFixed(2) }} KB
                <span class="mx-1">|</span>
                {{ file.created }}
                <span class="mx-1">|</span>
                {{ file.creator.username }}
              </small>
            </div>
            <div>
              <v-icon
                v-if="write_contract"
                icon="mdi-pencil"
                :color="editingFileId === file.pk ? 'success' : 'warning'"
                size="x-small"
                class="ml-3 pointer"
                @click="toggleEditMode(file.pk)"
              />
              <v-icon
                v-if="write_contract"
                icon="mdi-delete"
                color="grey"
                size="x-small"
                class="ml-1 pointer"
                @click="confirmDeleteFile(file.pk, file.file_name)"
              />
            </div>
          </div>

          <!-- 파일 수정 폼 -->
          <div v-if="editingFileId === file.pk" class="mt-2 p-3 border rounded bg-light">
            <div class="mb-2">
              <strong class="text-warning">파일 수정</strong>
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
            <div class="d-flex gap-2">
              <v-btn
                color="success"
                size="small"
                :disabled="!editFile || isUpdating"
                :loading="isUpdating"
                @click="updateFile(file.pk)"
              >
                {{ isUpdating ? '수정 중...' : '파일 수정' }}
              </v-btn>
              <v-btn
                color="secondary"
                size="small"
                variant="outlined"
                :disabled="isUpdating"
                @click="toggleEditMode(file.pk)"
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
          <CCol :sm="12">
            <v-file-input
              v-model="selectedFile"
              density="compact"
              label="계약서 파일"
              clearable
              :disabled="!write_contract || isUploading"
            />
            <v-btn
              color="primary"
              size="small"
              :disabled="!write_contract || !selectedFile || isUploading"
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
      <v-btn color="error" size="small" @click="deleteFile">
        <v-icon icon="mdi-delete" size="small" class="mr-1" />
        삭제
      </v-btn>
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
