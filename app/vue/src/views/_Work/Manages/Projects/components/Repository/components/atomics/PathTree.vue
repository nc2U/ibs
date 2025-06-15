<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import type { Changed } from '@/store/types/work_git_repo.ts'

const props = defineProps({
  sha: { type: String, required: true },
  changeFiles: { type: Array as PropType<Changed[]>, default: () => [] },
})

const emit = defineEmits(['into-path', 'file-view', 'diff-view'])

const separatedFiles = computed(() =>
  props.changeFiles.map(item => ({
    path: item.path.split('/'),
    type: item.type,
  })),
)

const intoPath = (path: string, index: number) =>
  emit('into-path', {
    path: path
      .split('/')
      .slice(0, index + 1)
      .join('/') as string,
    sha: props.sha as string,
  })

const viewFile = async (path: string, index: number) =>
  emit('file-view', {
    path: path
      .split('/')
      .slice(0, index + 1)
      .join('/') as string,
    sha: props.sha as string,
  })

const choiceFunc = (isFile: boolean, path: string, index: number) => {
  if (isFile) viewFile(path, index)
  else intoPath(path, index)
}
</script>

<template>
  <CRow class="text-right">
    <CCol>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-plus-circle" color="success" size="" /> 추가됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="warning" size="" /> 변경됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="info" size="" /> 복사됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="purple" size="" /> 이름바뀜
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-minus-circle" color="danger" size="" /> 삭제됨
      </span>
    </CCol>
  </CRow>

  <CRow v-for="(file, i) in separatedFiles" :key="i">
    <CCol>
      <CRow v-for="(item, j) in file.path" :key="j" class="pl-5">
        <CCol :style="`padding-left: ${j * 20}px`">
          <CCol v-if="i === 0 || separatedFiles[i - 1].path[j] !== item">
            <span v-if="j !== file.path.length - 1" class="mr-2">
              <v-icon icon="mdi-folder-open" color="#EFD2A8" size="16" />
            </span>
            <span v-else class="mr-2" style="font-size: 0.8em">
              <v-icon v-if="file.type === 'A'" color="success" icon="mdi-plus-circle" size="" />
              <v-icon
                v-else-if="file.type === 'D'"
                color="danger"
                icon="mdi-minus-circle"
                size=""
              />
              <v-icon v-else-if="file.type === 'R'" color="purple" icon="mdi-circle" size="" />
              <v-icon v-else-if="file.type === 'C'" color="info" icon="mdi-circle" size="" />
              <v-icon v-else color="warning" icon="mdi-circle" size="" />
            </span>
            <span>
              <router-link
                to=""
                @click="choiceFunc(file.path.length - 1 === j, file.path.join('/'), j)"
              >
                {{ item }}
              </router-link>
            </span>
            <span v-if="j === file.path.length - 1">
              (<router-link to="" @click="emit('diff-view', i)">비교(diff)</router-link>)
            </span>
          </CCol>
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>
