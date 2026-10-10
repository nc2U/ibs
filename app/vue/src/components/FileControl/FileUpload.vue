<script lang="ts" setup>
import { computed, ref } from 'vue'

interface FileItem {
  id: number
  file: File | null
  description: string
}

interface Props {
  maxFileSize?: number // 기본 100MB
  maxTotalSize?: number // 기본 100MB
}

const props = withDefaults(defineProps<Props>(), {
  maxFileSize: 100 * 1024 * 1024,
  maxTotalSize: 100 * 1024 * 1024,
})

const emit = defineEmits<{
  (e: 'enable-store', event: Event): void
  (e: 'file-upload', files: { file: File | null; description: string }[]): void
}>()

let nextId = 1
const fileErrorMessage = ref('')
const newFiles = ref<FileItem[]>([{ id: nextId++, file: null, description: '' }])

const totalFileSize = computed(() => {
  return newFiles.value.reduce((acc, item) => acc + (item.file?.size || 0), 0)
})

const formatBytes = (bytes: number, decimals = 1) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

const addFileField = () => {
  fileErrorMessage.value = ''
  newFiles.value.push({ id: nextId++, file: null, description: '' })
}

const removeFileField = (index: number) => {
  fileErrorMessage.value = ''
  newFiles.value.splice(index, 1)
  if (newFiles.value.length === 0) {
    newFiles.value.push({ id: nextId++, file: null, description: '' })
  }
}

const loadFile = (event: Event, item: FileItem) => {
  const el = event.target as HTMLInputElement
  fileErrorMessage.value = ''

  if (el.files && el.files.length > 0) {
    const file = el.files[0]

    // 1. 단일 파일 용량 체크
    if (file.size > props.maxFileSize) {
      fileErrorMessage.value = `[${file.name}] 파일 크기가 제한(${formatBytes(props.maxFileSize)})을 초과합니다.`
      el.value = ''
      item.file = null
      return
    }

    // 2. 전체 총용량 체크 (기존 해당 항목 파일 크기는 제외 후 새로 선택된 파일 포함)
    const currentTotalMinusTarget = newFiles.value.reduce(
      (acc, f) => acc + (f.id === item.id ? 0 : f.file?.size || 0),
      0,
    )
    if (currentTotalMinusTarget + file.size > props.maxTotalSize) {
      fileErrorMessage.value = `총 첨부파일 용량이 제한(${formatBytes(props.maxTotalSize)})을 초과하여 추가할 수 없습니다.`
      el.value = ''
      item.file = null
      return
    }

    item.file = file
    emit('enable-store', event)
  } else {
    item.file = null
  }
}

const getNewFiles = () => {
  const files = newFiles.value
    .filter(f => !!f.file)
    .map(f => ({ file: f.file, description: f.description }))
  emit('file-upload', files)
}

defineExpose({ getNewFiles })
</script>

<template>
  <CRow class="mb-2">
    <CCol sm="12">
      <div class="d-flex align-items-center justify-content-between text-muted small">
        <span>
          <v-icon icon="mdi-paperclip" size="14" class="mr-1" />
          첨부파일 용량 (최대 {{ formatBytes(maxTotalSize) }})
        </span>
        <span :class="{ 'text-danger font-weight-bold': totalFileSize > maxTotalSize }">
          {{ formatBytes(totalFileSize) }} / {{ formatBytes(maxTotalSize) }}
        </span>
      </div>

      <div v-if="fileErrorMessage" class="text-danger small mt-1">
        <v-icon icon="mdi-alert-circle" size="14" class="mr-1" />
        {{ fileErrorMessage }}
      </div>
    </CCol>
  </CRow>

  <CRow v-for="(item, index) in newFiles" :key="item.id" class="mb-2">
    <CCol>
      <CInputGroup>
        <CFormInput :id="`file-${item.id}`" type="file" @change="loadFile($event, item)" />
        <CInputGroupText
          id="basic-addon2"
          role="button"
          style="cursor: pointer"
          @click="index + 1 === newFiles.length ? addFileField() : removeFileField(index)"
        >
          <v-icon
            :icon="`mdi-${index + 1 === newFiles.length ? 'plus' : 'minus'}-thick`"
            :color="index + 1 === newFiles.length ? 'primary' : 'error'"
          />
        </CInputGroupText>
      </CInputGroup>
    </CCol>

    <CCol>
      <CInputGroup>
        <CFormInput
          v-model="item.description"
          placeholder="부가적인 설명"
          @input="emit('enable-store', $event)"
        />
      </CInputGroup>
      <div v-if="item.file" class="text-muted extra-small mt-1">
        용량: {{ formatBytes(item.file.size) }}
      </div>
    </CCol>
  </CRow>
</template>
