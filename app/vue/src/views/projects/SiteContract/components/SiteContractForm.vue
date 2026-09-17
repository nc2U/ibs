<script lang="ts" setup>
import { ref, reactive, computed, watch, onBeforeMount, type PropType } from 'vue'
import { useStore } from '@/store'
import { isValidate } from '@/utils/helper'
import { humanizeFileSize } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'
import { useSite } from '@/store/pinia/project_site'
import type { SiteContract, SiteOwner } from '@/store/types/project'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  project: { type: Number, default: null },
  contract: { type: Object as PropType<SiteContract>, default: null },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const { can, PERM } = usePerms()
const canSiteCreate = computed(() => can(PERM.SITE_CREATE))
const canSiteUpdate = computed(() => can(PERM.SITE_UPDATE))
const canSiteDelete = computed(() => can(PERM.SITE_DELETE))
const canSiteManage = computed(() => (!props.contract ? canSiteCreate.value : canSiteUpdate.value))

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = reactive<SiteContract>({
  pk: null,
  project: null,
  owner: null,
  contract_date: null,
  total_price: null,
  contract_area: null,
  down_pay1: null,
  down_pay1_date: null,
  down_pay1_is_paid: false,
  down_pay2: null,
  down_pay2_date: null,
  down_pay2_is_paid: false,
  inter_pay1: null,
  inter_pay1_date: null as string | null,
  inter_pay1_is_paid: false,
  inter_pay2: null,
  inter_pay2_date: null as string | null,
  inter_pay2_is_paid: false,
  remain_pay: null,
  remain_pay_date: null,
  remain_pay_is_paid: false,
  ownership_completion: false,
  acc_bank: '',
  acc_number: '',
  acc_owner: '',
  note: '',
  site_cont_files: [],
})

const siteStore = useSite()
const getOwners = computed(() => siteStore.getOwners)

const formsCheck = computed(() => {
  if (props.contract) {
    if (!canSiteUpdate.value) return true
    const a = form.owner === props.contract?.owner
    const b = form.contract_date === props.contract.contract_date
    const c = form.total_price === props.contract.total_price
    const d = form.contract_area === props.contract.contract_area
    const e = form.down_pay1 === props.contract.down_pay1
    const f = form.down_pay1_date === props.contract.down_pay1_date
    const g = form.down_pay1_is_paid === props.contract.down_pay1_is_paid
    const h = form.down_pay2 === props.contract.down_pay2
    const i = form.down_pay2_date === props.contract.down_pay2_date
    const j = form.down_pay2_is_paid === props.contract.down_pay2_is_paid
    const k = form.inter_pay1 === props.contract.inter_pay1
    const l = form.inter_pay1_date === props.contract.inter_pay1_date
    const m = form.inter_pay1_is_paid === props.contract.inter_pay1_is_paid
    const n = form.inter_pay2 === props.contract.inter_pay2
    const o = form.inter_pay2_date === props.contract.inter_pay2_date
    const p = form.inter_pay2_is_paid === props.contract.inter_pay2_is_paid
    const q = form.remain_pay === props.contract.remain_pay
    const r = form.remain_pay_date === props.contract.remain_pay_date
    const s = form.remain_pay_is_paid === props.contract.remain_pay_is_paid
    const t = form.ownership_completion === props.contract.ownership_completion
    const u = form.acc_bank === props.contract.acc_bank
    const v = form.acc_number === props.contract.acc_number
    const w = form.acc_owner === props.contract.acc_owner
    const x = form.note === props.contract.note

    const y = newFiles.value.length === 0
    const b1 = delFiles.value.length === 0

    const sky = a && b && c && d && e && f && g && h && i
    const sea = j && k && l && m && n && o && p && q && r
    const air = s && t && u && v && w && x && y && b1

    return sky && sea && air
  }
  return !canSiteCreate.value
})

const getAreaByOwner = computed(() =>
  !props.contract && siteStore.siteOwner
    ? (siteStore.siteOwner as SiteOwner).sites
        .map(s => Number(s.owned_area || 0))
        .reduce((sum, val) => sum + val, 0)
    : null,
)

watch(
  () => form.owner,
  val => {
    if (!props.contract && val) siteStore.fetchSiteOwner(val)
  },
)

watch(getAreaByOwner, val => (form.contract_area = val))

const appStore = useStore()
const isDark = computed(() => appStore.theme === 'dark')

// 새로 추가할 파일 목록
const newFiles = ref<File[]>([])
// 삭제 대기 중인 기존 파일 PK 목록
const delFiles = ref<number[]>([])

// 파일 인풋 ref 및 제한
const fileInputRef = ref<HTMLInputElement | null>(null)
const fileErrorMessage = ref('')
const maxFileSize = 100 * 1024 * 1024 // 100MB
const maxTotalSize = 200 * 1024 * 1024 // 200MB

// 총 새로 추가된 파일 용량
const totalNewFileSize = computed(() => {
  return newFiles.value.reduce((acc, f) => acc + (f.size || 0), 0)
})

// 파일 추가 핸들러 (복수 파일 선택 지원)
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  fileErrorMessage.value = ''
  if (!target.files || target.files.length === 0) return

  const files = Array.from(target.files)
  for (const file of files) {
    if (file.size > maxFileSize) {
      fileErrorMessage.value = `[${file.name}] 파일 크기가 제한(${humanizeFileSize(maxFileSize)})을 초과합니다.`
      continue
    }
    if (totalNewFileSize.value + file.size > maxTotalSize) {
      fileErrorMessage.value = `총 첨부파일 용량이 제한(${humanizeFileSize(maxTotalSize)})을 초과합니다.`
      break
    }
    const isDuplicate = newFiles.value.some(f => f.name === file.name && f.size === file.size)
    if (!isDuplicate) {
      newFiles.value.push(file)
    }
  }

  target.value = ''
}

// 새로 추가된 파일 목록에서 제거
const removeNewFile = (index: number) => {
  newFiles.value.splice(index, 1)
}

// 기존 파일 삭제/복구 토글
const toggleDeleteExistingFile = (pk: number) => {
  const idx = delFiles.value.indexOf(pk)
  if (idx > -1) {
    delFiles.value.splice(idx, 1)
  } else {
    delFiles.value.push(pk)
  }
}

// 삭제 대기 중 여부 확인
const isMarkedForDeletion = (pk: number) => {
  return delFiles.value.includes(pk)
}

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (canSiteManage.value) multiSubmit({ ...form })
    else refAlertModal.value.callModal()
    validated.value = false
  }
}

const multiSubmit = (payload: SiteContract) => {
  emit('multi-submit', {
    ...payload,
    new_files: newFiles.value,
    del_files: delFiles.value,
  })
  emit('close')
}

const deleteObject = () => {
  emit('on-delete', { pk: props.contract?.pk, project: props.contract?.project })
  refDelModal.value.close()
  emit('close')
}

const deleteConfirm = () => {
  if (canSiteDelete.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const dataSetup = () => {
  if (props.contract) {
    form.pk = props.contract.pk
    form.project = props.contract.project
    form.owner = props.contract.owner
    form.contract_date = props.contract.contract_date
    form.total_price = props.contract.total_price
    form.contract_area = props.contract.contract_area
    form.down_pay1 = props.contract.down_pay1
    form.down_pay1_date = props.contract.down_pay1_date
    form.down_pay1_is_paid = props.contract.down_pay1_is_paid
    form.down_pay2 = props.contract.down_pay2
    form.down_pay2_date = props.contract.down_pay2_date
    form.down_pay2_is_paid = props.contract.down_pay2_is_paid
    form.inter_pay1 = props.contract.inter_pay1
    form.inter_pay1_date = props.contract.inter_pay1_date
    form.inter_pay1_is_paid = props.contract.inter_pay1_is_paid
    form.inter_pay2 = props.contract.inter_pay2
    form.inter_pay2_date = props.contract.inter_pay2_date
    form.inter_pay2_is_paid = props.contract.inter_pay2_is_paid
    form.remain_pay = props.contract.remain_pay
    form.remain_pay_date = props.contract.remain_pay_date
    form.remain_pay_is_paid = props.contract.remain_pay_is_paid
    form.ownership_completion = props.contract.ownership_completion
    form.acc_bank = props.contract.acc_bank
    form.acc_number = props.contract.acc_number
    form.acc_owner = props.contract.acc_owner
    form.note = props.contract.note
    form.site_cont_files = props.contract.site_cont_files
  } else form.project = props.project as number
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">소유자</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model.number="form.owner"
                  :options="getOwners"
                  placeholder="소유자"
                  autocomplete="label"
                  :attrs="form.owner ? {} : { required: true }"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 총 계약면적(㎡)</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.contract_area"
                  type="number"
                  min="0"
                  step="0.0000001"
                  placeholder="총 계약면적(㎡)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required"> 총 매매가격</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.total_price"
                  min="0"
                  type="number"
                  required
                  placeholder="총 매매가격"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required"> 계약 체결일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.contract_date"
                  maxlength="10"
                  placeholder="계약 체결일"
                  required
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required"> 계약금 (1차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.down_pay1"
                    type="number"
                    min="0"
                    required
                    placeholder="계약금 - 1차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="down_pay1_is_paid"
                      v-model="form.down_pay1_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.down_pay1_date"
                  maxlength="10"
                  placeholder="계약금 1차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 계약금 (2차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.down_pay2"
                    type="number"
                    min="0"
                    placeholder="계약금 - 2차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="down_pay2_is_paid"
                      v-model="form.down_pay2_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.down_pay2_date"
                  maxlength="10"
                  placeholder="계약금 2차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 중도금 (1차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.inter_pay1"
                    type="number"
                    min="0"
                    placeholder="중도금 - 1차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="inter_pay1_is_paid"
                      v-model="form.inter_pay1_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.inter_pay1_date"
                  maxlength="10"
                  placeholder="중도금 1차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 중도금 (2차)</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.inter_pay2"
                    type="number"
                    min="0"
                    placeholder="중도금 - 2차"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="inter_pay2_is_paid"
                      v-model="form.inter_pay2_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.inter_pay2_date"
                  maxlength="10"
                  placeholder="중도금 2차 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">잔금</CFormLabel>
              <CCol sm="8">
                <CInputGroup class="mb-3">
                  <CFormInput
                    v-model.number="form.remain_pay"
                    type="number"
                    min="0"
                    required
                    placeholder="계약 잔금"
                  />
                  <CInputGroupText>
                    <CFormCheck
                      id="remain_pay_is_paid"
                      v-model="form.remain_pay_is_paid"
                      type="checkbox"
                      label="지급"
                    />
                  </CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 지급 약정일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.remain_pay_date"
                  maxlength="10"
                  placeholder="잔금 지급일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required"> 입금 은행</CFormLabel>
              <CCol sm="3">
                <CFormInput
                  v-model="form.acc_bank"
                  maxlength="20"
                  required
                  placeholder="입금 은행"
                />
              </CCol>
              <CCol sm="3">
                <CFormInput
                  v-model="form.acc_number"
                  maxlength="25"
                  required
                  placeholder="계좌번호"
                />
              </CCol>
              <CCol sm="2">
                <CFormInput v-model="form.acc_owner" maxlength="20" required placeholder="예금주" />
              </CCol>
              <CCol sm="2" class="pt-2">
                <CFormSwitch
                  id="ownership_completion"
                  v-model="form.ownership_completion"
                  label="소유권 확보"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 특이사항</CFormLabel>
              <CCol sm="10">
                <CFormTextarea v-model="form.note" rows="3" placeholder="특이사항" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3 py-2 px-1 rounded" :class="{ 'bg-light': !isDark, 'bg-dark': isDark }">
          <CFormLabel class="col-sm-2 col-form-label"> 계약서 및 첨부파일 </CFormLabel>
          <CCol sm="10">
            <!-- 파일 선택 영역 -->
            <div class="d-flex align-items-center mb-2">
              <input
                ref="fileInputRef"
                type="file"
                multiple
                class="d-none"
                @change="handleFileSelect"
              />
              <v-btn
                color="primary"
                variant="tonal"
                size="small"
                prepend-icon="mdi-paperclip"
                @click="fileInputRef?.click()"
              >
                파일 선택 (복수 가능)
              </v-btn>
              <span class="text-caption text-grey ml-3">
                토지매매계약서, 인감증명서, 위임장, 등기부등본 등 관련 서류를 복수로 등록할 수
                있습니다.
              </span>
            </div>

            <!-- 파일 에러 메시지 -->
            <div v-if="fileErrorMessage" class="text-danger small mb-2">
              <v-icon icon="mdi-alert-circle" size="14" class="mr-1" />
              {{ fileErrorMessage }}
            </div>

            <!-- 기존 등록된 파일 목록 -->
            <div v-if="form.site_cont_files && form.site_cont_files.length > 0" class="mb-3">
              <div class="text-caption text-medium-emphasis mb-1 font-weight-bold">
                <v-icon icon="mdi-folder-outline" size="14" class="mr-1" />
                등록된 계약서 / 첨부 서류 ({{ form.site_cont_files.length }}개)
              </div>
              <v-list density="compact" class="py-0 border rounded bg-transparent">
                <v-list-item
                  v-for="file in form.site_cont_files"
                  :key="file.pk"
                  class="px-3 py-1"
                  :class="{
                    'text-decoration-line-through text-grey bg-grey-lighten-4': isMarkedForDeletion(
                      file.pk,
                    ),
                  }"
                >
                  <template #prepend>
                    <v-icon
                      :icon="
                        isMarkedForDeletion(file.pk)
                          ? 'mdi-file-remove'
                          : 'mdi-file-document-outline'
                      "
                      :color="isMarkedForDeletion(file.pk) ? 'grey' : 'primary'"
                      size="18"
                      class="mr-2"
                    />
                  </template>

                  <v-list-item-title class="text-body-2">
                    <a
                      v-if="!isMarkedForDeletion(file.pk)"
                      :href="file.file"
                      target="_blank"
                      class="text-decoration-none text-primary font-weight-medium"
                    >
                      {{ file.file_name }}
                    </a>
                    <span v-else>{{ file.file_name }}</span>
                    <span class="text-caption text-grey ml-2">
                      ({{ humanizeFileSize(file.file_size) }})
                    </span>
                    <span v-if="file.creator?.username" class="text-caption text-grey ml-2">
                      · {{ file.creator.username }}
                    </span>
                    <span v-if="file.created" class="text-caption text-grey ml-1">
                      · {{ file.created.substring(0, 10) }}
                    </span>
                    <v-chip
                      v-if="isMarkedForDeletion(file.pk)"
                      color="error"
                      size="x-small"
                      class="ml-2"
                      variant="outlined"
                    >
                      삭제 대기
                    </v-chip>
                  </v-list-item-title>

                  <template #append>
                    <v-btn
                      density="compact"
                      :icon="isMarkedForDeletion(file.pk) ? 'mdi-undo' : 'mdi-delete-outline'"
                      :color="isMarkedForDeletion(file.pk) ? 'info' : 'error'"
                      variant="text"
                      size="small"
                      @click="toggleDeleteExistingFile(file.pk)"
                    >
                      <v-tooltip activator="parent" location="top">
                        {{ isMarkedForDeletion(file.pk) ? '삭제 취소' : '삭제' }}
                      </v-tooltip>
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </div>

            <!-- 새로 추가된 파일 목록 -->
            <div v-if="newFiles.length > 0">
              <div
                class="text-caption text-medium-emphasis mb-1 font-weight-bold d-flex justify-content-between"
              >
                <span>
                  <v-icon icon="mdi-cloud-upload-outline" size="14" class="mr-1" />
                  추가할 파일 ({{ newFiles.length }}개, 총 {{ humanizeFileSize(totalNewFileSize) }})
                </span>
              </div>
              <v-list density="compact" class="py-0 border rounded bg-transparent">
                <v-list-item
                  v-for="(nFile, idx) in newFiles"
                  :key="`${nFile.name}-${idx}`"
                  class="px-3 py-1"
                >
                  <template #prepend>
                    <v-icon icon="mdi-file-plus-outline" color="success" size="18" class="mr-2" />
                  </template>

                  <v-list-item-title class="text-body-2">
                    {{ nFile.name }}
                    <span class="text-caption text-grey ml-2">
                      ({{ humanizeFileSize(nFile.size) }})
                    </span>
                  </v-list-item-title>

                  <template #append>
                    <v-btn
                      density="compact"
                      icon="mdi-close"
                      color="grey"
                      variant="text"
                      size="small"
                      @click="removeNewFile(idx)"
                    >
                      <v-tooltip activator="parent" location="top">제거</v-tooltip>
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </div>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <slot name="footer">
        <v-btn
          type="submit"
          size="small"
          :color="contract ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="contract" size="small" type="button" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header> 부지 매입 계약 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 부지 매입 계약 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
