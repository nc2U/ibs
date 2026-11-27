<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { numFormat } from '@/utils/baseMixins'
import { ratioFormat } from '@/utils/areaMixins'
import { TableSecondary } from '@/utils/cssMixins'
import { type SubsSummary, type ContSummary } from '@/store/types/contract'
import { type Project } from '@/store/types/project'

const props = defineProps({
  project: { type: Object as PropType<Project>, default: null },
})

const contractStore = useContract()
const projectDataStore = useProjectData()

const orderGroupList = computed(() => contractStore.orderGroupList)
const subsSummaryList = computed(() => contractStore.subsSummaryList)
const contSummaryList = computed(() => contractStore.contSummaryList)
const unitTypeList = computed(() => projectDataStore.unitTypeList)

const calcRatio = (numerator: number, denominator: number | null | undefined): string => {
  if (!denominator || denominator <= 0) return ratioFormat(0)
  return ratioFormat((numerator / denominator) * 100)
}

const subsNum = (type?: number | null): number => {
  let list = subsSummaryList.value
  if (type !== undefined) {
    list = list.filter((s: SubsSummary) => s.unit_type === type)
  }
  return list.reduce((acc: number, cur: SubsSummary) => acc + (cur.num_cont || 0), 0)
}

const untypedSubsNum = computed(() => subsNum(null))

const contNum = (order: number | null, type?: number): number => {
  let list = contSummaryList.value
  if (order) list = list.filter((c: ContSummary) => c.order_group === order)
  if (type) list = list.filter((c: ContSummary) => c.unit_type === type)
  return list.reduce((acc: number, cur: ContSummary) => acc + (cur.conts_num || 0), 0)
}
</script>

<template>
  <CTable hover responsive bordered class="mt-3">
    <CTableHead class="text-center" :color="TableSecondary">
      <CTableRow align="middle">
        <CTableHeaderCell rowspan="2">프로젝트명</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">타입</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">세대수</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">청약건수</CTableHeaderCell>
        <CTableHeaderCell :colspan="orderGroupList.length === 1 ? 1 : orderGroupList.length + 1">
          계약건수
        </CTableHeaderCell>
        <CTableHeaderCell rowspan="2">잔여세대(실)</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">계약율</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">분양율(청약+계약)</CTableHeaderCell>
      </CTableRow>

      <CTableRow v-if="orderGroupList.length > 1">
        <CTableHeaderCell v-for="order in orderGroupList" :key="order.pk">
          {{ order.name }}
        </CTableHeaderCell>

        <CTableHeaderCell v-if="orderGroupList.length > 1"> 합계</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="props.project">
      <CTableRow v-for="(type, i) in unitTypeList" :key="type.pk ?? i" class="text-end" align="middle">
        <!-- 프로젝트명 -->
        <CTableHeaderCell
          v-if="props.project && i === 0"
          class="text-center"
          :rowspan="unitTypeList.length + (untypedSubsNum > 0 ? 1 : 0)"
        >
          {{ props.project.name }}
        </CTableHeaderCell>
        <!--  타입 -->
        <CTableDataCell class="text-start ps-2">
          <CIcon name="cibDiscover" :style="'color:' + type.color" size="sm" />
          {{ type.name }}
        </CTableDataCell>
        <!--  타입별 세대수 -->
        <CTableDataCell>
          {{ numFormat(type.num_unit as number) }}{{ type.sort === '1' ? '세대' : '실' }}
        </CTableDataCell>
        <!-- 타입별 청약건수-->
        <CTableDataCell>{{ numFormat(subsNum(type.pk)) }}</CTableDataCell>
        <!-- 차수별 타입별 계약건수-->
        <CTableDataCell v-if="orderGroupList.length === 0">-</CTableDataCell>
        <CTableDataCell v-for="order in orderGroupList" v-else :key="order.pk">
          {{ numFormat(contNum(order.pk, type.pk)) }}
        </CTableDataCell>

        <!-- 차수별 계약건수 합계 -->
        <CTableDataCell v-if="orderGroupList.length > 1">
          {{ numFormat(contNum(null, type.pk)) }}
        </CTableDataCell>
        <!--잔여세대-->
        <CTableDataCell>
          {{ numFormat((type.num_unit as number) - contNum(null, type.pk) - subsNum(type.pk)) }}
        </CTableDataCell>
        <!-- 계약율-->
        <CTableDataCell>
          {{ calcRatio(contNum(null, type.pk), type.num_unit) }}
        </CTableDataCell>
        <!-- 분양율(청약+계약)-->
        <CTableDataCell>
          {{ calcRatio(contNum(null, type.pk) + subsNum(type.pk), type.num_unit) }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow v-if="untypedSubsNum > 0" class="text-end" align="middle">
        <CTableHeaderCell v-if="unitTypeList.length === 0" class="text-center">
          {{ props.project.name }}
        </CTableHeaderCell>
        <CTableDataCell class="text-start ps-2 text-medium-emphasis"> 미지정 </CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
        <CTableDataCell>{{ numFormat(untypedSubsNum) }}</CTableDataCell>
        <CTableDataCell v-if="orderGroupList.length === 0">-</CTableDataCell>
        <CTableDataCell v-for="order in orderGroupList" v-else :key="order.pk">-</CTableDataCell>
        <CTableDataCell v-if="orderGroupList.length > 1">-</CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-end" :color="TableSecondary">
        <CTableDataCell class="text-center"> 합계</CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <!-- 타입별 세대수 합계-->
        <CTableDataCell> {{ numFormat(props.project?.num_unit ?? 0) }}세대</CTableDataCell>
        <!-- 청약 건수 타입별 합계-->
        <CTableDataCell>{{ numFormat(subsNum()) }}</CTableDataCell>
        <!--차수별 계약건수 타입별 합계-->
        <CTableDataCell v-if="orderGroupList.length === 0">-</CTableDataCell>
        <CTableDataCell v-for="order in orderGroupList" v-else :key="order.pk">
          {{ numFormat(contNum(order.pk)) }}
        </CTableDataCell>
        <!-- 차수별 타입별 계약건수 총계-->
        <CTableDataCell v-if="orderGroupList.length > 1">
          {{ numFormat(contNum(null)) }}
        </CTableDataCell>
        <!-- 타입별 잔여세대 합계-->
        <CTableDataCell>
          {{ numFormat((props.project?.num_unit ?? 0) - contNum(null) - subsNum()) }}
        </CTableDataCell>
        <!-- 타입별 계약율 합계-->
        <CTableDataCell>
          {{ calcRatio(contNum(null), props.project?.num_unit) }}
        </CTableDataCell>
        <!-- 타입별 분양율(청약+계약) 합계-->
        <CTableDataCell>
          {{ calcRatio(contNum(null) + subsNum(), props.project?.num_unit) }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
