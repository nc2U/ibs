<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { Commit } from '@/store/types/work_git_repo.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { useRouter } from 'vue-router'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import Pagination from '@/components/Pagination'

const props = defineProps({
  page: { type: Number, required: true },
  limit: { type: Number, required: true },
  commitList: { type: Array as PropType<Commit[]>, default: () => [] },
  getListSort: { type: String as PropType<'latest' | 'all' | 'branch'>, default: 'latest' },
  setHeadId: { type: String, default: '' },
  setBaseId: { type: String, default: '' },
})

watch(
  () => props.commitList,
  newVal => {
    if (newVal.length >= 2) {
      headId.value = String(newVal[0].revision_id)
      baseId.value = String(newVal[1].revision_id)
    }
  },
)

const emit = defineEmits([
  'head-set',
  'base-set',
  'get-list-sort',
  'revision-view',
  'get-commit',
  'get-diff',
  'page-select',
])

watch(
  () => props.getListSort,
  newVal => {
    if (newVal === 'latest') emit('page-select', 1)
  },
)

const commits = computed(() =>
  props.getListSort === 'all' ? props.commitList : props.commitList.slice(0, 10),
)

const baseId = ref<string>('')
watch(baseId, newVal => {
  if (newVal) emit('base-set', Number(newVal))
})
const headId = ref<string>('')
watch(headId, newVal => {
  if (newVal) emit('head-set', Number(newVal))
})

const updateBase = (pk: number) => (baseId.value = String(pk - 1))
const updateHead = (pk: number) => {
  if (Number(headId.value) <= pk) headId.value = String(pk + 1)
}

const getDiff = () => {
  const base = props.commitList.find(c => c.revision_id === Number(baseId.value))?.commit_hash
  const head = props.commitList.find(c => c.revision_id === Number(headId.value))?.commit_hash
  emit('get-diff', { base, head })
}

const gitStore = useGitRepo()
const commitCount = computed<number>(() => gitStore.commitCount)
const commitPages = (page: number) => gitStore.commitPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const assignCommit = (commit: Commit) => gitStore.assignCommit(commit)

const viewRevision = (commit: Commit) => {
  assignCommit(commit)
  emit('revision-view')
}

const router = useRouter()
const issueStore = useIssue()
const goToIssue = async (pk: number) => {
  const issue = await issueStore.fetchIssue(pk)
  await router.push({ name: '(업무) - 보기', params: { projId: issue.project, issueId: issue.pk } })
}

onBeforeMount(() => {
  if (props.commitList.length > 1) {
    headId.value = props.setHeadId || String(props.commitList.map(c => c.revision_id)[0])
    baseId.value = props.setBaseId || String(props.commitList.map(c => c.revision_id)[1])
  }
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ getListSort === 'all' ? '리비전' : '최근 리비전' }}</h5>
    </CCol>
  </CRow>

  <CRow class="my-4">
    <CCol>
      <v-btn
        size="small"
        variant="outlined"
        color="primary"
        :disabled="commitList.length < 2"
        @click="getDiff"
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
            :id="`${commit.pk}-1`"
            name="headId"
            :value="String(commit.revision_id)"
            v-model="headId"
            @change="updateBase(commit.revision_id)"
          />
        </CTableDataCell>

        <CTableDataCell>
          <CFormCheck
            v-if="i !== 0"
            type="radio"
            :id="`${commit.pk}-2`"
            name="baseId"
            :value="String(commit.revision_id)"
            v-model="baseId"
            @change="updateHead(commit.revision_id)"
          />
        </CTableDataCell>
        <CTableDataCell class="text-center">{{ timeFormat(commit.date) }}</CTableDataCell>
        <CTableDataCell class="text-center">{{ commit.author }}</CTableDataCell>
        <CTableDataCell>
          {{ cutString(commit.message, 80) }}
          <template v-if="commit.issues.length">
            (<span v-for="(issue, i) in commit.issues" :key="issue">
              <template v-if="i > 0">, </template>
              <router-link to="" @click="goToIssue(issue)">#{{ issue }}</router-link> </span
            >)
          </template>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CRow class="my-4">
    <CCol>
      <v-btn
        size="small"
        variant="outlined"
        color="primary"
        :disabled="commitList.length < 2"
        @click="getDiff"
      >
        차이점 보기
      </v-btn>
    </CCol>
  </CRow>

  <CRow v-if="getListSort === 'all'">
    <CCol class="d-flex mt-3">
      <Pagination
        :active-page="page"
        :limit="8"
        :pages="commitPages(limit)"
        @active-page-change="pageSelect"
      />
      <CCol class="text-50 ms-3" style="padding-top: 7px">
        ({{ page * limit - limit + 1 }}-{{
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
    <CCol v-if="getListSort === 'latest'">
      <router-link to="" @click="emit('get-list-sort', 'all')">전체 리비전 표시</router-link>
      <!--      |-->
      <!--      <router-link to="" @click="emit('get-list-sort', 'branch')">리비전 보기</router-link>-->
    </CCol>
    <CCol v-else>
      <router-link to="" @click="emit('get-list-sort', 'latest')">최근 리비전 보기</router-link>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
svg {
  border: none;
  overflow: visible !important;
}
</style>
