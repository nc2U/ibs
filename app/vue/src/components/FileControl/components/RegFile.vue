<script lang="ts" setup>
import { onBeforeMount, type PropType, ref } from 'vue'

export interface RFile {
  pk: null | number
  file: string
  description?: string
  del?: boolean
  edit?: boolean
}

const props = defineProps({
  file: { type: Object as PropType<RFile>, required: true },
  fileName: { type: String, required: true },
})

const emit = defineEmits(['file-change'])

const form = ref<{ file: RFile | null }>({
  file: null,
})

const handleEditToggle = () => {
  const f = form.value.file
  if ((f as RFile)?.edit);
  ;(f as RFile).del = false
}

const fileChange = (event: Event, pk: number) => {
  const el = event.target as HTMLInputElement
  if (el.files?.length) {
    emit('file-change', { pk, file: el.files[0] })
  }
}

onBeforeMount(() => {
  if (props.file) form.value.file = { ...props.file }
})
</script>

<template>
  <small>
    현재 :
    <s v-if="(form.file as RFile)?.del || (form.file as RFile)?.edit">{{ fileName }}</s>
    <a v-else :href="file.file" target="_blank">{{ fileName }}</a>

    <span>
      <CFormCheck
        v-model="(form.file as RFile).del"
        :id="`del-file-${file.pk}`"
        label="삭제"
        inline
        :disabled="(form.file as RFile).edit"
        class="ml-4"
      />
      <CFormCheck
        v-model="(form.file as RFile).edit"
        :id="`edit-file-${file.pk}`"
        label="변경"
        inline
        @click="handleEditToggle"
      />
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
