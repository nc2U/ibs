<script lang="ts" setup>
import Cookies from 'js-cookie'
import { useRoute } from 'vue-router'
import { useProject } from '@/store/pinia/project'
import { useCompany } from '@/store/pinia/company'
import HeaderNav from '@/layouts/ContentHeader/components/HeaderNav.vue'
import CompanySelect from '@/layouts/ContentHeader/components/CompanySelect.vue'
import ProjectSelect from '@/layouts/ContentHeader/components/ProjectSelect.vue'

defineProps({
  pageTitle: {
    type: String,
    default: 'Page Title',
  },
  navMenu: {
    type: Array,
    default: () => ['Base Menu'],
  },
  selector: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['com-select', 'proj-select'])

const route = useRoute()
const companyStore = useCompany()
const projectStore = useProject()

const comSelect = async (com: number | null) => {
  if (!!com) {
    Cookies.set('curr-company', `${com}`)
    await companyStore.fetchCompany(com)
  } else companyStore.removeCompany()
  emit('com-select', com)
}

const projSelect = async (proj: number | null) => {
  if (!!proj) {
    Cookies.set('curr-project', `${proj}`)
    await projectStore.fetchProject(proj)
  } else projectStore.removeProject()
  emit('proj-select', proj)
}
</script>

<template>
  <CCard class="text-body mt-4 mx-2 mx-md-3 mx-xl-5">
    <CCardHeader>
      <v-icon icon="mdi mdi-text-box-check-outline" size="small" />
      <strong class="pl-1"> {{ pageTitle }}</strong>
    </CCardHeader>

    <CCardBody>
      <HeaderNav :menus="navMenu" :query="route?.query" />

      <CompanySelect v-if="selector === 'CompanySelect'" @com-select="comSelect" />

      <ProjectSelect v-if="selector === 'ProjectSelect'" @proj-select="projSelect" />

      <slot />
    </CCardBody>
  </CCard>
</template>
