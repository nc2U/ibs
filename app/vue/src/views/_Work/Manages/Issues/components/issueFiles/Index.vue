<script lang="ts" setup>
import { ref, onBeforeMount, type PropType, watch } from 'vue'
import type { IssueFile } from '@/store/types/work_project.ts'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  projStatus: { type: String, default: '' },
  issueFiles: { type: Array as PropType<IssueFile[]>, default: () => [] },
})

watch(
  () => props.issueFiles,
  nVal => {
    editFiles.value = JSON.parse(JSON.stringify(nVal))
  },
)

const emit = defineEmits(['file-change', 'issue-file-control'])

const RefDelFile = ref()

// file 관련 코드
const editMode = ref(false)

const editFiles = ref<IssueFile[]>([])

const loadFile = (event: Event, i: number) => {
  const el = event.target as HTMLInputElement
  if (el.files && el.files[0]) editFiles.value[i].cngFile = el.files[0]
}

const removeFile = (filePk: number, i: number) => {
  const file_form = document.getElementById(`issue-file-${filePk}`) as HTMLInputElement
  file_form.value = ''
  editFiles.value[i].cngFile = null
  editFiles.value[i].edit = false
}

const editFileSubmit = (payload: IssueFile) => {
  const form = new FormData()
  form.append('edit_file', JSON.stringify(payload.pk))
  if (payload.cngFile) form.append('cng_file', payload.cngFile)
  form.append('edit_file_desc', payload.description)
  emit('issue-file-control', form)
  editMode.value = false
}

const delFile = ref<number | null>(null)
const delFileConfirm = (pk: number) => {
  delFile.value = pk
  RefDelFile.value.callModal()
}
const delFileSubmit = () => {
  const form = new FormData()
  form.append('del_file', JSON.stringify(delFile.value))
  emit('issue-file-control', form)
  delFile.value = null
  RefDelFile.value.close()
}

onBeforeMount(async () => {
  if (props.issueFiles) editFiles.value = JSON.parse(JSON.stringify(props.issueFiles))
})
</script>

<template>
  <CRow class="mb-3">
    <CCol>
      <CRow class="mb-2">
        <CCol class="title">파일</CCol>
      </CRow>
      <CRow v-for="(file, i) in issueFiles" :key="file.pk">
        <CCol class="col-10">
          <v-icon icon="mdi-paperclip" size="sm" color="grey" class="mr-2" />
          <span>
            <a :href="file.file" target="_blank"> {{ cutString(file.file_name, 25) }} </a>
            <v-tooltip activator="parent" location="top">{{ file.file_name }}</v-tooltip>
          </span>
          <span class="file-desc1 mr-1"> ({{ humanizeFileSize(file.file_size) }}) </span>
          <span class="mr-2">
            <a :href="file.file" target="_blank">
              <v-icon icon="mdi-download-box" size="16" color="secondary" />
              <v-tooltip activator="parent" location="top">다운로드</v-tooltip>
            </a>
          </span>
          <span v-if="file.description" class="mr-2">{{ file.description }}</span>
          <span class="file-desc2 mr-1"> {{ file.user.username }}, </span>
          <span class="file-desc2 mr-2">{{ timeFormat(file.created) }}</span>
          <span v-if="projStatus !== '9'">
            <router-link to="">
              <v-icon
                icon="mdi-trash-can-outline"
                size="16"
                color="secondary"
                class="mr-2"
                @click="delFileConfirm(file.pk)"
              />
              <v-tooltip activator="parent" location="top">삭제</v-tooltip>
            </router-link>
          </span>
        </CCol>

        <CCol v-if="i === 0" class="text-right form-text col-2">
          <span v-if="projStatus !== '9'" class="mr-2">
            <router-link to="">
              <v-icon icon="mdi-pencil" color="amber" size="18" @click="editMode = !editMode" />
            </router-link>
            <v-tooltip activator="parent" location="top">첨부파일 편집</v-tooltip>
          </span>

          <span v-if="issueFiles.length > 1" class="mr-2">
            <router-link to="">
              <v-icon icon="mdi-download-box" color="secondary" size="18" />
            </router-link>
            <v-tooltip activator="parent" location="top">전체 다운로드</v-tooltip>
          </span>
        </CCol>

        <template v-if="editMode">
          <CCol class="col-5">
            <CInputGroup size="sm">
              <CFormInput
                :id="`issue-file-${file.pk}`"
                type="file"
                placeholder="파일명"
                @change="loadFile($event, i)"
                :disabled="!editFiles[i].edit"
              />
              <CInputGroupText v-if="!editFiles[i].cngFile" class="pb-0">
                <CFormCheck
                  :id="`change-file-${file.pk}`"
                  label="변경"
                  @click="editFiles[i].edit = !editFiles[i].edit"
                  size="sm"
                />
              </CInputGroupText>

              <CInputGroupText v-else class="pb-0">
                <v-icon
                  icon="mdi-trash-can-outline"
                  color="grey"
                  size="sm"
                  @click="removeFile(file.pk, i)"
                />
              </CInputGroupText>
            </CInputGroup>
          </CCol>

          <CCol class="col-6">
            <CInputGroup size="sm">
              <CFormInput
                v-model="editFiles[i].description"
                placeholder="부가적인 설명"
                @keydown.enter="editFileSubmit(editFiles[i])"
              />
              <CInputGroupText
                v-if="editFiles[i].cngFile || file.description !== editFiles[i].description"
                :id="`file-desc-${file.pk}`"
                @click="editFileSubmit(editFiles[i])"
              >
                업데이트
              </CInputGroupText>
            </CInputGroup>
          </CCol>
        </template>
      </CRow>
    </CCol>
  </CRow>

  <v-divider v-if="projStatus !== '9'" />

  <ConfirmModal ref="RefDelFile">
    <template #default>이 파일 삭제를 계속 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="delFileSubmit">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
.title {
  font-weight: bold;
}

.file-desc1 {
  font-size: 0.9em;
  color: #777;
}

.file-desc2 {
  font-size: 0.85em;
  color: #888;
}
</style>
