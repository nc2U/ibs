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

const subsNum = (type?: number | null) => {
  // 청약 수
  let subs: SubsSummary[] | number[] = subsSummaryList.value
  if (type !== undefined) {
    subs = subs.filter((s: SubsSummary) => s.unit_type === type)
  }
  subs = subs.map((s: SubsSummary) => s.num_cont)
  return subs.reduce((o: number, n: number) => o + n, 0)
}

const untypedSubsNum = computed(() => subsNum(null))

const contNum = (order: number | null, type?: number) => {
  // 계약 수
  let cont: ContSummary[] | number[] = contSummaryList.value
  cont = order ? cont.filter((c: ContSummary) => c.order_group === order) : cont
  cont = type ? cont.filter((c: ContSummary) => c.unit_type === type) : cont
  cont = cont.map((c: ContSummary) => c.conts_num)
  return cont.reduce((p: number, c: number) => p + c, 0)
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
      <CTableRow v-for="(type, i) in unitTypeList" :key="i" class="text-right" align="middle">
        <!-- 프로젝트명 -->
        <CTableHeaderCell
          v-if="props.project && i === 0"
          class="text-center"
          :rowspan="unitTypeList.length + (untypedSubsNum > 0 ? 1 : 0)"
        >
          {{ props.project.name }}
        </CTableHeaderCell>
        <!--  타입 -->
        <CTableDataCell class="text-left pl-2">
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
        <CTableDataCell v-for="order in orderGroupList" :key="order.pk">
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
          {{ ratioFormat((contNum(null, type.pk) / (type?.num_unit as number)) * 100) }}
        </CTableDataCell>
        <!-- 분양율(청약+계약)-->
        <CTableDataCell>
          {{
            ratioFormat(
              ((contNum(null, type.pk) + subsNum(type.pk)) / (type.num_unit as number)) * 100,
            )
          }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow v-if="untypedSubsNum > 0" class="text-right" align="middle">
        <CTableHeaderCell v-if="unitTypeList.length === 0" class="text-center">
          {{ props.project.name }}
        </CTableHeaderCell>
        <CTableDataCell class="text-left pl-2 text-medium-emphasis"> 미지정 </CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
        <CTableDataCell>{{ numFormat(untypedSubsNum) }}</CTableDataCell>
        <CTableDataCell v-for="order in orderGroupList" :key="order.pk">-</CTableDataCell>
        <CTableDataCell v-if="orderGroupList.length > 1">-</CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
        <CTableDataCell>-</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-right" :color="TableSecondary">
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
          {{ ratioFormat((contNum(null) / (props.project?.num_unit ?? 1)) * 100) }}
        </CTableDataCell>
        <!-- 타입별 분양율(청약+계약) 합계-->
        <CTableDataCell>
          {{ ratioFormat(((contNum(null) + subsNum()) / (props.project?.num_unit ?? 1)) * 100) }}
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
