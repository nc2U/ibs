<script lang="ts" setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['enable-store', 'file-upload'])

const newFileNum = ref(1)
const newFileRange = computed(() => range(0, newFileNum.value))
const newFiles = ref<{ file: File | null; description: string }[]>([
  { file: null, description: '' },
])

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const ctlFileNum = (n: number) => {
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
  if (el.files) {
    const file = el.files[0]
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
  <CRow v-for="fNum in newFileRange" :key="`fn-${fNum}`" class="mb-2">
    <CCol>
      <CInputGroup>
        <CFormInput :id="`file-${fNum}`" type="file" @input="loadFile($event, fNum)" />
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
    </CCol>
  </CRow>
</template>
