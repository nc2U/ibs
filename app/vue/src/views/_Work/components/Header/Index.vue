<script lang="ts" setup>
import { ref, computed, type PropType, watch, onBeforeMount } from 'vue'
import { useStore } from '@/store'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import type { SimpleProject } from '@/store/types/work_project.ts'
import HeaderSearch from './components/Search.vue'
import HeaderNav from './components/HeaderNav.vue'

defineProps({
  pageTitle: { type: String, default: '' },
  navMenu: { type: Array, default: () => ['Base Menu'] },
  familyTree: { type: Array as PropType<SimpleProject[]>, default: () => [] },
})

const visible = ref(false)

const [route, router] = [useRoute(), useRouter()]
watch(route, () => (visible.value = false))

const isDark = computed(() => useStore().theme === 'dark')
const backGround = computed(() => (isDark.value ? 'bg-blue-grey-darken-5' : 'bg-indigo-lighten-5'))
const baseColor = computed(() => (isDark.value ? '#fff' : '#333'))
const bgColor = computed(() => (isDark.value ? '#24252F' : '#fefefe'))

const emit = defineEmits(['side-nav-call'])
const sideNavCall = () => emit('side-nav-call')

// 프로젝트 선택 기능 시작
const workStore = useWork()
const getProjects = computed(() =>
  workStore.getAllProjects
    .filter(p => p.slug !== route.params.projId)
    .map(p => ({ value: p.slug, label: p.label, repo: p.repo })),
)

const chkRepo = (slug: string) => getProjects.value.filter(p => p.value === slug)[0].repo
const cngProject = async (event: any) => {
  if (event) {
    if (!route?.params.projId) await router.replace({ name: '(개요)', params: { projId: event } })
    else {
      if (route.name === '(저장소)' && !(await chkRepo(event)))
        await router.replace({ name: '(개요)', params: { projId: event } })
      else await router.replace({ name: '(저장소)', params: { projId: event } })
    }
  }
}

onBeforeMount(async () => {
  await workStore.fetchAllIssueProjectList()
})
</script>

<template>
  <CRow class="mb-0" :class="backGround">
    <CCol>
      <CRow class="px-3">
        <CCol class="mb-2 p-4 col-9 col-md-6 col-lg-7 col-xl-9">
          <CRow v-if="!!familyTree.length" class="d-none d-lg-block">
            <CCol>
              <span v-for="p in familyTree" :key="p.pk">
                <span v-if="p.visible" class="mr-1 text-blue-grey">
                  <router-link :to="{ name: route.name ?? '(개요)', params: { projId: p.slug } }">
                    {{ p.name }}
                  </router-link>
                  »
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
              :class="{ pointer: !!familyTree.length }"
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
