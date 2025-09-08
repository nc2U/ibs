<script lang="ts" setup>
import { onBeforeMount, type PropType, reactive, ref } from 'vue'
import { type SiteOwner, type Relation, type SimpleSite } from '@/store/types/project'
import Site from '@/views/projects/SiteOwner/components/Site.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteOwnerForm from '@/views/projects/SiteOwner/components/SiteOwnerForm.vue'

const props = defineProps({
  owner: { type: Object as PropType<SiteOwner>, required: true },
  isReturned: { type: Boolean },
  isHighlight: { type: Boolean, default: false },
})

const emit = defineEmits(['relation-patch', 'multi-submit', 'on-delete'])

const form = reactive({
  pk: null as number | null,
  project: null as number | null,
  owner: '',
  date_of_birth: null as string | null,
  phone1: '',
  phone2: '',
  zipcode: '',
  address1: '',
  address2: '',
  address3: '',
  own_sort: '',
  own_sort_desc: '',
  sites: [] as SimpleSite[],
  counsel_record: '',
})

const updateFormModal = ref()
const showDetail = () => updateFormModal.value.callModal()
const relationPatch = (payload: Relation) => emit('relation-patch', payload)
const multiSubmit = (payload: SiteOwner) => emit('multi-submit', payload)
const onDelete = (payload: { pk: number; project: number }) => emit('on-delete', payload)

onBeforeMount(() => {
  if (props.owner) {
    form.pk = props.owner.pk as number
    form.project = props.owner.project
    form.owner = props.owner.owner
    form.date_of_birth = props.owner.date_of_birth
    form.phone1 = props.owner.phone1
    form.phone2 = props.owner.phone2
    form.zipcode = props.owner.zipcode
    form.address1 = props.owner.address1
    form.address2 = props.owner.address2
    form.address3 = props.owner.address3
    form.own_sort = props.owner.own_sort
    form.own_sort_desc = props.owner.own_sort_desc
    form.sites = props.owner.sites
    form.counsel_record = props.owner.counsel_record
  }
})
</script>

<template>
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
      @multi-submit="multiSubmit"
      @on-delete="onDelete"
    />
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>부지 소유자 정보 관리</template>
    <template #default>
      <SiteOwnerForm
        :owner="owner"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
