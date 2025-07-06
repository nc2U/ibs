<script lang="ts" setup>
import { onBeforeMount, type PropType, ref } from 'vue'

export interface RFile {
  pk: null | number
  file: string
  description?: string
  // newFile?: Blob
  del?: boolean
  edit?: boolean
}

const props = defineProps({ file: { type: Object as PropType<RFile>, required: true } })

const form = ref({
  file: null as null | RFile,
})

const devideUri = (uri: string) => {
  const devidedUri = decodeURI(uri).split('media/')
  return [devidedUri[0] + 'media/', devidedUri[1]]
}

const editFile = () => {
  ;(form.value.file as any).del = false
  ;(form.value.file as any).edit = !(form.value.file as any).edit
}

const fileChange = (event: Event, pk: number) => {
  // enableStore(event)
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    // emit('file-change', { pk, file })
  }
}

onBeforeMount(() => {
  if (props.file) form.value.file = props.file
})
</script>

<template>
  <small>
    현재 :
    <s v-if="(form.file as RFile)?.del || (form.file as RFile)?.edit">
      {{ devideUri(file.file ?? ' ')[1] }}
    </s>
    <a v-else :href="file.file" target="_blank">
      {{ devideUri(file.file ?? ' ')[1] }}
    </a>

    <span>
      <CFormCheck
        v-model="(form.file as RFile).del"
        :id="`del-file-${file.pk}`"
        label="삭제"
        inline
        :disabled="(form.file as RFile).edit"
        class="ml-4"
      />
      <CFormCheck :id="`edit-file-${file.pk}`" label="변경" inline @click="editFile" />
    </span>
    <CRow v-if="(form.file as RFile).edit">
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
