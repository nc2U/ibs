<script lang="ts" setup="">
import { inject, type PropType, ref } from 'vue'
import { cutString, humanizeFileSize } from '@/utils/baseMixins'
import type { ContractFile } from '@/store/types/contract'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  contractFiles: { type: Array as PropType<ContractFile[]>, default: () => [] },
  deleted: { type: Number, default: null },
})

const emit = defineEmits(['file-control'])

const RefDelFile = ref()

const newFile = ref<File | null>(null)

const isDark = inject('isDark')

const editMode = ref(false)
const doneEdit = () => (editMode.value = false)
defineExpose({ doneEdit })
const editFile = ref<number | null>(null)
const cngFile = ref<File | null>(null)

const loadFile = (data: Event, pk = null as null | number) => {
  const el = data.target as HTMLInputElement

  if (el.files && el.files[0]) {
    if (el.id === 'scan-new-file') {
      newFile.value = el.files[0]
      emit('file-control', { newFile: newFile.value })
    } else {
      editFile.value = pk
      cngFile.value = el.files[0]
      emit('file-control', { editFile: editFile.value, cngFile: cngFile.value })
    }
  }
}

const removeFile = (id: string) => {
  const file_form = document.getElementById(id) as HTMLInputElement
  file_form.value = ''
  if (id === 'scan-new-file') {
    newFile.value = null
    emit('file-control', { newFile: null })
  } else {
    editFile.value = null
    cngFile.value = null
    emit('file-control', { editFile: null, cngFile: null })
  }
}

const delFile = ref<number | null>(null)

const delFileConfirm = (pk: number) => {
  delFile.value = pk
  RefDelFile.value.callModal()
}

const delFileSubmit = () => {
  if (props.deleted) {
    emit('file-control', { delFile: '' })
    RefDelFile.value.close()
  } else {
    emit('file-control', { delFile: delFile.value })
    delFile.value = null
    RefDelFile.value.close()
  }
}
</script>

<template>
  <CRow class="my-3 py-2" :class="{ 'bg-light': !isDark }">
    <CFormLabel class="col-sm-2 col-form-label"> 계약서 파일</CFormLabel>
    <CCol sm="10">
      <template v-if="!!contractFiles.length">
        <CRow v-for="file in contractFiles" :key="file.pk" class="mb-2" style="padding-top: 6px">
          <CCol sm="10">
            <v-icon icon="mdi-paperclip" size="sm" color="grey" class="mr-2" />
            <span :class="{ 'text-decoration-line-through': file.pk === deleted }">
              <a :href="file.file" target="_blank">
                {{ cutString(file.file_name, 46) }}
              </a>
            </span>
            <span class="file-desc1 form-text mr-1">
              ({{ humanizeFileSize(file.file_size) }})
            </span>
          </CCol>
          <CCol class="text-right">
            <v-btn
              density="compact"
              icon="mdi-pencil"
              :color="!deleted ? 'success' : 'secondary'"
              size="small"
              :class="{ pointer: !deleted }"
              variant="text"
              :disabled="!!deleted"
              @click="editMode = !editMode"
            />
            <v-btn
              density="compact"
              :icon="!deleted ? 'mdi-delete' : 'mdi-delete-restore'"
              :color="editMode ? 'secondary' : 'grey'"
              size="small"
              class="ml-2"
              variant="text"
              :disabled="editMode"
              @click="delFileConfirm(file.pk)"
            />
          </CCol>

          <CRow>
            <CInputGroup v-if="editMode" class="mt-2">
              <CFormInput id="scan-edit-file" type="file" @change="loadFile($event, file.pk)" />
              <CInputGroupText v-if="editFile">
                <v-icon
                  icon="mdi-trash-can-outline"
                  color="grey"
                  size="16"
                  @click="removeFile('scan-edit-file')"
                />
              </CInputGroupText>
            </CInputGroup>
          </CRow>
        </CRow>
      </template>

      <CInputGroup v-else>
        <CFormInput id="scan-new-file" type="file" @change="loadFile" />
        <CInputGroupText v-if="newFile">
          <v-icon
            icon="mdi-trash-can-outline"
            color="grey"
            size="16"
            @click="removeFile('scan-new-file')"
          />
        </CInputGroupText>
      </CInputGroup>
    </CCol>
  </CRow>

  <ConfirmModal ref="RefDelFile">
    <template #default>
      <span v-if="!deleted">이 파일 삭제를 계속 진행하시겠습니까?</span>
      <span v-else>이 파일 삭제를 취소 하시겠습니까?</span>
    </template>
    <template #footer>
      <v-btn :color="!deleted ? 'warning' : 'success'" @click="delFileSubmit">
        <span v-if="!deleted">삭제</span>
        <span v-else>취소</span>
      </v-btn>
    </template>
  </ConfirmModal>
</template>
