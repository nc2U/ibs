<script lang="ts" setup>
import { computed, onBeforeMount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { Repository, Commit, BranchInfo, Tree, DiffApi } from '@/store/types/work_git_repo.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import BranchTree from './components/BranchTree.vue'
import ViewFile from './components/ViewFile.vue'
import ViewRevision from './components/ViewRevision.vue'
import Revisions from './components/Revisions.vue'
import ViewDiff from './components/ViewDiff.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const cFilter = ref({
  repo: 1 as number,
  branch: '',
  project: undefined as number | undefined,
  issues: [],
  page: 1,
  limit: 25,
  search: '',
  up_to: '',
})

const [route, router] = [useRoute(), useRouter()]

const workStore = useWork()
const project = computed<IssueProject | null>(() => workStore.issueProject)
watch(project, nVal => {
  if (nVal) dataSetup(nVal?.pk as number)
})

// get github api
const gitStore = useGitRepo()
const repo = computed<Repository | null>(() => gitStore.repository)
const repoList = computed<Repository[]>(() => gitStore.repositoryList)
const commitList = computed<Commit[]>(() => gitStore.commitList)

watch(repo, nVal => {
  if (nVal) cFilter.value.repo = nVal.pk as number
})
watch(repoList, nVal => {
  if (nVal.length) fetchRepo(nVal[0].pk as number)
})

const fetchRepo = (pk: number) => gitStore.fetchRepo(pk)
const fetchRepoList = (project?: number, is_def?: string) => gitStore.fetchRepoList(project, is_def)
const fetchCommitList = (payload: {
  repo: number
  branch?: string
  project?: number
  issues?: number[]
  page?: number
  limit?: number
  search?: string
  up_to?: string
}) => gitStore.fetchCommitList(payload)

const branches = computed<string[]>(() => gitStore.branches)
const tags = computed<string[]>(() => gitStore.tags)
const default_branch = computed<string>(() => gitStore.default_branch)

const curr_path = computed(() => gitStore.curr_path)
const curr_refs = computed<string>(() => gitStore.curr_refs || default_branch.value)
const branch_refs = computed<BranchInfo | null>(() => gitStore.branch_refs)
watch(
  () => branch_refs.value?.branches,
  newVal => {
    if (newVal && newVal.length > 0)
      cFilter.value.branch = newVal.includes(curr_refs.value) ? curr_refs.value : newVal[0]
  },
)
const branch_tree = computed<Tree[]>(() => gitStore.branch_tree)
const up_to_sha = computed<string>(() => gitStore.up_to_sha)
watch(up_to_sha, newVal => {
  if (newVal) cFilter.value.up_to = newVal
})

const fetchRepoApi = (pk: number) => gitStore.fetchRepoApi(pk)
const fetchBranches = (repoPk: number) => gitStore.fetchBranches(repoPk)
const fetchTags = (repoPk: number) => gitStore.fetchTags(repoPk)
const fetchRefTree = (payload: { repo: number; refs: string; path?: string }) =>
  gitStore.fetchRefTree(payload)
const fetchGitDiff = (pk: number, diff_hash: string, full = false) =>
  gitStore.fetchGitDiff(pk, diff_hash, full)

const changeRefs = async (refs: string, isSha = false) => {
  cFilter.value.page = 1
  cFilter.value.limit = 25
  // if (isSha) cFilter.value.up_to = refs
  await fetchRefTree({ repo: repo.value?.pk as number, refs })
  await fetchCommitList(cFilter.value)
}

// into path
const intoPath = async (path: string) => {
  gitStore.setCurrPath(path)
  await fetchRefTree({
    repo: repo.value?.pk as number,
    refs: curr_refs.value,
    path,
  })
}

// revisons
const getListSort = ref<'latest' | 'all' | 'branch'>('latest')

const setListSort = (sort: 'latest' | 'all') => (getListSort.value = sort)

const headId = ref<number | null>(null)
const baseId = ref<number | null>(null)

const headSet = (revision_id: number) => (headId.value = revision_id)
const baseSet = (revision_id: number) => (baseId.value = revision_id)

const getCommit = async (limit: number) => {
  cFilter.value.page = 1
  cFilter.value.limit = limit
  await fetchCommitList(cFilter.value)
}

const pageSelect = (page: number) => {
  cFilter.value.page = page
  fetchCommitList(cFilter.value)
}

const dataSetup = async (proj: number) => {
  if (proj) {
    cFilter.value.project = proj
    await fetchRepoList(proj, 'true')
    await fetchRepo(repoList.value[0].pk as number)
    if (repo.value) {
      cFilter.value.repo = repo.value?.pk as number
      cFilter.value.branch = default_branch.value
      await fetchRepoApi(repo.value?.pk as number)
      await fetchBranches(cFilter.value.repo)
      await fetchTags(cFilter.value.repo)
      await fetchRefTree({
        repo: cFilter.value.repo,
        refs: curr_refs.value,
        path: curr_path.value,
      })
      await fetchCommitList(cFilter.value)
    }
  }
}

const loading = ref(true)
onBeforeMount(async () => {
  if (project.value) await dataSetup((project.value as IssueProject).pk as number)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <template v-if="route.name === '(저장소)'">
        <BranchTree
          :repo="repo as Repository"
          :curr-path="curr_path"
          :branches="branches"
          :tags="tags"
          :curr-refs="curr_refs"
          :branch-tree="branch_tree"
          @into-path="intoPath"
          @change-refs="changeRefs"
        />

        <Revisions
          :page="cFilter.page"
          :limit="cFilter.limit"
          :commit-list="commitList"
          :get-list-sort="getListSort"
          :set-head-id="String(headId ?? '')"
          :set-base-id="String(baseId ?? '')"
          @head-set="headSet"
          @base-set="baseSet"
          @get-commit="getCommit"
          @set-list-sort="setListSort"
          @page-select="pageSelect"
          @page-reset="cFilter.page = 1"
        />
      </template>

      <ViewDiff v-if="route.name === '(저장소) - 차이점 보기'" />

      <ViewFile
        v-else-if="route.name === '(저장소) - 파일 보기'"
        :repo-name="repo?.slug as string"
        :curr-refs="curr_refs"
        @into-path="intoPath"
      />

      <ViewRevision
        v-else-if="route.name === '(저장소) - 리비전 보기'"
        :repo="repo?.pk as number"
        @change-refs="changeRefs"
        @into-path="intoPath"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
