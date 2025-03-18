<script lang="ts" setup>
import { computed, ref } from 'vue'
import type { AFile } from '@/store/types/docs'
import { AlertSecondary } from '@/utils/cssMixins'

defineProps({ docs: { type: Object, default: () => null } })

const emit = defineEmits(['file-upload', 'file-change'])

const attach = ref(true)
const form = ref({
  files: [],
})

const newFileNum = ref(1)
const newFileRange = computed(() => range(0, newFileNum.value))

const devideUri = (uri: string) => {
  const devidedUri = decodeURI(uri).split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1]]
}

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

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
</script>

<template>
  <CRow class="mb-3">
    <CFormLabel for="title" class="col-md-2 col-form-label">파일</CFormLabel>
    <CCol md="10" lg="8" xl="6">
      <CRow v-if="docs && (form.files as AFile[]).length">
        <CAlert :color="AlertSecondary">
          <small>{{ devideUri((form.files as AFile[])[0]?.file ?? ' ')[0] }}</small>
          <CCol v-for="(file, i) in form.files as AFile[]" :key="file.pk" xs="12" color="primary">
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
