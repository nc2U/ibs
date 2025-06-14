<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { Changed, ChangedFile, Commit, DiffApi } from '@/store/types/work_git_repo.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { btnLight, btnSecondary } from '@/utils/cssMixins.ts'
import RevisionControl from './HeaderMenu/RevisionControl.vue'
import PathTree from './atomics/PathTree.vue'
import Diff from './atomics/Diff.vue'

const props = defineProps({
  repo: { type: Number, required: true },
})

const emit = defineEmits(['goto-back', 'get-diff', 'get-commit', 'into-path', 'file-view'])

const tabKey = ref(1)

const gitStore = useGitRepo()
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
const changedFile = computed<ChangedFile | null>(() => gitStore.changedFile)

const fetchGitDiff = (repo, diff_hash: string) => gitStore.fetchGitDiff(repo, diff_hash)
const fetchChangedFiles = (repo: number, sha: string) => gitStore.fetchChangedFiles(repo, sha)

const diffIndex = ref<number | null>(null)
const partialDiffView = (n: number) => {
  diffIndex.value = n
  tabKey.value = 2
}

const tabReset = () => {
  diffIndex.value = null
  tabKey.value = 1
}

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

  <CRow class="pl-4">
    <CCol>
      <ul class="pl-3">
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

  <CRow v-if="commit?.issues.length" class="mb-5">
    <CCol>
      <h6>연결된 업무</h6>
      <ul class="ml-4">
        <li v-for="issue in commit.issues" :key="issue.pk">
          <router-link
            :to="{ name: '(업무) - 보기', params: { projId: issue.project, issueId: issue.pk } }"
          >
            {{ issue.tracker }} #{{ issue?.pk }}
          </router-link>
          :<span class="ml-2">{{ issue?.subject }}</span>
        </li>
      </ul>
    </CCol>
  </CRow>

  <CNav variant="tabs" class="mb-3">
    <CNavItem>
      <CNavLink href="javascript:void(0);" :active="tabKey === 1" @click="tabReset">
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
    @diff-view="partialDiffView"
  />

  <v-btn
    v-if="tabKey === 2"
    variant="outlined"
    :color="btnSecondary"
    @click="emit('goto-back')"
    size="small"
    class="mb-3"
  >
    목록으로
  </v-btn>

  <Diff
    v-if="tabKey === 2"
    :git-diff="gitDiff as DiffApi"
    :diff-index="diffIndex as number"
    @get-diff="emit('get-diff', $event)"
  />

  <v-divider v-if="tabKey === 1" class="mb-2" />

  <v-btn
    variant="outlined"
    :color="btnSecondary"
    @click="emit('goto-back')"
    size="small"
    class="my-3"
  >
    목록으로
  </v-btn>
</template>
