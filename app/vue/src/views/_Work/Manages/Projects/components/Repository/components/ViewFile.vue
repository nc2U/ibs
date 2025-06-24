<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { btnSecondary } from '@/utils/cssMixins.ts'
import type { CommitApi, FileInfo } from '@/store/types/work_git_repo.ts'
import Loading from '@/components/Loading/Index.vue'
import FileContent from './atomics/FileContent.vue'
import FileHistory from './atomics/FileHistory.vue'

defineProps({
  repoName: { type: String, required: true },
  currRefs: { type: String, required: true },
})

const emit = defineEmits(['into-path'])

const viewSort = ref<'file' | 'history' | 'desc'>('file')

const fileData = ref<FileInfo>()
const fileCommits = ref<CommitApi[]>([])

const [route, router] = [useRoute(), useRouter()]
const repoId = computed(() => Number(route.params.repoId))
const sha = computed(() => route.params.sha as string)
const path = computed(() => route.params.path)

const currentPath = computed(() =>
  Array.isArray(path.value)
    ? path.value[0].split('/').slice(0, -1)
    : path.value.split('/').slice(0, -1),
)

const intoPath = (path: string) => {
  const index = currentPath.value.indexOf(path)
  const nowPath = index === -1 ? null : currentPath.value.slice(0, index + 1).join('/')
  router.push({ name: '(저장소)' })
  emit('into-path', nowPath)
}

const gitStore = useGitRepo()
const fetchFileView = (repo: number, path: string, sha: string) =>
  gitStore.fetchFileView(repo, path, sha)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  const [file, commits] = await fetchFileView(repoId.value, path.value as string, sha.value)
  fileData.value = file
  fileCommits.value = commits
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <CRow class="py-2">
    <CCol>
      <h5>
        <router-link to="" @click="intoPath('')">{{ repoName }}</router-link>
        <span v-for="path in currentPath" :key="path">
          /
          <router-link to="" @click="intoPath(path)">{{ path }}</router-link>
        </span>
        /
        {{ fileData?.name }}
        @ {{ currRefs }}
      </h5>
    </CCol>
  </CRow>

  <CNav variant="tabs" class="mx-2 mt-3">
    <CNavItem @click="viewSort = 'file'">
      <CNavLink :active="viewSort === 'file'"> 보기</CNavLink>
    </CNavItem>
    <CNavItem @click="viewSort = 'history'">
      <CNavLink :active="viewSort === 'history'"> 이력</CNavLink>
    </CNavItem>
    <CNavItem>
      <CNavLink :active="viewSort === 'desc'" disabled> 이력해설</CNavLink>
    </CNavItem>
  </CNav>

  <FileContent v-if="viewSort === 'file' && fileData" :file-data="fileData" />

  <FileHistory v-else-if="viewSort === 'history'" :commits="fileCommits" />

  <CRow v-if="viewSort === 'file'" class="pl-2">
    <CCol>
      <v-btn
        size="small"
        variant="outlined"
        :color="btnSecondary"
        @click="router.push({ name: '(저장소)' })"
      >
        목록으로
      </v-btn>
    </CCol>
  </CRow>
</template>
