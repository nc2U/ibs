<script lang="ts" setup>
import { nextTick, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { AFile } from '@/store/types/docs'
import { AlertSecondary } from '@/utils/cssMixins'

const props = defineProps({
  label: { type: String, default: '파일' },
  files: { type: Array as PropType<AFile[]>, default: () => [] },
})

const emit = defineEmits(['files-update', 'file-upload', 'file-change'])

const form = ref<{ files: AFile[] }>({ files: [] })

const formUpdate = () => nextTick(() => emit('files-update', form.value.files))

let slotSeq = 1
const newFileSlots = ref<{ id: number; file: File | null }[]>([{ id: slotSeq++, file: null }])

const devideUri = (uri: string) => {
  if (!uri || !uri.includes('media/')) return ['', uri || '']
  let decoded = uri
  try {
    decoded = decodeURI(uri)
  } catch {
    // 잘못 인코딩된 URI는 원본 사용
  }
  const devidedUri = decoded.split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1] || '']
}

const ctlFileNum = (idx: number) => {
  if (idx + 1 >= newFileSlots.value.length) {
    newFileSlots.value.push({ id: slotSeq++, file: null })
  } else {
    newFileSlots.value.splice(idx, 1)
  }
}

const fileUpload = (event: Event, idx: number) => {
  const el = event.target as HTMLInputElement
  const file = el.files?.[0] ?? null
  if (newFileSlots.value[idx]) {
    newFileSlots.value[idx].file = file
  }
  if (file) emit('file-upload', file)
}

const getNewFiles = (): File[] =>
  newFileSlots.value.map(s => s.file).filter((f): f is File => f !== null)

const editFile = (i: number) => {
  const target = form.value.files[i]
  if (target) {
    target.del = false
    formUpdate()
  }
}

const fileChange = (event: Event, pk: number) => {
  const el = event.target as HTMLInputElement
  if (el.files?.[0]) {
    emit('file-change', { pk, file: el.files[0] })
  }
}

const delFile = () => {
  formUpdate()
}

const checkRelease = () => {
  form.value.files.forEach(f => {
    f.edit = false
    f.del = false
  })
  newFileSlots.value = [{ id: slotSeq++, file: null }]
}

defineExpose({ checkRelease, getNewFiles })

const dataSetup = () => {
  if (props.files) {
    form.value.files = props.files.map(file => ({
      ...file,
      del: false,
      edit: false,
    }))
  }
  formUpdate()
}

watch(
  () => props.files,
  () => dataSetup(),
  { deep: true },
)

onBeforeMount(() => dataSetup())
</script>

<template>
  <CRow>
    <CFormLabel for="title" class="col-form-label col-2 text-end">{{ label }}</CFormLabel>
    <CCol class="col-sm-10 col-xl-8">
      <CRow v-if="(files as AFile[]).length">
        <CAlert :color="AlertSecondary">
          <small>{{ devideUri((files as AFile[])[0]?.file ?? ' ')[0] }}</small>
          <CCol v-for="(file, i) in files as AFile[]" :key="file.pk" xs="12">
            <small>
              현재 :
              <a :href="file.file" target="_blank" rel="noopener noreferrer">
                {{ devideUri(file.file ?? ' ')[1] }}
              </a>
              <span>
                <CFormCheck
                  v-if="form.files[i]"
                  :id="`del-file-${i}`"
                  v-model="form.files[i].del"
                  label="삭제"
                  inline
                  :disabled="form.files[i]?.edit"
                  class="ms-4"
                  @change="delFile"
                />
                <CFormCheck
                  v-if="form.files[i]"
                  :id="`edit-file-${i}`"
                  v-model="form.files[i].edit"
                  label="변경"
                  inline
                  @change="editFile(i)"
                />
              </span>
              <CRow v-if="(form.files as AFile[])[i]?.edit">
                <CCol>
                  <CInputGroup>
                    변경 : &nbsp;
                    <CFormInput
                      :id="`docs-file-${i}`"
                      size="sm"
                      type="file"
                      @input="fileChange($event, file.pk as number)"
                    />
                  </CInputGroup>
                </CCol>
              </CRow>
            </small>
          </CCol>
        </CAlert>
      </CRow>

      <CRow class="mb-2">
        <CCol>
          <CInputGroup v-for="(slot, idx) in newFileSlots" :key="`fn-${slot.id}`" class="mb-2">
            <CFormInput :id="`file-${slot.id}`" type="file" @input="fileUpload($event, idx)" />
            <CInputGroupText class="pointer" @click="ctlFileNum(idx)">
              <v-icon
                :icon="`mdi-${idx + 1 < newFileSlots.length ? 'minus' : 'plus'}-thick`"
                :color="idx + 1 < newFileSlots.length ? 'error' : 'primary'"
              />
            </CInputGroupText>
          </CInputGroup>
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>
