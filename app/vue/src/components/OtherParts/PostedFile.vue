<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { AFile } from '@/store/types/docs'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ file: { type: Object as PropType<AFile>, required: true } })

const emit = defineEmits(['file-delete'])

const RefDelFile = ref()
const isEdit = ref(false)

const editFile = (pk: number) => {
  alert(pk)
}

const delFile = ref<number | null>(null)
const delFileConfirm = (pk: number) => {
  delFile.value = pk
  RefDelFile.value.callModal()
}

const delFileSubmit = () => {
  const form = new FormData()
  form.append('del_file', JSON.stringify(delFile.value))
  emit('file-delete', form)
  delFile.value = null
  RefDelFile.value.close()
}
</script>

<template>
  <td style="vertical-align: top">
    <v-icon icon="mdi-paperclip" size="sm" class="mr-2" />
    <a :href="file.file" target="_blank"> {{ cutString(file.file_name, 60) }} </a>
    <span class="ml-1">({{ humanizeFileSize(file.file_size as number) }})</span>
    <span class="mx-2">
      <a :href="file.file" target="_blank">
        <v-icon icon="mdi-download" size="20" color="secondary" />
        <v-tooltip activator="parent" location="top">다운로드</v-tooltip>
      </a>
    </span>
  </td>
  <td class="px-2">{{ file.description }}</td>
  <td class="text-secondary">
    <span>{{ file.user }}, {{ timeFormat(file.created as string, false, '/') }}</span>
    <span class="ml-2">
      <router-link to="#" @click.prevent="isEdit = !isEdit">
        <v-icon icon="mdi-pencil" size="16" color="secondary" />
        <v-tooltip activator="parent" location="top">변경</v-tooltip>
      </router-link>
    </span>
    <span class="ml-2">
      <router-link to="#" @click.prevent="delFileConfirm(file.pk as number)">
        <v-icon icon="mdi-trash-can-outline" size="16" color="secondary" class="mr-2" />
        <v-tooltip activator="parent" location="top">삭제</v-tooltip>
      </router-link>
    </span>
    <div>
      <CInputGroup v-if="isEdit" size="sm">
        <CFormInput type="file" :aria-describedby="`file-edit-${file.pk}`" />
        <CInputGroupText :id="`file-edit-${file.pk}`" @click="editFile(file.pk as number)">
          추가
        </CInputGroupText>
      </CInputGroup>
    </div>
  </td>

  <ConfirmModal ref="RefDelFile">
    <template #default>이 파일을 삭제 하시겠습니까?</template>
    <template #footer>
      <CButton color="warning" @click="delFileSubmit">삭제</CButton>
    </template>
  </ConfirmModal>
</template>
