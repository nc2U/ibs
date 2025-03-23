<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUpdate, type PropType, ref } from 'vue'
import type { AFile } from '@/store/types/docs'
import { AlertSecondary } from '@/utils/cssMixins'

const props = defineProps({ files: { type: Array as PropType<AFile[]>, default: () => [] } })

const emit = defineEmits(['file-upload', 'file-change'])

const attach = ref(true)
const form = ref<{ files: AFile[] }>({
  files: [],
})

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const newFileNum = ref(1)
const newFileRange = computed(() => range(0, newFileNum.value))

const devideUri = (uri: string) => {
  const devidedUri = decodeURI(uri).split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1]]
}

const ctlFileNum = (n: number) => {
  if (n + 1 >= newFileNum.value) newFileNum.value = newFileNum.value + 1
  else newFileNum.value = newFileNum.value - 1
}

const enableStore = (event: Event) => {
  const el = event.target as HTMLInputElement
  attach.value = !el.value
}

const editFile = (i: number) => {
  if ((form.value.files as any[]).length) {
    ;(form.value.files as any[])[i].del = false
    ;(form.value.files as any[])[i].edit = !(form.value.files as any[])[i].edit
  }
}

const fileChange = (event: Event, pk: number) => {
  enableStore(event)
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-change', { pk, file })
  }
}

const fileUpload = (event: Event) => {
  enableStore(event)
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-upload', file)
  }
}

const dataSetup = () => {
  if (props.files) form.value.files = props.files
  form.value.files.forEach(file => {
    file.del = false
    file.edit = false
  })
}

onBeforeMount(() => dataSetup())
onBeforeUpdate(() => dataSetup())
</script>

<template>
  <CRow>
    <CFormLabel for="title" class="col-form-label col-2 text-right">파일</CFormLabel>
    <CCol class="col-sm-10 col-xl-8">
      <CRow v-if="(files as AFile[]).length">
        <CAlert :color="AlertSecondary">
          <small>{{ devideUri((files as AFile[])[0]?.file ?? ' ')[0] }}</small>
          <CCol v-for="(file, i) in files as AFile[]" :key="file.pk" xs="12" color="primary">
            <small>
              현재 :
              <a :href="file.file" target="_blank">
                {{ devideUri(file.file ?? ' ')[1] }}
              </a>
              <span>
                <CFormCheck
                  v-model="(form.files as AFile[])[i].del"
                  :id="`del-file-${file.pk}`"
                  @input="enableStore"
                  label="삭제"
                  inline
                  :disabled="(form.files as AFile[])[i].edit"
                  class="ml-4"
                />
                <CFormCheck :id="`edit-file-${file.pk}`" label="변경" inline @click="editFile(i)" />
              </span>
              <CRow v-if="(form.files as AFile[])[i].edit">
                <CCol>
                  <CInputGroup>
                    변경 : &nbsp;
                    <CFormInput
                      :id="`docs-file-${file.pk}`"
                      v-model="(form.files as AFile[])[i].newFile"
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
          <CInputGroup v-for="fNum in newFileRange" :key="`fn-${fNum}`" class="mb-2">
            <CFormInput :id="`file-${fNum}`" type="file" @input="fileUpload" />
            <CInputGroupText id="basic-addon2" @click="ctlFileNum(fNum)">
              <v-icon
                :icon="`mdi-${fNum + 1 < newFileNum ? 'minus' : 'plus'}-thick`"
                :color="fNum + 1 < newFileNum ? 'error' : 'primary'"
              />
            </CInputGroupText>
          </CInputGroup>
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>
