<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import type { Site } from '@/store/types/project'
import { usePerms } from '@/composables/usePerms'
import { cutString, numFormat } from '@/utils/baseMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteForm from './SiteForm.vue'

const props = defineProps({
  site: { type: Object as PropType<Site>, required: true },
  isReturned: { type: Boolean, default: false },
  isHighlight: { type: Boolean, default: false },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const canSiteCreate = computed(() => can(PERM.SITE_CREATE))
const canSiteUpdate = computed(() => can(PERM.SITE_UPDATE))
const canSiteManage = computed(() => canSiteCreate.value || canSiteUpdate.value)

const updateFormModal = ref()
const isModalVisible = ref(false)

const owners = computed(() => (props.site.owners ? props.site.owners.map(o => o.owner) : []))

const showDetail = () => {
  isModalVisible.value = true
  updateFormModal.value.callModal()
}

const closeModal = () => {
  updateFormModal.value.close()
  isModalVisible.value = false
}

const multiSubmit = (payload: Site) => {
  emit('multi-submit', payload)
  closeModal()
}

const onDelete = (payload: { pk: number; project: number }) => {
  emit('on-delete', payload)
  closeModal()
}
</script>

<template>
  <CTableRow
    class="text-center"
    :class="{ 'table-warning': props.isHighlight }"
    :data-site-id="site.pk"
  >
    <CTableDataCell>{{ site.order }}</CTableDataCell>
    <CTableDataCell>
      <a href="#" @click.prevent="showDetail">
        {{ site.district }}
      </a>
    </CTableDataCell>
    <CTableDataCell>
      <a href="#" @click.prevent="showDetail">
        {{ site.lot_number }}
      </a>
    </CTableDataCell>
    <CTableDataCell>
      {{ site.site_purpose }}
    </CTableDataCell>
    <CTableDataCell class="text-end">
      {{ numFormat(site.official_area || 0, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-end" color="warning">
      {{ numFormat((Number(site.official_area) || 0) * 0.3025, 2) }}
    </CTableDataCell>
    <CTableDataCell v-if="isReturned" class="text-end">
      {{ numFormat(site.returned_area || 0, 2) }}
    </CTableDataCell>
    <CTableDataCell v-if="isReturned" class="text-right" color="warning">
      {{ numFormat((Number(site.returned_area) || 0) * 0.3025, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      {{ owners.length ? cutString(owners.join(', '), 48) : '' }}
      <v-tooltip v-if="owners.length" activator="parent" location="top">
        {{ owners.length ? owners.join(', ') : '' }}
      </v-tooltip>
    </CTableDataCell>
    <CTableDataCell>
      <span v-if="site.site_info_files && site.site_info_files.length" class="pointer">
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
    <CTableDataCell v-if="canSiteManage">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>사업 부지 상세 및 수정</template>
    <template #default>
      <SiteForm
        v-if="isModalVisible"
        :site="site"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="closeModal"
      />
    </template>
  </FormModal>
</template>
