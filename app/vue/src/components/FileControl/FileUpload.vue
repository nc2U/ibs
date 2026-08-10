<script lang="ts" setup>
import { computed, ref } from 'vue'

const props = defineProps({
  maxFileSize: { type: Number, default: 100 * 1024 * 1024 }, // 기본 100MB
  maxTotalSize: { type: Number, default: 100 * 1024 * 1024 }, // 기본 100MB
})

const emit = defineEmits(['enable-store', 'file-upload'])

const fileErrorMessage = ref('')
const newFileNum = ref(1)
const newFileRange = computed(() => range(0, newFileNum.value))
const newFiles = ref<{ file: File | null; description: string }[]>([
  { file: null, description: '' },
])

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

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

const ctlFileNum = (n: number) => {
  fileErrorMessage.value = ''
  if (n + 1 >= newFileNum.value) {
    // 파일 필드 추가
    newFileNum.value++
    newFiles.value.push({ file: null, description: '' })
  } else {
    // 파일 필드 제거
    const input = document.getElementById(`file-${n}`) as HTMLInputElement
    if (input) input.value = ''

    // 마지막 전 요소 삭제 시, 마지막 것도 비움
    if (n === newFiles.value.length - 2) {
      const last = document.getElementById(`file-${n + 1}`) as HTMLInputElement
      if (last) last.value = ''
      newFiles.value[n + 1] = { file: null, description: '' }
    }

    newFiles.value.splice(n, 1)
    newFileNum.value--
  }
}

const loadFile = (event: Event, n: number) => {
  const el = event.target as HTMLInputElement
  fileErrorMessage.value = ''

  if (el.files && el.files.length > 0) {
    const file = el.files[0]

    // 1. 단일 파일 용량 체크
    if (file.size > props.maxFileSize) {
      fileErrorMessage.value = `[${file.name}] 파일 크기가 제한(${formatBytes(props.maxFileSize)})을 초과합니다.`
      el.value = ''
      newFiles.value[n].file = null
      return
    }

    // 2. 전체 총용량 체크 (기존 해당 번호 파일의 크기는 제외 후 새로 선택된 파일 포함)
    const currentTotalMinusTarget = newFiles.value.reduce(
      (acc, item, idx) => acc + (idx === n ? 0 : item.file?.size || 0),
      0,
    )
    if (currentTotalMinusTarget + file.size > props.maxTotalSize) {
      fileErrorMessage.value = `총 첨부파일 용량이 제한(${formatBytes(props.maxTotalSize)})을 초과하여 추가할 수 없습니다.`
      el.value = ''
      newFiles.value[n].file = null
      return
    }

    newFiles.value[n].file = file
    emit('enable-store', event)
  }
}

const getNewFiles = () => {
  const files = newFiles.value.filter(f => !!f.file)
  emit('file-upload', [...files])
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

  <CRow v-for="fNum in newFileRange" :key="`fn-${fNum}`" class="mb-2">
    <CCol>
      <CInputGroup>
        <CFormInput :id="`file-${fNum}`" type="file" @change="loadFile($event, fNum)" />
        <CInputGroupText id="basic-addon2" @click="ctlFileNum(fNum)">
          <v-icon
            :icon="`mdi-${fNum + 1 < newFileNum ? 'minus' : 'plus'}-thick`"
            :color="fNum + 1 < newFileNum ? 'error' : 'primary'"
          />
        </CInputGroupText>
      </CInputGroup>
    </CCol>

    <CCol>
      <CInputGroup v-if="newFiles[fNum]">
        <CFormInput
          v-model="newFiles[fNum].description"
          placeholder="부가적인 설명"
          @input="emit('enable-store', $event)"
        />
      </CInputGroup>
      <div v-if="newFiles[fNum]?.file" class="text-muted extra-small mt-1">
        용량: {{ formatBytes(newFiles[fNum].file.size) }}
      </div>
    </CCol>
  </CRow>
</template>
