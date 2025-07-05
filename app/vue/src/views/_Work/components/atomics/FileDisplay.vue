<script lang="ts" setup>
import { computed, type ComputedRef, inject, type PropType, ref } from 'vue'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { NewsFile } from '@/store/types/work_inform.ts'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({ file: { type: Object as PropType<NewsFile>, required: true } })

const emit = defineEmits(['delete-file'])

const RefDelFile = ref() // Del confirm model

const deleteFile = () => {
  emit('delete-file', props.file.pk)
  RefDelFile.value.close()
}

const iProject = inject<ComputedRef<IssueProject | null>>('iProject')
const projStatus = computed(() => iProject?.value?.status)
</script>

<template>
  <CCol class="col-10">
    <v-icon icon="mdi-paperclip" size="sm" color="grey" class="mr-2" />
    <span>
      <a :href="file.file" target="_blank"> {{ cutString(file.file_name, 25) }} </a>
      <v-tooltip activator="parent" location="top">{{ file.file_name }}</v-tooltip>
    </span>
    <span class="file-desc1 mr-1"> ({{ humanizeFileSize(file.file_size) }}) </span>
    <span class="mr-2">
      <a :href="file.file" target="_blank">
        <v-icon icon="mdi-download-box" size="16" color="secondary" />
        <v-tooltip activator="parent" location="top">다운로드</v-tooltip>
      </a>
    </span>
    <span v-if="file.description" class="mr-2">{{ file.description }}</span>
    <span class="file-desc2 mr-1 text-grey"> {{ file.user?.username }}, </span>
    <span class="file-desc2 mr-2 text-grey">{{ timeFormat(file.created) }}</span>

    <span v-if="projStatus !== '9'">
      <router-link to="">
        <v-icon
          icon="mdi-trash-can-outline"
          size="16"
          color="secondary"
          class="mr-2"
          @click="RefDelFile.callModal()"
        />
        <v-tooltip activator="parent" location="top">삭제</v-tooltip>
      </router-link>
    </span>
  </CCol>

  <ConfirmModal ref="RefDelFile">
    <template #default>이 파일의 삭제를 계속 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteFile">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
