<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { bgLight } from '@/utils/cssMixins'
import { useDocs } from '@/store/pinia/docs'
import type { AFile, DFile } from '@/store/types/docs'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  docs: { type: Number, required: true },
  files: { type: Object as PropType<AFile[]>, default: () => [] },
})

const emit = defineEmits(['file-change', 'file-delete'])

const docStore = useDocs()

// 파일 폼 핸들링 로직
const inputKey = ref(0)
const addFileForm = ref(false)
const descShow = ref(false)

const handleFileChange = (event: Event) => {
  descShow.value = true
  const el = event.target as HTMLInputElement
  if (el.files) newFile.value.file = el.files[0] || null
}

const clearFile = (mode: 'new' | 'edit' | undefined) => {
  inputKey.value += 1 // 키 변경으로 새 <input> 생성
  descShow.value = false
  resetFile(mode)
}

// 파일 생성 로직
const newFile = ref<DFile>({
  docs: null,
  file: null,
  description: '',
})
const newFormSet = () => {
  addFileForm.value = !addFileForm.value
  resetFile('new')
}

const fileUpload = (event: Event) => {
  descShow.value = false
  addFileForm.value = false
  const formData = new FormData()
  formData.append('docs', props.docs.toString())
  formData.append('file', newFile.value.file as Blob)
  formData.append('description', newFile.value.description)
  docStore.createFile(formData)
}

// 파일 변경 로직
const isEditForm = ref<number | null>(null)
const editFile = ref<DFile>({
  pk: undefined,
  docs: null,
  file: null,
  description: '',
})
const resetFile = (mode: 'new' | 'edit' | 'all' = 'all') => {
  if (mode !== 'new') addFileForm.value = false
  if (mode !== 'edit') isEditForm.value = null
  newFile.value.file = null
  newFile.value.description = ''
  editFile.value.pk = undefined
  editFile.value.file = null
  editFile.value.description = ''
}
const editFormSet = (pk: number) => {
  editFile.value.pk = pk
  isEditForm.value = isEditForm.value === pk ? null : pk
  resetFile('edit')
}
const editFileChange = (event: Event) => {
  const el = event.target as HTMLInputElement
  if (el.files) editFile.value.file = el.files[0] || null
}
const fileChange = (pk: number) => {
  isEditForm.value = null
  if (editFile.value.file || editFile.value.description) {
    const formData = new FormData()
    formData.append('docs', props.docs.toString())
    if (editFile.value.file) formData.append('file', editFile.value.file as Blob)
    formData.append('description', editFile.value.description)
    docStore.patchFile(pk, formData)
  }
  resetFile()
}

// 파일 삭제 로직
const refDelFile = ref()
const delFilePk = ref<number | null>(null)
const delFileConfirm = (pk: number) => {
  delFilePk.value = pk
  refDelFile.value.callModal()
}
const fileDelete = () => {
  if (delFilePk.value) {
    docStore.deleteFile(delFilePk.value as number, props.docs as number)
    delFilePk.value = null
    refDelFile.value.close()
  }
}
</script>

<template>
  <CRow class="mb-3">
    <CCol>
      <table>
        <tr v-for="file in files" :key="file.pk as number">
          <td style="vertical-align: top">
            <v-icon icon="mdi-paperclip" size="sm" class="mr-2" />
            <a :href="file.file" target="_blank"> {{ cutString(file.file_name, 60) }} </a>
            <span class="ml-1">({{ humanizeFileSize(file.file_size as number) }})</span>
            <span class="mx-2">
              <a :href="file.file" target="_blank">
                <v-icon icon="mdi-download" size="20" color="secondary" />
                <v-tooltip activator="parent" location="top">다운로드</v-tooltip>
              </a>
            </span>
          </td>
          <td class="px-2">{{ file.description }}</td>
          <td class="text-secondary">
            <span>{{ file.user }}, {{ timeFormat(file.created as string, false, '/') }}</span>
            <span class="ml-2">
              <router-link to="#" @click.prevent="editFormSet(file.pk as number)">
                <v-icon icon="mdi-pencil" size="16" color="secondary" />
                <v-tooltip activator="parent" location="top">변경</v-tooltip>
              </router-link>
            </span>
            <span class="ml-2">
              <router-link to="#" @click.prevent="delFileConfirm(file.pk as number)">
                <v-icon icon="mdi-trash-can-outline" size="16" color="secondary" class="mr-2" />
                <v-tooltip activator="parent" location="top">삭제</v-tooltip>
              </router-link>
            </span>
            <span v-if="isEditForm === file.pk">
              <CRow>
                <CCol xs>
                  <CInputGroup size="sm" style="width: 250px">
                    <CFormInput
                      type="file"
                      :key="inputKey"
                      :aria-describedby="`file-edit-${file.pk}`"
                      @input="editFileChange($event)"
                    />
                    <CInputGroupText
                      :id="`file-edit-${file.pk}`"
                      :color="editFile.file ? 'info' : 'secondary'"
                      @click="clearFile"
                    >
                      취소
                    </CInputGroupText>
                  </CInputGroup>
                </CCol>
                <CCol v-if="editFile.file" xs>
                  <CInputGroup size="sm" style="width: 250px">
                    <CFormInput
                      v-model="editFile.description"
                      placeholder="부가적인 설명"
                      size="sm"
                    />
                    <CInputGroupText>
                      <v-icon icon="mdi-trash-can-outline" size="16" @click="clearFile('edit')" />
                    </CInputGroupText>
                  </CInputGroup>
                </CCol>
                <CCol v-if="editFile.file" xs>
                  <CButton color="success" size="sm" @click="fileChange(file.pk as number)">
                    변경
                  </CButton>
                  <CButton color="light" size="sm" @click="clearFile"> 취소 </CButton>
                </CCol>
              </CRow>
            </span>
          </td>
        </tr>
      </table>
    </CCol>
  </CRow>

  <CRow class="mb-2">
    <CCol>
      <router-link to="#" @click.prevent="newFormSet">파일추가</router-link>
    </CCol>
  </CRow>

  <CRow v-if="addFileForm" class="p-3 mb-3" :class="bgLight">
    <CCol>
      <CInputGroup size="sm">
        <CFormInput type="file" :key="inputKey" size="sm" @input="handleFileChange" />
        <CInputGroupText v-if="newFile.file" @click="clearFile('new')">제거</CInputGroupText>
      </CInputGroup>
    </CCol>

    <CCol>
      <CInputGroup v-if="descShow" size="sm">
        <CFormInput
          v-model="newFile.description"
          @keydown.enter="fileUpload"
          placeholder="부가적인 설명"
        />
        <CInputGroupText>
          <v-icon icon="mdi-trash-can-outline" size="16" @click="clearFile('new')" />
        </CInputGroupText>
      </CInputGroup>
    </CCol>
  </CRow>

  <CRow v-if="addFileForm">
    <CCol>
      <CButton color="success" size="sm" @click="fileUpload">추가</CButton>
      <CButton color="light" size="sm" @click="clearFile">취소</CButton>
    </CCol>
  </CRow>

  <ConfirmModal ref="refDelFile">
    <template #default>이 파일을 삭제 하시겠습니까?</template>
    <template #footer>
      <CButton color="warning" @click="fileDelete">삭제</CButton>
    </template>
  </ConfirmModal>
</template>
