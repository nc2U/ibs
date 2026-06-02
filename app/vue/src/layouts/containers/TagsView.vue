<script lang="ts" setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useStore } from '@/store'
import { useTagsView } from '@/store/pinia/tagsView'
import { type VisitedView } from '@/store/types/tagsView'
import { useRoute, useRouter, type RouteRecordRaw } from 'vue-router'

const store = useStore()
const dark = computed(() => store.theme === 'dark')
const btnColor = computed(() => (dark.value ? 'blue-grey' : ''))

const [route, router] = [useRoute(), useRouter()]
watch(
  () => route?.meta?.title,
  () => {
    addTags()
    moveToCurrentTag()
  },
)

const visible = ref(false)
watch(visible, value =>
  value
    ? document.body.addEventListener('click', closeMenu)
    : document.body.removeEventListener('click', closeMenu),
)

const affixTags = ref<VisitedView[]>([]) // 고정 태그

const tagsViewStore = useTagsView()
const visitedViews = computed(() => tagsViewStore.visitedViews)

// 의도된 설계: 제목이 같으면(목록/생성/수정 등) 동일한 활성 탭으로 처리
const isActive = (currView: VisitedView) =>
  currView.name === route.name || currView.meta.title === route.meta.title

const isAffix = (view: VisitedView) => !!(view.meta && view.meta.affix)

const slashPath = (p: string) => (p.charAt(0) !== '/' ? '/' + p : p)

const filterAffixTags = (regRoutes: readonly RouteRecordRaw[]) => {
  let affixedViews: VisitedView[] = []
  regRoutes.forEach((view: RouteRecordRaw) => {
    if (view?.meta && view.meta?.affix) {
      const path = slashPath(view.path)
      affixedViews.push({
        name: view.name as string,
        path,
        fullPath: path,
        meta: { ...view.meta },
      })
    }

    if (view.children) {
      const tempViews = filterAffixTags(view.children)
      if (!!tempViews.length) {
        affixedViews = [...affixedViews, ...tempViews]
      }
    }
  })

  return affixedViews
}

const initTags = () => {
  // 현재 matched 뿐만 아니라 전체 라우트에서 고정 태그 검색
  const routes = router.getRoutes()
  affixTags.value = filterAffixTags(routes)
  affixTags.value.forEach((view: VisitedView) => {
    if (view?.meta?.title) tagsViewStore.addView(view)
  })
}

const addTags = () => {
  if (route?.meta?.title && !route?.meta?.except) {
    tagsViewStore.addView({
      name: route.name,
      path: route.path,
      fullPath: route.fullPath,
      meta: route.meta,
    } as VisitedView)
  }
}

const moveToCurrentTag = () =>
  nextTick(() => {
    // visitedViews 데이터를 직접 순회하여 쿼리 변경 시 업데이트
    for (const view of visitedViews.value) {
      if (view.path === route.path) {
        if (view.fullPath !== route.fullPath) {
          tagsViewStore.updateVisitedView(route)
        }
        break
      }
    }
  })

const toLastView = () => {
  const latestView = visitedViews.value.slice(-1)[0]
  if (latestView) {
    router.push({ path: latestView.fullPath ?? latestView.path })
  } else {
    // 모든 태그가 닫혔을 경우 기본 대시보드 또는 루트로 이동
    router.push('/')
  }
}

const closeSelectedTag = (view: VisitedView) =>
  tagsViewStore.delView(view).then(() => {
    if (isActive(view)) toLastView() // 현재 페이지를 닫았다면 이전 페이지로 이동
  })

const closeMenu = () => (visible.value = false)

onMounted(() => {
  initTags()
  addTags()
})
</script>

<template>
  <v-sheet max-width="100%" class="my-1" :class="{ dark }">
    <v-slide-group show-arrows>
      <v-slide-group-item
        v-for="view in visitedViews"
        :key="view.fullPath"
        class="tags-view-item"
        @click.middle="!isAffix(view) ? closeSelectedTag(view) : ''"
      >
        <v-btn
          class="mx-1 my-0 text-body"
          :class="{ darkBtn: dark }"
          style="text-decoration: none"
          size="small"
          :border="true"
          :rounded="0"
          :color="isActive(view) ? 'success' : btnColor"
          :to="{ path: view.fullPath }"
        >
          <v-icon v-if="isActive(view)" icon="mdi-circle" size="x-small" class="mr-2" />
          {{ view.meta.title }}
          <v-icon
            v-if="!isAffix(view)"
            icon="mdi-close"
            size="x-small"
            class="pa-2 ml-1 close"
            @click.prevent.stop="closeSelectedTag(view)"
          />
        </v-btn>
      </v-slide-group-item>
    </v-slide-group>
  </v-sheet>
</template>

<style lang="scss" scoped>
.close:hover {
  background: #ccc;
}

.dark {
  background: #2a2b36;
}
</style>
