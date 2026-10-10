<script lang="ts" setup>
import { ref, watch } from 'vue'

export interface RFile {
  pk: null | number
  file?: string
  file_name?: string
  description?: string
  del?: boolean
  edit?: boolean
}

interface Props {
  file: RFile
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'file-delete', payload: { pk: number; del: boolean }): void
  (e: 'file-change', payload: { pk: number; file: File }): void
}>()

const fileData = ref<RFile>({
  ...props.file,
  del: props.file.del ?? false,
  edit: props.file.edit ?? false,
})

watch(
  () => props.file,
  newFile => {
    if (newFile) {
      fileData.value = {
        ...newFile,
        del: newFile.del ?? false,
        edit: newFile.edit ?? false,
      }
    }
  },
  { deep: true },
)

const handleEditChange = () => {
  if (fileData.value.edit && props.file.pk !== null && props.file.pk !== undefined) {
    fileData.value.del = false
    emit('file-delete', { pk: props.file.pk, del: false })
  }
}

const handleDeleteChange = () => {
  if (props.file.pk !== null && props.file.pk !== undefined) {
    emit('file-delete', { pk: props.file.pk, del: fileData.value.del ?? false })
  }
}

const fileChange = (event: Event, pk: number) => {
  const el = event.target as HTMLInputElement
  if (el.files?.length) {
    emit('file-change', { pk, file: el.files[0] })
  }
}
</script>

<template>
  <small>
    현재 :
    <s v-if="fileData.del || fileData.edit">{{ file.file_name }}</s>
    <a v-else :href="file.file" target="_blank">{{ file.file_name }}</a>

    <span v-if="file?.description" class="pl-2"> ({{ file.description }}) </span>

    <span>
      <CFormCheck
        v-model="fileData.del"
        :id="`del-file-${file.pk}`"
        label="삭제"
        inline
        :disabled="fileData.edit"
        class="ml-4"
        @change="handleDeleteChange"
      />
      <CFormCheck
        v-model="fileData.edit"
        :id="`edit-file-${file.pk}`"
        label="변경"
        inline
        @change="handleEditChange"
      />
    </span>
    <CRow v-if="fileData.edit">
      <CCol>
        <CInputGroup>
          변경 : &nbsp;
          <CFormInput
            :id="`docs-file-${file.pk}`"
            size="sm"
            type="file"
            @input="fileChange($event, file.pk as number)"
          />
        </CInputGroup>
      </CCol>
    </CRow>
  </small>
</template>
