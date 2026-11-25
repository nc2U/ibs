<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import type { FormVersion, IssueProject, Version } from '@/store/types/work_project'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import RoadmapList from './components/RoadmapList.vue'
import VersionDetail from './components/VersionDetail.vue'
import VersionForm from './components/VersionForm.vue'
import RoadmapAside from './components/RoadmapAside.vue'

const props = defineProps<{
  navMenu?: string[]
  currentProject?: IssueProject | null
}>()

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)
const toggle = () => cBody.value?.toggle()
defineExpose({ toggle })

const [route, router] = [useRoute(), useRouter()]

const aside = computed(() => route.name === '(로드맵)')

const workStore = useWork()
const { can, PERM } = usePerms()

const currentProject = computed(() => props.currentProject ?? workStore.currentProject)
const canManageVersions = computed(
  () =>
    currentProject.value?.status === '1' && can(PERM.PROJECT_VERSION, currentProject.value?.slug),
)
const version = computed(() => workStore.version)
const rawVersionList = computed(() => workStore.versionList)
const trackerList = computed(() => currentProject.value?.trackers ?? [])

const showCompleted = ref(route.query.completed === '1')
const selectedTrackers = ref<number[]>([])
const selectedVersionId = ref<number | null>(null)

// 선택된 트래커 필터링이 적용된 버전 목록 계산
const filteredVersionList = computed(() => {
  if (!selectedTrackers.value.length) {
    return rawVersionList.value
  }
  const selectedSet = new Set(selectedTrackers.value)
  return rawVersionList.value.map(ver => {
    // 최근 일감 목록 필터링
    const recentIssues = (ver.recent_issues ?? []).filter(i =>
      i.tracker?.pk ? selectedSet.has(i.tracker.pk) : true,
    )
    return {
      ...ver,
      recent_issues: recentIssues,
    }
  })
})

const onSelectVersion = (verId: number) => {
  selectedVersionId.value = verId
}

const loadRoadmapData = async () => {
  const projId = route.params.projId as string
  if (!projId) return

  const payload: {
    project: string
    status?: '' | '1' | '2' | '3'
    exclude?: '' | '1' | '2' | '3'
  } = {
    project: projId,
  }

  // 완료된(닫힌) 단계를 포함하지 않는 경우 status='3' 제외
  if (!showCompleted.value) {
    payload.exclude = '3'
  }

  await workStore.fetchVersionList(payload)
}

const onApplyFilter = async (filter: { completed: boolean; trackerIds: number[] }) => {
  const completedChanged = showCompleted.value !== filter.completed
  showCompleted.value = filter.completed
  selectedTrackers.value = filter.trackerIds

  await router.replace({
    query: {
      ...route.query,
      completed: filter.completed ? '1' : undefined,
    },
  })

  if (!completedChanged) return

  loading.value = true
  try {
    await loadRoadmapData()
  } finally {
    loading.value = false
  }
}

const onSubmit = async (payload: FormVersion, back = false) => {
  const projId = route.params.projId as string
  if (!payload.pk) {
    payload.project = projId
    const createdPk = await workStore.createVersion(payload)
    if (!createdPk) return
    if (back) {
      await router.replace({ name: '(설정)', params: { projId }, query: { menu: '단계' } })
    } else {
      await router.replace({ name: '(로드맵)', params: { projId } })
    }
  } else {
    const updated = await workStore.updateVersion(payload)
    if (!updated) return
    if (back) {
      await router.replace({ name: '(설정)', params: { projId }, query: { menu: '단계' } })
    } else {
      await router.replace({
        name: '(로드맵) - 보기',
        params: { projId, verId: updated.pk ?? payload.pk },
      })
    }
  }
}

watch(
  () => route.query.completed,
  val => {
    const next = val === '1'
    if (showCompleted.value !== next) {
      showCompleted.value = next
      loadRoadmapData()
    }
  },
)

watch(
  [() => route.name, () => route.params.verId],
  async ([name, verId]) => {
    if (name === '(로드맵) - 보기' && verId) {
      await workStore.fetchVersion(Number(verId))
    }
  },
  { immediate: true },
)

watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) loadRoadmapData()
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  try {
    await loadRoadmapData()
  } catch (err) {
    console.error('Failed to load roadmap data:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :nav-menu="navMenu" :aside="aside">
    <template v-slot:default>
      <RoadmapList
        v-if="route.name === '(로드맵)'"
        :version-list="filteredVersionList"
        :selected-version-id="selectedVersionId"
      />

      <VersionDetail
        v-if="route.name === '(로드맵) - 보기' && version"
        :version="version as Version"
      />

      <template v-if="route.name === '(로드맵) - 추가' || route.name === '(로드맵) - 수정'">
        <VersionForm v-if="canManageVersions" @on-submit="onSubmit" />
        <CAlert v-else color="warning"> 권한이 없거나 닫혀 있는 워크스페이스입니다. </CAlert>
      </template>
    </template>

    <template v-slot:aside>
      <RoadmapAside
        v-if="route.name === '(로드맵)'"
        :trackers="trackerList"
        :version-list="filteredVersionList"
        :completed="showCompleted"
        :selected-trackers="selectedTrackers"
        :selected-version-id="selectedVersionId"
        @apply-filter="onApplyFilter"
        @select-version="onSelectVersion"
      />
    </template>
  </ContentBody>
</template>
