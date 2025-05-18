<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import type { Commit } from '@/store/types/work.ts'
import 'diff2html/bundles/css/diff2html.min.css'
import Diff2Html from 'diff2html'

const props = defineProps({
  headCommit: { type: Object as PropType<Commit>, required: true },
  baseCommit: { type: Object as PropType<Commit>, required: true },
})

const emit = defineEmits(['get-back'])

const viewSort = ref<'1' | '2'>('1')

const getBack = () => emit('get-back')

// const diffContainer = ref<HTMLElement | null>(null)
const outputFormat = ref<'line-by-line' | 'side-by-side'>('side-by-side')
//
// // 예시 API 엔드포인트 (공개 저장소에서 token 없이 사용 가능, rate limit 주의)
// const owner = 'octocat'
// const repo = 'Hello-World'
// const base = '7fd1a60b01f91b314f59955a4e4d236a3a26c71d'
// const head = 'f5f3699d9a84c3e9bce0c1134efb7f3d5b1a19c9'
//
// const fetchDiff = async () => {
//   const res = await fetch(
//     `https://api.github.com/repos/${owner}/${repo}/compare/${base}...${head}`,
//     {
//       headers: {
//         Accept: 'application/vnd.github.v3+json',
//       },
//     },
//   )
//   const data = await res.json()
//   const patches =
//     data.files
//       ?.map((f: any) => f.patch)
//       .filter(Boolean)
//       .join('\n') || ''
//
//   if (diffContainer.value) {
//     diffContainer.value.innerHTML = Diff2Html.html(patches, {
//       drawFileList: true,
//       matching: 'lines',
//       outputFormat: outputFormat.value,
//     })
//   }
// }
//
// onMounted(fetchDiff)
//
// watch(outputFormat, fetchDiff)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ headCommit.pk }} : {{ baseCommit.pk }}</h5>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      차이접 보기 :
      <CFormCheck
        type="radio"
        name="viewChoice"
        id="c1"
        label="두줄로"
        value="1"
        inline
        v-model="viewSort"
      />
      <CFormCheck
        type="radio"
        name="viewChoice"
        id="c2"
        label="한줄로"
        value="2"
        inline
        v-model="viewSort"
      />
    </CCol>
  </CRow>

  <div>
    <div class="mb-2">
      <label>Output Format: </label>
      <select v-model="outputFormat">
        <option value="line-by-line">Line by Line</option>
        <option value="side-by-side">Side by Side</option>
      </select>
    </div>

    <div ref="diffContainer" class="diff-container"></div>
  </div>

  <!--  <CRow>-->
  <!--    <CCol>-->
  <!--      <CTable>-->
  <!--        <colgroup>-->
  <!--          <col style="width: 2%" />-->
  <!--          <col v-if="viewSort === '2'" style="width: 48%" />-->
  <!--          <col style="width: 2%" />-->
  <!--          <col :style="{ width: viewSort === '1' ? 96 : 48 + '%' }" />-->
  <!--        </colgroup>-->
  <!--        <CTableHead>-->
  <!--          <CTableRow>-->
  <!--            <CTableHeaderCell :colspan="viewSort === '1' ? 3 : 4">-->
  <!--              {{ 'a' }}-->
  <!--            </CTableHeaderCell>-->
  <!--          </CTableRow>-->
  <!--        </CTableHead>-->
  <!--        <CTableBody>-->
  <!--          <CTableRow>-->
  <!--            <CTableDataCell>{{ headCommit }}</CTableDataCell>-->
  <!--            <CTableDataCell v-if="viewSort === '2'">asdf</CTableDataCell>-->
  <!--            <CTableDataCell>{{ baseCommit }}</CTableDataCell>-->
  <!--            <CTableDataCell>asdf</CTableDataCell>-->
  <!--          </CTableRow>-->
  <!--        </CTableBody>-->
  <!--      </CTable>-->
  <!--    </CCol>-->
  <!--  </CRow>-->

  <CRow class="mt-3">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>
</template>

<style scoped>
.diff-container {
  overflow-x: auto;
  border: 1px solid #ccc;
  font-size: 14px;
}
</style>
