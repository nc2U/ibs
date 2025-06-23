<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUnmount, ref } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import { useRoute, useRouter } from 'vue-router'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import type { DiffApi } from '@/store/types/work_git_repo.ts'
import 'diff2html/bundles/css/diff2html.min.css'
import Loading from '@/components/Loading/Index.vue'
import Diff from './atomics/Diff.vue'

const [route, router] = [useRoute(), useRouter()]

const gitStore = useGitRepo()
const gitDiff = computed<DiffApi>(() => gitStore.gitDiff)

const repo = computed(() => Number(route.params.repoId))
const base = computed(() => route.params.base as string)
const head = computed(() => route.params.head as string)

const getDiff = async () => {
  const diff_hash = `?base=${base.value}&head=${head.value}`
  await gitStore.fetchGitDiff(repo.value as number, diff_hash)
}

const getBack = () => {
  router.push({ name: '(저장소)' })
  gitStore.removeGitDiff()
}

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await getDiff()
  loading.value = false
})
onBeforeUnmount(gitStore.removeGitDiff)
</script>

<template>
  <Loading v-model:active="loading" />
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ base.substring(0, 8) }} : {{ head.substring(0, 8) }}</h5>
    </CCol>
  </CRow>

  <CRow class="mb-3">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">
        목록으로
      </v-btn>
    </CCol>
  </CRow>

  <Diff :git-diff="gitDiff" />

  <CRow class="mt-3">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">
        목록으로
      </v-btn>
    </CCol>
  </CRow>
</template>
