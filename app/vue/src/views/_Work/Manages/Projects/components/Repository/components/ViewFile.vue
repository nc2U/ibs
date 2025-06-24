<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { btnSecondary } from '@/utils/cssMixins.ts'
import Loading from '@/components/Loading/Index.vue'
import FileContent from './atomics/FileContent.vue'

defineProps({
  repoName: { type: String, required: true },
  currRefs: { type: String, required: true },
})

const emit = defineEmits(['into-path'])

const fileData = ref()

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
  fileData.value = await fetchFileView(repoId.value, path.value as string, sha.value)
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

  <CRow class="mb-3 pl-2">
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

  <CNav variant="tabs" class="mx-2">
    <CNavItem>
      <CNavLink href="#" active>보기</CNavLink>
    </CNavItem>
    <CNavItem>
      <CNavLink href="#">이력</CNavLink>
    </CNavItem>
    <CNavItem>
      <CNavLink href="#" disabled>이력해설</CNavLink>
    </CNavItem>
  </CNav>

  <FileContent :file-data="fileData" />

  <CRow class="mb-5 pl-2">
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
