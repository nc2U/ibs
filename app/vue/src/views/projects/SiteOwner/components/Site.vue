<script setup lang="ts">
import { computed, onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { write_project_site } from '@/utils/pageAuth'
import { type SiteOwner, type SimpleSite } from '@/store/types/project'
import DatePicker from '@/components/DatePicker/index.vue'

const props = defineProps({
  owner: { type: Object as PropType<SiteOwner>, required: true },
  site: { type: Object as PropType<SimpleSite>, required: true },
  index: { type: Number, default: 0 },
})

const emit = defineEmits(['show-detail', 'relation-patch'])

type semiRel = {
  pk: number | null
  site: number | null
  ownership_ratio: string
  owned_area: string
  acquisition_date: null | string
}

const form = reactive<semiRel>({
  pk: null,
  site: null,
  ownership_ratio: '',
  owned_area: '',
  acquisition_date: null,
})
const calcArea = ref(0)

watch(form, val => {
  if (val.owned_area) calcArea.value = Number(val.owned_area) * 0.3025
  else calcArea.value = 0
})

const formsCheck = computed(() => {
  const a = form.pk === props.site.pk
  const b = form.site === props.site.site
  const c = form.ownership_ratio === props.site.ownership_ratio
  const d = form.owned_area === props.site.owned_area
  const e = form.acquisition_date === props.site.acquisition_date

  return a && b && c && d && e
})

const sitesNum = computed(() => props.owner.sites.length)

const showDetail = () => emit('show-detail')
const relationPatch = (payload: semiRel) => emit('relation-patch', payload)
const relPatch = () => relationPatch(form)

onBeforeMount(() => {
  if (props.site) {
    form.pk = props.site.pk
    form.site = props.site.site
    form.ownership_ratio = props.site.ownership_ratio
    form.owned_area = props.site.owned_area
    form.acquisition_date = props.site.acquisition_date
    calcArea.value = (Number(props.site.owned_area) || 0) * 0.3025
  }
})
</script>

<template>
  <CTableDataCell v-if="index === 0" :rowspan="sitesNum">
    {{ owner.own_sort_desc }}
  </CTableDataCell>
  <CTableDataCell v-if="index === 0" :rowspan="sitesNum">
    {{ owner.owner }}
  </CTableDataCell>
  <CTableDataCell v-if="index === 0" :rowspan="sitesNum">
    {{ owner.date_of_birth }}
  </CTableDataCell>
  <CTableDataCell v-if="index === 0" :rowspan="sitesNum">
    {{ owner.phone1 }}
  </CTableDataCell>
  <CTableDataCell class="text-left">
    {{ site.__str__ }}
  </CTableDataCell>
  <CTableDataCell class="text-right">
    <CFormInput
      v-model.number="form.ownership_ratio"
      type="number"
      min="0"
      step="0.0000001"
      placeholder="소유지분(%)"
      @keydown.enter="relPatch"
    />
  </CTableDataCell>
  <CTableDataCell class="text-right">
    <CFormInput
      v-model.number="form.owned_area"
      type="number"
      min="0"
      step="0.0000001"
      placeholder="면적(제곱미터)"
      @keydown.enter="relPatch"
    />
  </CTableDataCell>
  <CTableDataCell class="text-right" color="warning">
    {{ numFormat(calcArea, 4) }}
  </CTableDataCell>
  <CTableDataCell class="text-left">
    <DatePicker
      v-model="form.acquisition_date"
      type="number"
      maxlength="10"
      placeholder="소유권 취득일"
      @keydown.enter="relPatch"
    />
  </CTableDataCell>
  <CTableDataCell :class="{ 'bg-success': owner.use_consent }">
    {{ owner.use_consent ? '동의' : '' }}
  </CTableDataCell>
  <CTableDataCell v-if="write_project_site">
    <v-btn color="success" size="small" :disabled="formsCheck" @click="relPatch"> 적용</v-btn>
  </CTableDataCell>
  <CTableDataCell v-if="index === 0 && write_project_site" :rowspan="sitesNum">
    <v-btn color="info" size="small" @click="showDetail"> 확인</v-btn>
  </CTableDataCell>
</template>
