<script lang="ts" setup>
import { onBeforeMount, type PropType, ref, watch } from 'vue'
import { timeFormat } from '@/utils/baseMixins.ts'
import type { Commit } from '@/store/types/work.ts'

const props = defineProps({ commitList: { type: Array as PropType<Commit[]>, default: () => [] } })

watch(
  () => props.commitList,
  newVal => {
    if (newVal.length >= 2) {
      refCommit.value = String(newVal[0].pk)
      comCommit.value = String(newVal[1].pk)
    }
  },
)

const revSort = ref<'latest' | 'all'>('latest')

const refCommit = ref<string>('')
const comCommit = ref<string>('')

const changeRef = (pk: number) => (comCommit.value = String(pk - 1))
const changeCom = (pk: number) => {
  if (Number(refCommit.value) <= pk) refCommit.value = String(pk + 1)
}

onBeforeMount(() => {
  refCommit.value = String(props.commitList.map(c => c.pk)[0])
  comCommit.value = String(props.commitList.map(c => c.pk)[1])
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ revSort === 'all' ? '리비전' : '최근 리비전' }}</h5>
    </CCol>
  </CRow>

  <CRow class="my-5">
    <CCol>
      <v-btn>차이점 보기</v-btn>
    </CCol>
  </CRow>
  <CTable hover responsive striped>
    <colgroup>
      <col style="width: 4%" />
      <col style="width: 2%" />
      <col style="width: 5%" />
      <col style="width: 14%" />
      <col style="width: 16%" />
      <col style="width: 61%" />
    </colgroup>
    <CTableHead>
      <CTableRow class="text-center">
        <CTableHeaderCell>#</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell>일자</CTableHeaderCell>
        <CTableHeaderCell>작성자</CTableHeaderCell>
        <CTableHeaderCell>설명</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="(commit, i) in commitList" :key="commit.pk">
        <CTableDataCell class="text-center">
          <span class="mr-5">{{ commit.pk }}</span>
        </CTableDataCell>
        <CTableDataCell>
          <CFormCheck
            v-if="i !== commitList.length - 1"
            type="radio"
            :id="`${commit.pk}-1`"
            name="refCommit"
            :value="String(commit.pk)"
            v-model="refCommit"
            @change="changeRef(commit.pk)"
          />
        </CTableDataCell>

        <CTableDataCell>
          <CFormCheck
            v-if="i !== 0"
            type="radio"
            :id="`${commit.pk}-2`"
            name="comCommit"
            :value="String(commit.pk)"
            v-model="comCommit"
            @change="changeCom(commit.pk)"
          />
        </CTableDataCell>
        <CTableDataCell class="text-center">{{ timeFormat(commit.date) }}</CTableDataCell>
        <CTableDataCell class="text-center">
          <router-link to="">{{ commit.author }}</router-link>
        </CTableDataCell>
        <CTableDataCell>
          {{ commit.message }}
          <template v-if="commit.issues.length">
            (<span v-for="(issue, i) in commit.issues" :key="issue">
              <template v-if="i > 0">, </template>
              <router-link to="">#{{ issue }} </router-link> </span
            >)
          </template>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CRow class="my-5">
    <CCol>
      <v-btn>차이점 보기</v-btn>
    </CCol>
  </CRow>

  <CRow v-if="revSort === 'latest'">
    <CCol>
      <router-link to="" @click="() => (revSort = 'all')">전체 리비전 보기</router-link>
    </CCol>
  </CRow>
  <CRow v-else> Pagination...</CRow>
</template>
