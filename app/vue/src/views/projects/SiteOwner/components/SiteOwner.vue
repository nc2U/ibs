<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { usePerms } from '@/composables/usePerms'
import type { Relation, SimpleSite, SiteOwner } from '@/store/types/project'
import Site from '@/views/projects/SiteOwner/components/Site.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteOwnerForm from '@/views/projects/SiteOwner/components/SiteOwnerForm.vue'

const props = defineProps({
  owner: { type: Object as PropType<SiteOwner>, required: true },
  isReturned: { type: Boolean, default: false },
  isHighlight: { type: Boolean, default: false },
})

const emit = defineEmits(['relation-patch', 'multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const canSiteUpdate = computed(() => can(PERM.SITE_UPDATE))

const updateFormModal = ref()
const isModalVisible = ref(false)

const showDetail = () => {
  isModalVisible.value = true
  updateFormModal.value.callModal()
}

const closeModal = () => {
  updateFormModal.value.close()
  isModalVisible.value = false
}

const relationPatch = (payload: Relation) => emit('relation-patch', payload)

const multiSubmit = (payload: SiteOwner) => {
  emit('multi-submit', payload, (ok: boolean) => {
    if (ok) closeModal()
  })
}

const onDelete = (payload: { pk: number; project: number }) => {
  emit('on-delete', payload, (ok: boolean) => {
    if (ok) closeModal()
  })
}
</script>

<template>
  <template v-if="owner.sites && owner.sites.length">
    <CTableRow
      v-for="(site, index) in owner.sites"
      :key="site.pk"
      class="text-center"
      :class="{ 'table-warning': props.isHighlight && index === 0 }"
      :data-site-owner-id="index === 0 ? owner.pk : null"
    >
      <Site
        :owner="owner"
        :site="site as SimpleSite"
        :index="index"
        :is-returned="isReturned"
        :is-highlight="isHighlight && index === 0"
        @show-detail="showDetail"
        @relation-patch="relationPatch"
      />
    </CTableRow>
  </template>
  <CTableRow
    v-else
    class="text-center"
    :class="{ 'table-warning': props.isHighlight }"
    :data-site-owner-id="owner.pk"
  >
    <CTableDataCell>{{ owner.own_sort_desc }}</CTableDataCell>
    <CTableDataCell>{{ owner.owner }}</CTableDataCell>
    <CTableDataCell>{{ owner.date_of_birth }}</CTableDataCell>
    <CTableDataCell>{{ owner.phone1 }}</CTableDataCell>
    <CTableDataCell class="text-start text-muted">-</CTableDataCell>
    <CTableDataCell class="text-end text-muted">-</CTableDataCell>
    <CTableDataCell class="text-end text-muted">-</CTableDataCell>
    <CTableDataCell class="text-end text-muted">-</CTableDataCell>
    <CTableDataCell class="text-start text-muted">-</CTableDataCell>
    <CTableDataCell :class="{ 'bg-success': owner.use_consent }">
      {{ owner.use_consent ? '동의' : '' }}
    </CTableDataCell>
    <CTableDataCell v-if="canSiteUpdate"></CTableDataCell>
    <CTableDataCell v-if="canSiteUpdate">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>부지 소유자 정보 관리</template>
    <template #default>
      <SiteOwnerForm
        v-if="isModalVisible"
        :owner="owner"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="closeModal"
      />
    </template>
  </FormModal>
</template>
