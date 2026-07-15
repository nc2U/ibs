<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useStore } from '@/store'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings.ts'
import type { SimpleProject } from '@/store/types/work_project.ts'
import HeaderSearch from './components/Search.vue'
import HeaderNav from './components/HeaderNav.vue'

defineProps({
  pageTitle: { type: String, default: '' },
  navMenu: { type: Array, default: () => ['Base Menu'] },
  ancestors: { type: Array as PropType<SimpleProject[]>, default: () => [] },
})

const visible = ref(false)

const [route, router] = [useRoute(), useRouter()]
watch(route, () => (visible.value = false))

const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)

const isDark = computed(() => useStore().theme === 'dark')
const backGround = computed(() => (isDark.value ? 'bg-blue-grey-darken-5' : 'bg-indigo-lighten-5'))
const baseColor = computed(() => (isDark.value ? '#fff' : '#333'))
const bgColor = computed(() => (isDark.value ? '#24252F' : '#fefefe'))

const emit = defineEmits(['side-nav-call'])
const sideNavCall = () => emit('side-nav-call')

// 프로젝트 선택 기능 시작
const workStore = useWork()
const getProjects = computed(() =>
  workStore.getAllProjects.filter(p => p.slug !== route.params.projId),
)

const chkModules = (slug: string) => {
  const routeName = (route.name as string) ?? ''
  const project = workStore.issueProjectsFlat.filter(p => p.slug === slug)[0]
  if ((route.meta as any)?.title === '설 정 관 리' || routeName.includes('프로젝트')) return false
  else if (!route?.params?.projId || !project) return true
  else {
    if (routeName.includes('로드맵') && !project.versions?.length) return false
    else if (routeName.includes('업무') && !project.module?.issue) return false
    else if (routeName.includes('캘린더') && !project.module?.calendar) return false
    else if (routeName.includes('공지') && !project.module?.news) return false
    else if (routeName.includes('문서') && !project.module?.document) return false
    else return true
  }
}

const cngProject = async (slug: any) => {
  const routeName = (route.name as string) ?? ''
  const name = /^\(.*\)$/.test(routeName) ? routeName : `(${routeName})`
  if (slug) {
    if (!chkModules(slug)) await router.push({ name: '(개요)', params: { projId: slug } })
    else await router.push({ name, params: { projId: slug } })
  }
}

onBeforeMount(workStore.fetchAllProjectList)
</script>

<template>
  <CRow class="mb-0" :class="backGround">
    <CCol>
      <CRow class="px-3">
        <CCol class="mb-2 py-3 px-4 col-9 col-md-6 col-lg-7 col-xl-8">
          <CRow class="ps-4 ps-lg-0">
            <CCol class="mb-1" style="font-size: 0.9em">
              <span v-if="route.params.projId && company" class="mr-1 text-blue-grey">
                <router-link :to="{ name: '프로젝트' }">{{ company?.name }}</router-link>
                »
              </span>

              <span v-if="!!ancestors.length">
                <span v-for="p in ancestors" :key="p.pk">
                  <span v-if="p.visible" class="mr-1 text-blue-grey">
                    <router-link :to="{ name: route.name ?? '(개요)', params: { projId: p.slug } }">
                      {{ p.name }}
                    </router-link>
                    »
                  </span>
                </span>
              </span>
            </CCol>
          </CRow>

          <CRow>
            <CCol class="text-body d-none d-lg-block">
              <strong class="title pl-1"> {{ pageTitle }}</strong>
            </CCol>

            <CCol
              class="text-body d-lg-none pointer"
              :class="{ pointer: !!ancestors.length }"
              @click="visible = !visible"
            >
              <v-icon :icon="visible ? 'mdi-chevron-up' : 'mdi-chevron-down'" color="" />
              <strong class="title pl-1"> {{ pageTitle }}</strong>

              <CCollapse :visible="visible">
                <v-card class="mx-auto mt-3" :max-width="1000">
                  <v-list density="compact" :base-color="baseColor" :bg-color="bgColor">
                    <v-list-item
                      v-for="proj in getProjects"
                      :key="proj.value"
                      @click="cngProject(proj.value)"
                    >
                      <span v-if="!!proj.depth && proj.parent_visible">
                        {{ '&nbsp;'.repeat(proj.depth) }} »
                      </span>
                      {{ proj.label }}
                    </v-list-item>
                  </v-list>
                </v-card>
              </CCollapse>
            </CCol>
          </CRow>
        </CCol>

        <CCol class="text-body d-lg-none text-right p-3">
          <v-app-bar-nav-icon @click="sideNavCall" />
        </CCol>
        <CCol class="d-none d-lg-block text-right">
          <HeaderSearch :get-projects="getProjects" @change-project="cngProject" />
        </CCol>
      </CRow>

      <CRow class="d-none d-lg-block">
        <CCol>
          <HeaderNav :menus="navMenu" />
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
strong.title {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 20px;
  color: #5e636a;
}

.dark-theme .title {
  color: #ddd;
}
</style>
