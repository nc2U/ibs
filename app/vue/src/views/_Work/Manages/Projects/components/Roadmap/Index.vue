<script lang="ts" setup>
import { computed, onBeforeMount } from 'vue'
import { useWork } from '@/store/pinia/work'
import { useRoute, useRouter } from 'vue-router'
import type { Version } from '@/store/types/work'
import RoadmapList from './components/RoadmapList.vue'
import VersionView from './components/VersionView.vue'
import VersionForm from './components/VersionForm.vue'

const emit = defineEmits(['aside-visible'])

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

const asideVisible = (visible: boolean) => emit('aside-visible', visible)

onBeforeMount(() =>
  workStore.fetchVersionList({ project: route.params.projId as string, exclude: '3' }),
)
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default></template>

    <template v-slot:aside></template>
  </ContentBody>
  
  <RoadmapList
    v-if="route.name === '(로드맵)'"
    :version-list="versionList"
    @aside-visible="asideVisible"
  />

  <VersionView
    v-if="route.name === '(로드맵) - 보기'"
    :version="version as Version"
    @aside-visible="asideVisible"
  />

  <VersionForm
    v-if="route.name === '(로드맵) - 추가' || route.name === '(로드맵) - 수정'"
    @aside-visible="asideVisible"
    @on-submit="onSubmit"
  />
</template>
