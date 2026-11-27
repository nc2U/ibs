<script setup lang="ts">
import { computed, onBeforeMount, type PropType, reactive, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms'
import type { SimpleSite, SiteOwner } from '@/store/types/project'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({
  owner: { type: Object as PropType<SiteOwner>, required: true },
  site: { type: Object as PropType<SimpleSite>, required: true },
  index: { type: Number, default: 0 },
  isReturned: { type: Boolean, default: false },
  isHighlight: { type: Boolean, default: false },
})

const emit = defineEmits(['show-detail', 'relation-patch'])

const { can, PERM } = usePerms()
const canSiteUpdate = computed(() => can(PERM.SITE_UPDATE))

type semiRel = {
  pk: number | null
  site: number | null
  ownership_ratio: number | string
  owned_area: number | string
  acquisition_date: null | string
}

const toNumOrNull = (val: number | string | null | undefined): number | null =>
  val === null || val === undefined || val === '' ? null : Number(val)

const form = reactive<semiRel>({
  pk: null,
  site: null,
  ownership_ratio: '',
  owned_area: '',
  acquisition_date: null,
})
const calcArea = ref(0)

watch(form, val => {
  if (val.owned_area !== '' && val.owned_area !== null && val.owned_area !== undefined) {
    calcArea.value = Number(val.owned_area) * 0.3025
  } else calcArea.value = 0
})

const formsCheck = computed(() => {
  const a = form.pk === props.site.pk
  const b = form.site === props.site.site
  const c = toNumOrNull(form.ownership_ratio) === toNumOrNull(props.site.ownership_ratio)
  const d = toNumOrNull(form.owned_area) === toNumOrNull(props.site.owned_area)
  const e = form.acquisition_date === props.site.acquisition_date

  return a && b && c && d && e
})

const sitesNum = computed(() => props.owner.sites.length)

const showDetail = () => emit('show-detail')
const relationPatch = (payload: semiRel) => emit('relation-patch', payload)
const relPatch = () => {
  if (!canSiteUpdate.value || formsCheck.value) return
  relationPatch(form)
}

const dataSetup = () => {
  if (props.site) {
    form.pk = props.site.pk
    form.site = props.site.site
    form.ownership_ratio = props.site.ownership_ratio
    form.owned_area = props.site.owned_area
    form.acquisition_date = props.site.acquisition_date
    calcArea.value = (Number(props.site.owned_area) || 0) * 0.3025
  }
}

watch(() => props.site, dataSetup, { deep: true })

onBeforeMount(() => dataSetup())
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
  <CTableDataCell class="text-start">
    {{ site.__str__ }}
  </CTableDataCell>
  <CTableDataCell class="text-end">
    <CFormInput
      v-model.number="form.ownership_ratio"
      type="number"
      min="0"
      step="0.0000001"
      placeholder="소유지분(%)"
      :disabled="!canSiteUpdate"
      @keydown.enter.prevent="relPatch"
    />
  </CTableDataCell>
  <CTableDataCell class="text-end">
    <CFormInput
      v-model.number="form.owned_area"
      type="number"
      min="0"
      step="0.0000001"
      placeholder="면적(제곱미터)"
      :disabled="!canSiteUpdate"
      @keydown.enter.prevent="relPatch"
    />
  </CTableDataCell>
  <CTableDataCell class="text-end" color="warning">
    {{ numFormat(calcArea, 4) }}
  </CTableDataCell>
  <CTableDataCell class="text-start">
    <DatePicker
      v-model="form.acquisition_date"
      maxlength="10"
      placeholder="소유권 취득일"
      :disabled="!canSiteUpdate"
      @keydown.enter.prevent="relPatch"
    />
  </CTableDataCell>
  <CTableDataCell
    v-if="index === 0"
    :rowspan="sitesNum"
    :class="{ 'bg-success': owner.use_consent }"
  >
    {{ owner.use_consent ? '동의' : '' }}
  </CTableDataCell>
  <CTableDataCell v-if="canSiteUpdate">
    <v-btn color="success" size="x-small" :disabled="formsCheck" @click="relPatch">적용</v-btn>
  </CTableDataCell>
  <CTableDataCell v-if="index === 0 && canSiteUpdate" :rowspan="sitesNum">
    <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
  </CTableDataCell>
</template>
