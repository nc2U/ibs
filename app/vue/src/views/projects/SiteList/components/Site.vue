<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { type Site } from '@/store/types/project'
import { cutString, numFormat } from '@/utils/baseMixins'
import { write_project_site } from '@/utils/pageAuth'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteForm from './SiteForm.vue'

const props = defineProps({
  site: { type: Object as PropType<Site>, required: true },
  isReturned: { type: Boolean },
  isHighlight: { type: Boolean, default: false },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const updateFormModal = ref()

const owners = computed(() => (props.site.owners ? props.site.owners.map(o => o.owner) : []))

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: Site) => emit('multi-submit', payload)
const onDelete = (payload: { pk: number; project: number }) => emit('on-delete', payload)
</script>

<template>
  <CTableRow
    class="text-center"
    :class="{ 'table-warning': props.isHighlight }"
    :data-site-id="site.pk"
  >
    <CTableDataCell>{{ site.order }}</CTableDataCell>
    <CTableDataCell>
      {{ site.district }}
    </CTableDataCell>
    <CTableDataCell>
      {{ site.lot_number }}
    </CTableDataCell>
    <CTableDataCell>
      {{ site.site_purpose }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(site.official_area, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-right" color="warning">
      {{ numFormat((Number(site.official_area) || 0) * 0.3025, 2) }}
    </CTableDataCell>
    <CTableDataCell v-if="isReturned" class="text-right">
      {{ numFormat(site.returned_area as number, 2) }}
    </CTableDataCell>
    <CTableDataCell v-if="isReturned" class="text-right" color="warning">
      {{ numFormat((site.returned_area as number) * 0.3025, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      {{ owners.length ? cutString(owners.join(', '), 48) : '' }}
      <v-tooltip v-if="owners.length" activator="parent" location="top">
        {{ owners.length ? owners.join(', ') : '' }}
      </v-tooltip>
    </CTableDataCell>
    <CTableDataCell>
      <span v-if="!!site.site_info_files.length" class="pointer">
        <a :href="site.site_info_files[0].file" target="_blank">
          <v-icon icon="mdi-download-box" color="primary" />
        </a>
        <v-tooltip activator="parent" location="top">
          {{ site.site_info_files[0]?.file_name }} 다운로드
        </v-tooltip>
      </span>
      <span v-else>
        <v-icon icon="mdi-download-box-outline" color="secondary" />
        <v-tooltip activator="parent" location="top">미등록</v-tooltip>
      </span>
    </CTableDataCell>
    <CTableDataCell>
      {{ site.dup_issue_date }}
    </CTableDataCell>
    <CTableDataCell v-if="write_project_site">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>사업 부지 등록</template>
    <template #default>
      <SiteForm
        :site="site"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
