<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { Changed, ChangedFile, Commit, DiffApi } from '@/store/types/work_github.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import { btnLight } from '@/utils/cssMixins.ts'
import RevisionControl from './HeaderMenu/RevisionControl.vue'
import PathTree from './atomics/PathTree.vue'
import Diff from './atomics/Diff.vue'

const props = defineProps({
  repo: { type: Number, required: true },
})

const emit = defineEmits(['goto-back', 'get-commit', 'into-path', 'file-view'])

const tabKey = ref(1)

const gitStore = useGithub()
const commit = computed<Commit | null>(() => gitStore.commit)
watch(
  () => commit.value,
  async newVal => {
    if (newVal) {
      const diff_hash = `?base=${newVal.parents[0]}&head=${newVal.commit_hash}`
      await fetchGitDiff(props.repo, diff_hash)
      await fetchChangedFiles(props.repo as number, newVal.commit_hash)
    }
  },
)
const gitDiff = computed<DiffApi | null>(() => gitStore.gitDiff)
watch(
  () => gitDiff.value,
  nVal => {
    if (!nVal?.diff) tabKey.value = 1
  },
)
const changedFile = computed(() => gitStore.changedFile)

const fetchGitDiff = (repo, diff_hash: string) => gitStore.fetchGitDiff(repo, diff_hash)
const fetchChangedFiles = (repo: number, sha: string) => gitStore.fetchChangedFiles(repo, sha)

onBeforeMount(async () => {
  if (commit.value) {
    const diff_hash = `?base=${commit.value.parents[0]}&head=${commit.value.commit_hash}`
    await fetchGitDiff(props.repo, diff_hash)
    await fetchChangedFiles(props.repo as number, commit.value.commit_hash)
  }
})
</script>

<template>
  <CRow class="pt-2 flex-lg-row flex-column-reverse">
    <CCol>
      <h5>리비전 {{ commit?.commit_hash.substring(0, 8) }}</h5>

      <span>
        Austin Kho 이(가)
        <router-link to="">{{ elapsedTime(commit?.date) }}</router-link>
        에 추가함
      </span>
    </CCol>

    <CCol class="mb-2">
      <RevisionControl :commit="commit as Commit" @get-commit="emit('get-commit', $event)" />
    </CCol>
  </CRow>

  <v-divider class="mt-1" />

  <CRow class="pl-5">
    <CCol>
      <ul class="pl-5">
        <li><b>ID</b> {{ commit?.commit_hash }}</li>
        <li v-if="commit?.parents.length">
          <b>상위 </b>
          <span v-for="(hash, i) in commit.parents" :key="hash">
            <router-link to="" @click="emit('get-commit', hash)">
              {{ hash.substring(0, 8) }}
            </router-link>
            <span v-if="i < commit.parents.length - 1">, </span>
          </span>
        </li>
        <li v-if="commit?.children.length">
          <b>하위 </b>
          <span v-for="(hash, i) in commit.children" :key="hash">
            <router-link to="" @click="emit('get-commit', hash)">
              {{ hash.substring(0, 8) }}
            </router-link>
            <span v-if="i < commit.children.length - 1">, </span>
          </span>
        </li>
      </ul>
    </CCol>
  </CRow>

  <CRow class="mb-5">
    <CCol>{{ commit?.message }}</CCol>
  </CRow>

  <CRow class="mb-5">
    <CCol>
      <h6>연결된 업무</h6>
    </CCol>
  </CRow>

  <CNav variant="tabs" class="mb-5">
    <CNavItem>
      <CNavLink href="javascript:void(0);" :active="tabKey === 1" @click="tabKey = 1">
        변경사항들
      </CNavLink>
    </CNavItem>

    <CNavItem v-if="gitDiff?.diff">
      <CNavLink href="javascript:void(0);" :active="tabKey === 2" @click="tabKey = 2">
        차이점보기
      </CNavLink>
    </CNavItem>
  </CNav>

  <PathTree
    v-if="tabKey === 1"
    :sha="changedFile?.sha as string"
    :change-files="changedFile?.changed as Changed[]"
    @into-path="emit('into-path', $event)"
    @file-view="emit('file-view', $event)"
  />
  <Diff v-if="tabKey === 2" :git-diff="gitDiff as DiffApi" />

  <v-divider v-if="tabKey === 1" class="mb-2" />

  <v-btn @click="emit('goto-back')" :color="btnLight" size="small" class="my-5">목록으로</v-btn>
</template>
