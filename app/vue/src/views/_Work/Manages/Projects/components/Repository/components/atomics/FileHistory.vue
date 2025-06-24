<script lang="ts" setup>
import { computed, onBeforeMount, watch } from 'vue'
import { btnSecondary, TableSecondary } from '@/utils/cssMixins.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { onBeforeRouteLeave } from 'vue-router'

const props = defineProps({
  commits: { type: Array, default: () => [] },
})

watch(
  () => props.commits,
  newVal => {
    if (newVal.length > 1) initSha(headSha.value, baseSha.value, newVal)
  },
)

const gitStore = useGitRepo()
const baseSha = computed(() => gitStore.baseSha)
const headSha = computed(() => gitStore.headSha)
const setBaseSha = (sha: string) => gitStore.setBaseSha(sha)
const setHeadSha = (sha: string) => gitStore.setHeadSha(sha)

const initSha = (head: string, base: string, cList: any[]) => {
  const searchSha = (sha: string, shaList: string[], index: 0 | 1) =>
    shaList.includes(sha) ? sha : shaList[index]

  setHeadSha(
    searchSha(
      head,
      cList.map(c => c.sha),
      0,
    ),
  )
  setBaseSha(
    searchSha(
      base,
      cList.map(c => c.sha),
      1,
    ),
  )
}

const updateBase = (base: string, head) => {
  setBaseSha(base)
  setHeadSha(head)
}

const updateHead = (base: string, head?: string) => {
  setBaseSha(base)
  if (head) setHeadSha(head)
}

onBeforeMount(() => {
  if (props.commits.length > 1) initSha(headSha.value, baseSha.value, props.commits)
})

onBeforeRouteLeave(() => {
  setBaseSha('')
  setHeadSha('')
})
</script>

<template>
  <CRow class="my-3 pl-2">
    <CCol>
      <v-btn
        variant="outlined"
        :color="btnSecondary"
        size="small"
        :disabled="commits.length < 2"
        @click="
          $router.push({
            name: '(저장소) - 차이점 보기',
            params: { base: baseSha, head: headSha },
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
      <col style="width: 2%" />
      <col style="width: 5%" />
      <col style="width: 15%" />
      <col style="width: 16%" />
      <col style="width: 50%" />
    </colgroup>
    <CTableHead>
      <CTableRow class="text-center" :color="TableSecondary">
        <CTableHeaderCell>#</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>일자</CTableHeaderCell>
        <CTableHeaderCell>작성자</CTableHeaderCell>
        <CTableHeaderCell>설명</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="(commit, i) in commits" :key="i">
        <CTableDataCell class="text-center">
          <router-link to="" @click="viewRevision(commit)">
            {{ commit.sha.substring(0, 8) }}
          </router-link>
        </CTableDataCell>
        <CTableDataCell>
          <CFormCheck
            v-if="i !== commits.length - 1"
            type="radio"
            :id="`head-${commit.sha}`"
            name="headSha"
            :value="commit.sha"
            :model-value="headSha"
            @change="updateBase(commits[i + 1].sha, commit.sha)"
          />
        </CTableDataCell>

        <CTableDataCell>
          <CFormCheck
            v-if="i !== 0"
            type="radio"
            :id="`base-${commit.sha}`"
            name="baseSha"
            :value="commit.sha"
            :model-value="baseSha"
            @change="
              updateHead(commit.commit_hash, headSha === commit.sha ? commits[i - 1].sha : null)
            "
          />
        </CTableDataCell>
        <CTableDataCell class="text-center">{{ timeFormat(commit.date) }}</CTableDataCell>
        <CTableDataCell class="text-center">{{ commit.author }}</CTableDataCell>
        <CTableDataCell>
          {{ cutString(commit.message, 80) }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CRow class="my-3 pl-2">
    <CCol>
      <v-btn
        variant="outlined"
        :color="btnSecondary"
        size="small"
        :disabled="commits.length < 2"
        @click="
          $router.push({
            name: '(저장소) - 차이점 보기',
            params: { base: baseSha, head: headSha },
          })
        "
      >
        차이점 보기
      </v-btn>
    </CCol>
  </CRow>
</template>
