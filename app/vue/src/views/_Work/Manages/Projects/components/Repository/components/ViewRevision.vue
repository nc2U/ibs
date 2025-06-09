<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { Commit } from '@/store/types/work_github.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import { bgLight, btnLight } from '@/utils/cssMixins.ts'
import RevisionMenu from './HeaderMenu/RevisionMenu.vue'
import PathTree from './atomics/PathTree.vue'
import Diff from './atomics/Diff.vue'

const props = defineProps({
  repo: { type: Number, required: true },
  commit: { type: Object as PropType<Commit>, required: true },
})

const emit = defineEmits(['goto-back', 'revision-view'])

const tabKey = ref(1)

const gitStore = useGithub()
const gitDiff = computed(() => gitStore.gitDiff)
watch(
  () => gitDiff.value,
  nVal => {
    if (!nVal.diff) tabKey.value = 1
  },
)
const fetchGitDiff = (repo, diff_hash: string) => gitStore.fetchGitDiff(repo, diff_hash)
const fetchCommitBySha = (sha: string) => gitStore.fetchCommitBySha(sha)

const revisionView = async (hash: string) => emit('revision-view', await fetchCommitBySha(hash))

watch(
  () => props.commit,
  nVal => {
    if (nVal) {
      const diff_hash = `?base=${nVal.parents[0]}&head=${nVal.commit_hash}`
      fetchGitDiff(props.repo, diff_hash)
    }
  },
)

onBeforeMount(() => {
  if (props.commit) {
    const diff_hash = `?base=${props.commit.parents[0]}&head=${props.commit.commit_hash}`
    fetchGitDiff(props.repo, diff_hash)
  }
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ commit.commit_hash.substring(0, 8) }}</h5>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      Austin Kho 이(가)
      <router-link to="">{{ elapsedTime(commit.date) }}</router-link>
      에 추가함
    </CCol>

    <CCol>
      <RevisionMenu />
    </CCol>
  </CRow>

  <v-divider class="mt-0" />

  <CRow class="pl-5">
    <CCol>
      <ul class="pl-5">
        <li><b>ID</b> {{ commit.commit_hash }}</li>
        <li v-if="commit.parents.length">
          <b>상위 </b>
          <span v-for="(hash, i) in commit.parents" :key="hash">
            <router-link to="" @click="revisionView(hash)">
              {{ hash.substring(0, 8) }}
            </router-link>
            <span v-if="i < commit.parents.length - 1">, </span>
          </span>
        </li>
        <li v-if="commit.children.length">
          <b>하위 </b>
          <span v-for="(hash, i) in commit.children" :key="hash">
            <router-link to="" @click="revisionView(hash)">
              {{ hash.substring(0, 8) }}
            </router-link>
            <span v-if="i < commit.children.length - 1">, </span>
          </span>
        </li>
      </ul>
    </CCol>
  </CRow>

  <CRow class="mb-5">
    <CCol>{{ commit.message }}</CCol>
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

    <CNavItem v-if="gitDiff.diff">
      <CNavLink href="javascript:void(0);" :active="tabKey === 2" @click="tabKey = 2">
        차이점보기
      </CNavLink>
    </CNavItem>
  </CNav>

  <PathTree v-if="tabKey === 1" :git-diff="gitDiff" />
  <Diff v-if="tabKey === 2" :git-diff="gitDiff" />

  <v-btn @click="emit('goto-back')" :color="btnLight" size="small" class="my-5">목록으로</v-btn>
</template>
