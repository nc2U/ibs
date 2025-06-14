<script lang="ts" setup>
import { type PropType } from 'vue'
import type { Changed, ChangedFile } from '@/store/types/work_git_repo.ts'

const props = defineProps({
  sha: { type: String, required: true },
  changeFiles: { type: Array as PropType<Changed[]>, default: () => [] },
})

const emit = defineEmits(['into-path', 'file-view', 'diff-view'])

const pathList = (trees: string) => trees.split('/')

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

  <CRow v-for="(tree, i) in changeFiles" :key="i" class="mb-3">
    <CCol>
      <CRow v-for="(el, j) in pathList(tree.path)" :key="j" class="pl-5">
        <CCol :style="`padding-left: ${j * 25}px`">
          <span v-if="j !== pathList(tree.path).length - 1" class="mr-2">
            <v-icon icon="mdi-folder-open" color="#EFD2A8" size="16" />
          </span>
          <span v-else class="mr-2" style="font-size: 0.8em">
            <v-icon v-if="tree.type === 'A'" color="success" icon="mdi-plus-circle" size="" />
            <v-icon v-else-if="tree.type === 'D'" color="danger" icon="mdi-minus-circle" size="" />
            <v-icon v-else-if="tree.type === 'R'" color="purple" icon="mdi-circle" size="" />
            <v-icon v-else-if="tree.type === 'C'" color="info" icon="mdi-circle" size="" />
            <v-icon v-else color="warning" icon="mdi-circle" size="" />
          </span>
          <span>
            <router-link
              to=""
              @click="choiceFunc(pathList(tree.path).length - 1 === j, tree.path, j)"
              >{{ el }}</router-link
            >
          </span>
          <span v-if="j === pathList(tree.path).length - 1">
            (<router-link to="" @click="emit('diff-view', i)">비교(diff)</router-link>)
          </span>
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>
