<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useRoute, useRouter } from 'vue-router'
import type { Version } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import RoadmapList from './components/RoadmapList.vue'
import VersionView from './components/VersionView.vue'
import VersionForm from './components/VersionForm.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const aside = computed(() => route.name === '(로드맵)')

const workStore = useWork()
const version = computed(() => workStore.version)
const versionList = computed(() => workStore.versionList)

const [route, router] = [useRoute(), useRouter()]

const onSubmit = (payload: any, back = false) => {
  if (!payload.pk) {
    payload.project = route.params.projId as string
    workStore.createVersion(payload)
    if (!back) router.replace({ name: '(로드맵)' })
  } else workStore.updateVersion(payload)
  if (back) router.replace({ name: '(설정)', query: { menu: '버전' } })
}

watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) workStore.fetchVersionList({ project: nVal as string, exclude: '3' })
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  await workStore.fetchVersionList({ project: route.params.projId as string, exclude: '3' })
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="aside">
    <template v-slot:default>
      <RoadmapList v-if="route.name === '(로드맵)'" :version-list="versionList" />

      <VersionView v-if="route.name === '(로드맵) - 보기'" :version="version as Version" />

      <VersionForm
        v-if="route.name === '(로드맵) - 추가' || route.name === '(로드맵) - 수정'"
        @on-submit="onSubmit"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
