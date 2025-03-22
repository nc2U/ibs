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

const newFile = ref<DFile>({
  docs: null,
  file: null,
  description: '',
})

const docStore = useDocs()

const RefDelFile = ref()
const isEdit = ref(false)

const addFileForm = ref(false)
const inputKey = ref(0)
const descShow = ref(false)

const handleFileChange = (event: Event) => {
  descShow.value = true
  const el = event.target as HTMLInputElement
  if (el.files) newFile.value.file = el.files[0] || null
}

const clearFile = () => {
  inputKey.value += 1 // 키 변경으로 새 <input> 생성
  descShow.value = false
  newFile.value.file = null
  newFile.value.description = ''
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

const fileChange = (event: Event, pk: number) => {
  // form.value.file.del = false
  // form.value.file.edit = !form.value.file.edit

  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-change', { pk, file })
  }
}

const delFileConfirm = () => RefDelFile.value.callModal()

const fileDelete = (payload: FormData) => alert('준비중입니다!') // del_file 전달 파일 삭제 patch 실행
// const fileDelete = () => {
//   const form = new FormData()
//   form.append('del_file', JSON.stringify(props.file.pk as number))
//   emit('file-delete', form)
//   RefDelFile.value.close()
// }
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
              <router-link to="#" @click.prevent="isEdit = !isEdit">
                <v-icon icon="mdi-pencil" size="16" color="secondary" />
                <v-tooltip activator="parent" location="top">변경</v-tooltip>
              </router-link>
            </span>
            <span class="ml-2">
              <router-link to="#" @click.prevent="delFileConfirm()">
                <v-icon icon="mdi-trash-can-outline" size="16" color="secondary" class="mr-2" />
                <v-tooltip activator="parent" location="top">삭제</v-tooltip>
              </router-link>
            </span>
            <div>
              <CInputGroup v-if="isEdit" size="sm">
                <CFormInput
                  type="file"
                  :aria-describedby="`file-edit-${file.pk}`"
                  @input="fileChange($event, file.pk as number)"
                />
                <CInputGroupText
                  :id="`file-edit-${file.pk}`"
                  @click="fileChange($event, file.pk as number)"
                >
                  변경
                </CInputGroupText>
              </CInputGroup>
            </div>
          </td>
        </tr>
      </table>
    </CCol>
  </CRow>

  <CRow class="mb-2">
    <CCol>
      <router-link to="#" @click.prevent="addFileForm = !addFileForm">파일추가</router-link>
    </CCol>
  </CRow>

  <CRow v-if="addFileForm" class="p-3 mb-3" :class="bgLight">
    <CCol>
      <CFormInput type="file" :key="inputKey" size="sm" @input="handleFileChange" />
    </CCol>
    <CCol>
      <CInputGroup v-if="descShow" size="sm">
        <CFormInput v-model="newFile.description" placeholder="부가적인 설명" />
        <CInputGroupText>
          <v-icon icon="mdi-trash-can-outline" size="16" @click="clearFile" />
        </CInputGroupText>
      </CInputGroup>
    </CCol>
  </CRow>

  <CRow v-if="addFileForm">
    <CCol>
      <CButton color="light" size="sm" @click="fileUpload">추가</CButton>
    </CCol>
  </CRow>

  <ConfirmModal ref="RefDelFile">
    <template #default>이 파일을 삭제 하시겠습니까?</template>
    <template #footer>
      <CButton color="warning" @click="fileDelete">삭제</CButton>
    </template>
  </ConfirmModal>
</template>
