<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { Commit } from '@/store/types/work.ts'
import { useWork } from '@/store/pinia/work.ts'
import { timeFormat } from '@/utils/baseMixins.ts'
import Pagination from '@/components/Pagination'

const props = defineProps({
  page: { type: Number, required: true },
  commitList: { type: Array as PropType<Commit[]>, default: () => [] },
  getListSort: { type: String as PropType<'latest' | 'all'>, default: 'latest' },
  parentHeadPk: { type: String, default: '' },
  parentBasePk: { type: String, default: '' },
})

watch(
  () => props.commitList,
  newVal => {
    if (newVal.length >= 2) {
      headPk.value = String(newVal[0].pk)
      basePk.value = String(newVal[1].pk)
    }
  },
)

const emit = defineEmits(['head-set', 'base-set', 'get-list-sort', 'get-diff', 'page-select'])

watch(
  () => props.getListSort,
  newVal => {
    if (newVal === 'latest') emit('page-select', 1)
  },
)

const commits = computed(() =>
  props.getListSort === 'all' ? props.commitList : props.commitList.slice(0, 10),
)

const headPk = ref<string>('')
watch(headPk, newVal => {
  if (newVal) emit('head-set', Number(newVal))
})
const basePk = ref<string>('')
watch(basePk, newVal => {
  if (newVal) emit('base-set', Number(newVal))
})

const updateBase = (pk: number) => (basePk.value = String(pk - 1))
const updateHead = (pk: number) => {
  if (Number(headPk.value) <= pk) headPk.value = String(pk + 1)
}

const getDiff = () => emit('get-diff', false)

const workStore = useWork()
const commitPages = (page: number) => workStore.commitPages(page)
const pageSelect = (page: number) => emit('page-select', page)

onBeforeMount(() => {
  headPk.value = props.parentHeadPk
    ? props.parentHeadPk
    : String(props.commitList.map(c => c.pk)[0])
  basePk.value = props.parentBasePk
    ? props.parentBasePk
    : String(props.commitList.map(c => c.pk)[1])
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
      <CTableRow v-for="(commit, i) in commits" :key="commit.pk">
        <CTableDataCell class="text-center">
          <span class="mr-5">{{ commit.pk }}</span>
        </CTableDataCell>
        <CTableDataCell>
          <CFormCheck
            v-if="i !== commits.length - 1"
            type="radio"
            :id="`${commit.pk}-1`"
            name="headPk"
            :value="String(commit.pk)"
            v-model="headPk"
            @change="updateBase(commit.pk)"
          />
        </CTableDataCell>

        <CTableDataCell>
          <CFormCheck
            v-if="i !== 0"
            type="radio"
            :id="`${commit.pk}-2`"
            name="basePk"
            :value="String(commit.pk)"
            v-model="basePk"
            @change="updateHead(commit.pk)"
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
    <Pagination
      :active-page="page"
      :limit="8"
      :pages="commitPages(25)"
      @active-page-change="pageSelect"
    />
  </CRow>

  <CRow>
    <CCol v-if="getListSort === 'latest'">
      <router-link to="" @click="emit('get-list-sort', 'all')">전체 리비전 보기</router-link>
    </CCol>
    <CCol v-else>
      <router-link to="" @click="emit('get-list-sort', 'latest')">최근 리비전 보기</router-link>
    </CCol>
  </CRow>
</template>
