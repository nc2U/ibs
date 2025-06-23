<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { btnSecondary, TableSecondary } from '@/utils/cssMixins.ts'
import type { Commit, Repository } from '@/store/types/work_git_repo.ts'
import { useRouter } from 'vue-router'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import Pagination from '@/components/Pagination'

const router = useRouter()

const props = defineProps({
  repo: { type: Number, required: true },
  page: { type: Number, required: true },
  limit: { type: Number, required: true },
})

const emit = defineEmits(['get-commit', 'page-select', 'page-reset'])

const listSort = ref<'latest' | 'all' | 'branch'>('latest')
watch(
  () => listSort.value,
  newVal => {
    if (newVal === 'latest') emit('page-select', 1)
  },
)

const initSha = (head: string, base: string, cList: any[]) => {
  const searchSha = (sha: string, shaList: string[], index: 0 | 1) =>
    shaList.includes(sha) ? sha : shaList[index]

  setHeadSha(
    searchSha(
      head,
      cList.map(c => c.commit_hash),
      0,
    ),
  )
  setBaseSha(
    searchSha(
      base,
      cList.map(c => c.commit_hash),
      1,
    ),
  )
}

const gitStore = useGitRepo()
const repo = computed(() => (gitStore.repository as Repository)?.pk)
const commitCount = computed(() => gitStore.commitCount)
const commitList = computed<Commit[]>(() => gitStore.commitList)
watch(commitList, newVal => {
  if (newVal.length > 1) initSha(headSha.value, baseSha.value, newVal)
})
const commits = computed<Commit[]>(() =>
  listSort.value === 'all' ? commitList.value : commitList.value.slice(0, 10),
)

const baseSha = computed(() => gitStore.baseSha)
const headSha = computed(() => gitStore.headSha)

const commitPages = (page: number) => gitStore.commitPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const assignCommit = (commit: Commit) => gitStore.assignCommit(commit)
const setBaseSha = (sha: string) => gitStore.setBaseSha(sha)
const setHeadSha = (sha: string) => gitStore.setHeadSha(sha)

const updateBase = (base: string, head) => {
  setBaseSha(base)
  setHeadSha(head)
}

const commitMap = computed(() => {
  const map = new Map<string, Commit>()
  commits.value.forEach(commit => map.set(commit.commit_hash, commit))
  return map
})

const isDescendant = (descendantSha: string, ancestorSha: string): boolean => {
  if (descendantSha === ancestorSha) return false

  const visited = new Set<string>()
  const stack = [ancestorSha]

  while (stack.length) {
    const sha = stack.pop()!
    if (sha === descendantSha) return true // 자손 발견 → 변경 X
    if (!visited.has(sha)) {
      visited.add(sha)
      const node = commitMap.value.get(sha)
      if (node) {
        stack.push(...node.children)
      }
    }
  }
  return false // 자손 아님 → 변경 허용
}

const updateHead = (base: string, head: string) => {
  setBaseSha(base)

  const currentHead = headSha.value
  if (!currentHead || head === currentHead) {
    setHeadSha(head) // headSha가 없거나 cSha가 headSha와 동일 → 무조건 설정
    return
  }
  if (isDescendant(currentHead, head)) return // head가 cSha의 자손이면 변경 금지
  setHeadSha(head) // head 가 head 보다 조상이거나 아무 관련 없어도 → head 갱신
}

const viewRevision = (commit: Commit) => {
  assignCommit(commit)
  emit('page-select')
  router.push({
    name: '(저장소) - 리비전 보기',
    params: { repoId: repo.value, sha: commit.commit_hash },
  })
}

onBeforeMount(() => {
  if (commits.value.length > 1) initSha(headSha.value, baseSha.value, commitList.value)
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ listSort === 'all' ? '리비전' : '최근 리비전' }}</h5>
    </CCol>
  </CRow>

  <CRow class="my-3">
    <CCol>
      <v-btn
        variant="outlined"
        :color="btnSecondary"
        size="small"
        :disabled="commitList.length < 2"
        @click="
          router.push({
            name: '(저장소) - 차이점 보기',
            params: { repoId: repo, base: baseSha, head: headSha },
          })
        "
      >
        차이점 보기
      </v-btn>
    </CCol>
  </CRow>
  <CTable hover responsive striped small>
    <colgroup>
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 2%" />
      <col style="width: 5%" />
      <col style="width: 15%" />
      <col style="width: 16%" />
      <col style="width: 50%" />
    </colgroup>
    <CTableHead>
      <CTableRow class="text-center" :color="TableSecondary">
        <CTableHeaderCell colspan="2">#</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>일자</CTableHeaderCell>
        <CTableHeaderCell>작성자</CTableHeaderCell>
        <CTableHeaderCell>설명</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="(commit, i) in commits" :key="i">
        <CTableDataCell></CTableDataCell>
        <CTableDataCell class="text-center">
          <span class="mr-5">
            <router-link to="" @click="viewRevision(commit)">
              {{ commit.commit_hash.substring(0, 8) }}
            </router-link>
          </span>
        </CTableDataCell>
        <CTableDataCell>
          <CFormCheck
            v-if="i !== commits.length - 1"
            type="radio"
            :id="`head-${commit.commit_hash}`"
            name="headSha"
            :value="commit.commit_hash"
            :model-value="headSha"
            @change="updateBase(commit.parents[0], commit.commit_hash)"
          />
        </CTableDataCell>

        <CTableDataCell>
          <CFormCheck
            v-if="i !== 0"
            type="radio"
            :id="`base-${commit.commit_hash}`"
            name="baseSha"
            :value="commit.commit_hash"
            :model-value="baseSha"
            @change="updateHead(commit.commit_hash, commit.children[0])"
          />
        </CTableDataCell>
        <CTableDataCell class="text-center">{{ timeFormat(commit.date) }}</CTableDataCell>
        <CTableDataCell class="text-center">{{ commit.author }}</CTableDataCell>
        <CTableDataCell>
          {{ cutString(commit.message, 80) }}
          <template v-if="commit.issues.length">
            (<span v-for="(issue, i) in commit.issues" :key="i">
              <template v-if="i > 0">, </template>
              <router-link
                to=""
                @click="
                  router.push({
                    name: '(업무) - 보기',
                    params: { projId: issue.project, issueId: issue.pk },
                  })
                "
              >
                #{{ issue.pk }}
              </router-link> </span
            >)
          </template>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CRow class="my-3">
    <CCol>
      <v-btn
        variant="outlined"
        :color="btnSecondary"
        size="small"
        :disabled="commitList.length < 2"
        @click="
          router.push({
            name: '(저장소) - 차이점 보기',
            params: { repoId: repo, base: baseSha, head: headSha },
          })
        "
      >
        차이점 보기
      </v-btn>
    </CCol>
  </CRow>

  <CRow v-if="listSort === 'all'">
    <CCol class="d-flex mt-3">
      <Pagination
        :active-page="page"
        :limit="8"
        :pages="commitPages(limit)"
        @active-page-change="pageSelect"
      />
      <CCol class="text-50 ms-3" style="padding-top: 7px">
        ({{ page || 1 * limit - limit + 1 }}-{{
          limit * page < commitCount ? limit * page : commitCount
        }}/{{ commitCount }}) 페이지당 줄수:
        <b v-if="limit === 25">25</b>
        <span v-else><router-link to="" @click="emit('get-commit', 25)">25</router-link> </span>,
        <b v-if="limit === 50">50</b>
        <span v-else><router-link to="" @click="emit('get-commit', 50)">50</router-link> </span>,
        <b v-if="limit === 100">100</b>
        <span v-else><router-link to="" @click="emit('get-commit', 100)">100</router-link> </span>
      </CCol>
    </CCol>
  </CRow>

  <CRow>
    <CCol v-if="listSort === 'latest'">
      <router-link to="" @click="listSort = 'all'">전체 리비전 표시</router-link>
      <!--      |-->
      <!--      <router-link to="" @click="listSort = 'branch'">리비전 보기</router-link>-->
    </CCol>
    <CCol v-else>
      <router-link to="" @click="listSort = 'latest'">최근 리비전 보기</router-link>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
svg {
  border: none;
  overflow: visible !important;
}
</style>
