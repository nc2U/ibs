<script lang="ts" setup>
import { btnSecondary, TableSecondary } from '@/utils/cssMixins.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'

defineProps({
  commits: { type: Array, default: () => [] },
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
          <span class="mr-5">
            <router-link to="" @click="viewRevision(commit)">
              {{ commit.sha.substring(0, 8) }}
            </router-link>
          </span>
        </CTableDataCell>
        <CTableDataCell>
          <CFormCheck
            v-if="i !== commits.length - 1"
            type="radio"
            :id="`head-${commit.sha}`"
            name="headSha"
            :value="commit.sha"
            :model-value="headSha"
            @change="updateBase(commit.parents[0], commit.sha)"
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
            @change="updateHead(commit.sha, commit.children[0])"
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
</template>
