<script lang="ts" setup>
import { computed, inject, type PropType, ref } from 'vue'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins.ts'

defineProps({ file: { type: Object as PropType<any>, required: true } })

const iProject = inject('iProject')
const projStatus = computed(() => iProject.value.status)

const RefDelFile = ref()
const delFile = ref<number | null>(null)

const delFileConfirm = (pk: number) => {
  delFile.value = pk
  RefDelFile.value.callModal()
}
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
    <span class="file-desc2 mr-1 text-grey"> {{ file.user.username }}, </span>
    <span class="file-desc2 mr-2 text-grey">{{ timeFormat(file.created) }}</span>

    <span v-if="projStatus !== '9'">
      <router-link to="">
        <v-icon
          icon="mdi-trash-can-outline"
          size="16"
          color="secondary"
          class="mr-2"
          @click="delFileConfirm(file.pk)"
        />
        <v-tooltip activator="parent" location="top">삭제</v-tooltip>
      </router-link>
    </span>
  </CCol>
</template>
