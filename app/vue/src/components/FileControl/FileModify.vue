<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { AlertSecondary } from '@/utils/cssMixins.ts'

const props = defineProps({ files: { type: Array, default: () => [] } })

const emit = defineEmits(['file-change'])

const attach = ref(true)

export interface AFile {
  pk: null | number
  file: string
  description?: string
  // newFile?: Blob
  del?: boolean
  edit?: boolean
}

const form = ref({
  files: null as null | AFile[],
})

const devideUri = (uri: string) => {
  const devidedUri = decodeURI(uri).split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1]]
}

// const enableStore = (event: Event) => {
//   const el = event.target as HTMLInputElement
//   attach.value = !el.value
// }

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

onBeforeMount(() => {
  if (props.files.length) form.value.files = props.files
})
</script>

<template>
  <CRow v-if="files && files.length">
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
              label="삭제"
              inline
              :disabled="(form.files as AFile[])[i].edit"
              class="ml-4"
            />
            <!--              @input="enableStore"-->
            <CFormCheck :id="`edit-file-${file.pk}`" label="변경" inline @click="editFile(i)" />
          </span>
          <CRow v-if="(form.files as AFile[])[i].edit">
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
      </CCol>
    </CAlert>
  </CRow>
</template>
