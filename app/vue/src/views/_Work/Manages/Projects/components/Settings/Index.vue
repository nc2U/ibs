<script lang="ts" setup>
import Cookies from 'js-cookie'
import { computed, type ComputedRef, inject, onBeforeMount, ref, watch } from 'vue'
import { type IssueProject } from '@/store/types/work_project.ts'
import { type IssueCategory as ICategory } from '@/store/types/work_issue.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useRoute, useRouter } from 'vue-router'
import Loading from '@/components/Loading/Index.vue'
import ProjectForm from '@/views/_Work/Manages/Projects/components/ProjectForm.vue'
import Member from '@/views/_Work/Manages/Projects/components/Settings/components/Member.vue'
import IssueTracking from '@/views/_Work/Manages/Projects/components/Settings/components/IssueTracking.vue'
import Version from '@/views/_Work/Manages/Projects/components/Settings/components/Version.vue'
import IssueCategory from '@/views/_Work/Manages/Projects/components/Settings/components/IssueCategory.vue'
import Board from '@/views/_Work/Manages/Projects/components/Settings/components/Board.vue'
import CategoryForm from '@/views/_Work/Manages/Projects/components/Settings/category/CategoryForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const menu = ref('프로젝트')

const workManager = inject<ComputedRef<boolean>>('workManager')

const [route, router] = [useRoute(), useRouter()]
watch(route, newVal => {
  if (newVal.query?.menu) menu.value = newVal.query.menu as string
})

const initMenu = computed(() => (!!workManager?.value ? '프로젝트' : '단계'))

const settingMenus = computed(() => {
  const menus = [{ no: 4, menu: '단계' }]
  const perms = my_perms.value
  const isManager = !!workManager?.value
  const mods = modules.value

  if (isManager || perms?.includes('project_update')) menus.push({ no: 1, menu: '프로젝트' })
  if (isManager || perms?.includes('project_member')) menus.push({ no: 2, menu: '구성원' })
  if (isManager && mods?.issue) menus.push({ no: 3, menu: '업무추적' })
  if (mods?.issue) menus.push({ no: 5, menu: '업무범주' })
  if (isManager && mods?.forum) menus.push({ no: 7, menu: '게시판' })

  return menus.sort((a, b) => a.no - b.no).map(m => m.menu)
})

const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)
const my_perms = computed(() => (workStore.issueProject as IssueProject)?.my_perms)
const modules = computed(() => issueProject.value?.module)
const versionList = computed(() => workStore.versionList)
const memberList = computed(() =>
  (
    (issueProject.value
      ? issueProject.value.all_members
      : [...new Map(workStore.memberList.map(m => [m.user.pk, m])).values()]) as any[]
  ).map(m => m.user),
)

const deleteVersion = (pk: number) => workStore.deleteVersion(pk, issueProject.value?.slug)

const issueStore = useIssue()

const categorySubmit = (payload: ICategory) => {
  if (payload.pk) issueStore.updateCategory(payload)
  else issueStore.createCategory(payload)
  router.push({ name: '(설정)' })
}
const deleteCategory = (pk: number) => issueStore.deleteCategory(pk, issueProject.value?.slug)

const versionFilter = async (payload: { status?: '' | '1' | '2' | '3'; search?: string }) => {
  const { status, search } = payload
  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchVersionList({ project: projId, status, search })
  }
}

watch(
  () => route.params?.projId,
  async nVal => {
    if (nVal) {
      await workStore.fetchIssueProject(nVal as string)
      await workStore.fetchVersionList({ project: nVal as string })
    } else {
      workStore.removeIssueProject()
      await workStore.fetchIssueProjectList({ status: '1' })
    }
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (route.query.menu) menu.value = route.query.menu as string
  else menu.value = Cookies.get('workSettingMenu') ?? initMenu.value

  await workStore.fetchIssueProjectList({})
  await workStore.fetchRoleList()
  await issueStore.fetchTrackerList()

  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchIssueProject(projId)
    await workStore.fetchVersionList({ project: projId, status: '1' })
  }
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <template v-if="route.name === '(설정)'">
        <CRow class="py-2">
          <CCol>
            <h5>설정</h5>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol>
            <v-tabs v-model="menu" density="compact">
              <v-tab
                v-for="m in settingMenus"
                :value="m"
                :key="m"
                variant="tonal"
                :active="menu === m"
                @click="Cookies.set('workSettingMenu', m)"
              >
                {{ m }}
              </v-tab>
            </v-tabs>
          </CCol>
        </CRow>

        <ProjectForm v-if="menu === '프로젝트'" :project="issueProject" />

        <Member v-if="menu === '구성원'" />

        <IssueTracking v-if="menu === '업무추적'" />

        <Version
          v-if="menu === '단계'"
          :versions="versionList"
          @version-filter="versionFilter"
          @delete-version="deleteVersion"
        />

        <IssueCategory
          v-if="menu === '업무범주'"
          :categories="issueProject?.categories"
          @delete-category="deleteCategory"
        />

        <Board v-if="menu === '게시판'" :project="issueProject?.pk as number" />
      </template>

      <template v-if="route.name === '(설정) - 범주추가' || route.name === '(설정) - 범주수정'">
        <CategoryForm :member-list="memberList" @category-submit="categorySubmit" />
      </template>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
