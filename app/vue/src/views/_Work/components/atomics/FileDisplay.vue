<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins.ts'

defineProps({ file: { type: Object as PropType<any>, required: true } })

const RefDelFile = ref()
const delFile = ref<number | null>(null)

const delFileConfirm = (pk: number) => {
  delFile.value = pk
  RefDelFile.value.callModal()
}
</script>

<template>
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
    <span class="file-desc2 mr-1 text-grey"> {{ file.user.username }}, </span>
    <span class="file-desc2 mr-2 text-grey">{{ timeFormat(file.created) }}</span>

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

  <!--  <CCol v-if="i === 0" class="text-right form-text col-2">-->
  <!--    <span v-if="projStatus !== '9'" class="mr-2">-->
  <!--      <router-link to="">-->
  <!--        <v-icon icon="mdi-pencil" color="amber" size="18" @click="editMode = !editMode" />-->
  <!--      </router-link>-->
  <!--      <v-tooltip activator="parent" location="top">첨부파일 편집</v-tooltip>-->
  <!--    </span>-->

  <!--    <span v-if="issueFiles.length > 1" class="mr-2">-->
  <!--      <router-link to="">-->
  <!--        <v-icon icon="mdi-download-box" color="secondary" size="18" />-->
  <!--      </router-link>-->
  <!--      <v-tooltip activator="parent" location="top">전체 다운로드</v-tooltip>-->
  <!--    </span>-->
  <!--  </CCol>-->

  <!--  <template v-if="editMode">-->
  <!--    <CCol class="col-5">-->
  <!--      <CInputGroup size="sm">-->
  <!--        <CFormInput-->
  <!--          :id="`issue-file-${file.pk}`"-->
  <!--          type="file"-->
  <!--          placeholder="파일명"-->
  <!--          @change="loadFile($event, i)"-->
  <!--          :disabled="!editFiles[i].edit"-->
  <!--        />-->
  <!--        <CInputGroupText v-if="!editFiles[i].cngFile" class="pb-0">-->
  <!--          <CFormCheck-->
  <!--            :id="`change-file-${file.pk}`"-->
  <!--            label="변경"-->
  <!--            @click="editFiles[i].edit = !editFiles[i].edit"-->
  <!--            size="sm"-->
  <!--          />-->
  <!--        </CInputGroupText>-->

  <!--        <CInputGroupText v-else class="pb-0">-->
  <!--          <v-icon-->
  <!--            icon="mdi-trash-can-outline"-->
  <!--            color="grey"-->
  <!--            size="sm"-->
  <!--            @click="removeFile(file.pk, i)"-->
  <!--          />-->
  <!--        </CInputGroupText>-->
  <!--      </CInputGroup>-->
  <!--    </CCol>-->

  <!--    <CCol class="col-6">-->
  <!--      <CInputGroup size="sm">-->
  <!--        <CFormInput-->
  <!--          v-model="editFiles[i].description"-->
  <!--          placeholder="부가적인 설명"-->
  <!--          @keydown.enter="editFileSubmit(editFiles[i])"-->
  <!--        />-->
  <!--        <CInputGroupText-->
  <!--          v-if="editFiles[i].cngFile || file.description !== editFiles[i].description"-->
  <!--          :id="`file-desc-${file.pk}`"-->
  <!--          @click="editFileSubmit(editFiles[i])"-->
  <!--        >-->
  <!--          업데이트-->
  <!--        </CInputGroupText>-->
  <!--      </CInputGroup>-->
  <!--    </CCol>-->
  <!--  </template>-->
</template>
