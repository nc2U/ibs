<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { AFile } from '@/store/types/docs'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ file: { type: Object as PropType<AFile>, required: true } })

const emit = defineEmits(['file-delete'])

const RefDelFile = ref()

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
  <td>
    <v-icon icon="mdi-paperclip" size="sm" class="mr-2" />
    <a :href="file.file" target="_blank"> {{ cutString(file.file_name, 60) }} </a>
    <span class="ml-1">({{ humanizeFileSize(file.file_size) }})</span>
    <span class="mx-2">
      <a :href="file.file" target="_blank">
        <v-icon icon="mdi-download" size="20" color="secondary" />
        <v-tooltip activator="parent" location="top">다운로드</v-tooltip>
      </a>
    </span>
  </td>
  <td class="px-2">{{ file.description }}</td>
  <td class="text-secondary">
    <span>{{ file.user }}, {{ timeFormat(file.created, false, '/') }}</span>
    <span class="ml-2">
      <router-link to="">
        <v-icon
          icon="mdi-trash-can-outline"
          size="16"
          color="secondary"
          class="mr-2"
          @click="delFileConfirm(file.pk as number)"
        />
        <v-tooltip activator="parent" location="top">삭제</v-tooltip>
      </router-link>
    </span>
  </td>

  <ConfirmModal ref="RefDelFile">
    <template #default>이 파일 삭제를 계속 진행하시겠습니까?</template>
    <template #footer>
      <CButton color="warning" @click="delFileSubmit">삭제</CButton>
    </template>
  </ConfirmModal>
</template>
