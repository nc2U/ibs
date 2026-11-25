<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import type { IssueProject } from '@/store/types/work_project'
import type { IssueCategory as ICategory } from '@/store/types/work_issue'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'
import { useAccount } from '@/store/pinia/account'
import { message } from '@/utils/helper'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ProjectForm from '@/views/_Work/Manages/Projects/components/ProjectForm.vue'
import Member from './components/Member.vue'
import Version from './components/Version.vue'
import IssueCategory from './components/IssueCategory.vue'
import CategoryForm from './category/CategoryForm.vue'
import Forum from './components/Forum.vue'

const props = defineProps<{
  navMenu?: string[]
  currentProject?: IssueProject | null
}>()

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const toggle = () => cBody.value?.toggle()
defineExpose({ toggle })

const menu = ref('')

const { can, PERM } = usePerms()

const accStore = useAccount()
const workManager = computed(() => accStore.workManager)

const canAccessProject = computed(() => {
  if (workManager.value) return true
  const slug = currentProject.value?.slug
  return (
    can(PERM.PROJECT_UPDATE, slug) ||
    can(PERM.PROJECT_PUBLIC, slug) ||
    can(PERM.PROJECT_MODULE, slug)
  )
})

const canAccessForum = computed(() => {
  if (workManager.value) return true
  return can(PERM.FORUM_MANAGE, currentProject.value?.slug)
})

const [route, router] = [useRoute(), useRouter()]

const workStore = useWork()
const currentProject = computed<IssueProject | null>(
  () => props.currentProject ?? workStore.currentProject,
)

const isProjectActive = computed(() => !currentProject.value || currentProject.value.status === '1')

const settingMenus = computed(() => {
  if (!isProjectActive.value) return []
  const menus: { no: number; menu: string }[] = []
  const slug = currentProject.value?.slug

  const isForumEnabled = !currentProject.value?.module || currentProject.value.module.forum

  // PERM 상수를 기반으로 권한 체크 + 워크스페이스 모듈 활성화 여부 반영
  if (canAccessProject.value) menus.push({ no: 1, menu: '메인설정' })
  if (workManager.value || can(PERM.PROJECT_MEMBER, slug)) menus.push({ no: 2, menu: '구성원' })
  if (workManager.value || can(PERM.PROJECT_VERSION, slug)) menus.push({ no: 4, menu: '단계' })
  if (workManager.value || can(PERM.ISSUE_CATEGORY_MANAGE, slug))
    menus.push({ no: 5, menu: '업무범주' })
  if (isForumEnabled && canAccessForum.value) menus.push({ no: 7, menu: '게시판' })

  return menus.sort((a, b) => a.no - b.no).map(m => m.menu)
})

const initMenu = computed(() => settingMenus.value[0] || '')

const syncAllowedMenu = () => {
  const allowed = settingMenus.value
  const queryMenu = typeof route.query?.menu === 'string' ? route.query.menu : ''
  if (queryMenu && allowed.includes(queryMenu)) {
    menu.value = queryMenu
    return
  }
  if (menu.value && allowed.includes(menu.value)) return
  const localStorageMenu = localStorage.getItem('workSettingMenu')
  if (localStorageMenu && allowed.includes(localStorageMenu)) {
    menu.value = localStorageMenu
  } else {
    menu.value = initMenu.value
  }
}

watch([() => route.query?.menu, settingMenus], () => syncAllowedMenu(), { immediate: true })

const versionList = computed(() => workStore.versionList)
const memberList = computed(() => {
  const members = currentProject.value
    ? (currentProject.value.all_members ?? []).filter(m =>
        (m.roles ?? []).some(r => r.assignable !== false),
      )
    : [...new Map(workStore.memberList.map(m => [m.user.pk, m])).values()]
  return members.map(m => m.user).filter((u): u is { pk: number; username: string } => Boolean(u))
})

const deleteVersion = async (pk: number) => {
  await workStore.deleteVersion(pk, currentProject.value?.slug)
}

const issueStore = useIssue()

const categorySubmit = async (payload: ICategory) => {
  const saved = payload.pk
    ? await issueStore.updateCategory(payload)
    : await issueStore.createCategory(payload)
  if (!saved) return
  await router.push({
    name: '(설정)',
    params: { projId: route.params.projId },
    query: { menu: '업무범주' },
  })
}
const deleteCategory = async (pk: number) => {
  await issueStore.deleteCategory(pk, currentProject.value?.slug)
}

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
      await workStore.fetchVersionList({ project: nVal as string, status: '' })
    }
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  try {
    await issueStore.fetchTrackerList()

    if (route.params.projId) {
      const projId = route.params.projId as string
      await workStore.fetchVersionList({ project: projId, status: '' })
    }

    syncAllowedMenu()
  } catch (err) {
    console.log('Failed to load project settings configurations', err)
    message('warning', '', '워크스페이스 설정 정보를 불러오는 데 실패했습니다.')
  } finally {
    loading.value = false
  }
})
const handleMenuClick = (m: string) => {
  if (!settingMenus.value.includes(m)) return
  localStorage.setItem('workSettingMenu', m)
  menu.value = m
}
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :nav-menu="navMenu" :aside="false">
    <template v-slot:default>
      <template v-if="route.name === '(설정)'">
        <CRow class="py-2">
          <CCol>
            <h5><v-icon icon="mdi-cog" color="green-darken-1" size="small" class="me-2" />설정</h5>
          </CCol>
        </CRow>

        <CAlert v-if="!isProjectActive" color="warning">
          이 워크스페이스는 닫혀 있거나 잠금보관 상태이므로 설정을 변경할 수 없습니다.
        </CAlert>

        <CAlert v-else-if="!settingMenus.length" color="warning">
          워크스페이스 설정에 접근할 권한이 없습니다.
        </CAlert>

        <template v-else>
          <CRow class="mb-3">
            <CCol>
              <v-tabs v-model="menu" density="compact">
                <v-tab
                  v-for="m in settingMenus"
                  :value="m"
                  :key="m"
                  variant="tonal"
                  :active="menu === m"
                  @click="handleMenuClick(m)"
                >
                  {{ m }}
                </v-tab>
              </v-tabs>
            </CCol>
          </CRow>

          <ProjectForm v-if="menu === '메인설정'" :project="currentProject" />

          <Member v-if="menu === '구성원'" />

          <Version
            v-if="menu === '단계'"
            :versions="versionList"
            :current-project-slug="
              (currentProject?.slug as string) || (route.params.projId as string)
            "
            @version-filter="versionFilter"
            @delete-version="deleteVersion"
          />

          <IssueCategory
            v-if="menu === '업무범주'"
            :categories="currentProject?.categories"
            @delete-category="deleteCategory"
          />

          <Forum v-if="menu === '게시판'" :project="currentProject?.pk as number" />
        </template>
      </template>

      <template v-if="route.name === '(설정) - 범주추가' || route.name === '(설정) - 범주수정'">
        <CategoryForm
          v-if="
            isProjectActive &&
            (workManager || can(PERM.ISSUE_CATEGORY_MANAGE, currentProject?.slug))
          "
          :member-list="memberList"
          @category-submit="categorySubmit"
        />
        <CAlert v-else color="warning"> 권한이 없거나 닫혀 있는 워크스페이스입니다. </CAlert>
      </template>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
