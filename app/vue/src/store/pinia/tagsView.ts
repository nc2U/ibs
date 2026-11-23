import { ref } from 'vue'
import { defineStore } from 'pinia'
import { type CachedViews, type VisitedView } from '@/store/types/tagsView'
import { type RouteLocationNormalizedLoaded as RouteNormal } from 'vue-router'

export const useTagsView = defineStore('tags-view', () => {
  // state & getters
  const visitedViews = ref<VisitedView[]>([])
  const cachedViews = ref<CachedViews[]>([])

  // actions
  const addView = (view: VisitedView) => {
    addVisitedView(view)
    addCachedView(view)
  }

  const addVisitedView = (view: VisitedView) => {
    if (visitedViews.value.some(v => v.meta.title === view.meta.title)) return
    else visitedViews.value.push(Object.assign({}, view))
  }

  const addCachedView = (view: VisitedView) => {
    if (cachedViews.value.includes(view.name)) return
    if (!view?.meta?.noCache) cachedViews.value.push(view.name)
  }

  const delView = async (view: VisitedView) => {
    await delVisitedView(view)
    await delCachedView(view)
    return {
      visitedViews: [...visitedViews.value],
      cachedViews: [...cachedViews.value],
    }
  }

  const delVisitedView = (view: VisitedView) =>
    new Promise(resolve => {
      for (const [i, v] of visitedViews.value.entries()) {
        if (v.meta?.title === view.meta?.title) {
          visitedViews.value.splice(i, 1)
          break
        }
      }
      resolve([...visitedViews.value])
    })

  const delCachedView = (view: VisitedView) =>
    new Promise(resolve => {
      const index = cachedViews.value.indexOf(view.name)
      if (index > -1) cachedViews.value.splice(index, 1)
      resolve([...cachedViews.value])
    })

  const delOthersViews = async (view: VisitedView) => {
    await delOthersVisitedViews(view)
    await delOthersCachedViews(view)
    return {
      visitedViews: [...visitedViews.value],
      cachedViews: [...cachedViews.value],
    }
  }

  const delOthersVisitedViews = (view: VisitedView) =>
    new Promise(resolve => {
      visitedViews.value = visitedViews.value.filter(v => v.meta.affix || v.path === view.path)
      resolve([...visitedViews.value])
    })

  const delOthersCachedViews = (view: VisitedView) =>
    new Promise(resolve => {
      const index = cachedViews.value.indexOf(view.name)
      if (index > -1) cachedViews.value = cachedViews.value.slice(index, index + 1)
      else cachedViews.value = []
      resolve([...cachedViews.value])
    })

  const delAllViews = async () => {
    await delAllVisitedViews()
    await delAllCachedViews()
    return {
      visitedViews: [...visitedViews.value],
      cachedViews: [...cachedViews.value],
    }
  }

  const delAllVisitedViews = () =>
    new Promise(resolve => {
      visitedViews.value = visitedViews.value.filter(tag => tag.meta.affix)
      resolve([...visitedViews.value])
    })

  const delAllCachedViews = () =>
    new Promise(resolve => {
      cachedViews.value = []
      resolve([...cachedViews.value])
    })

  const updateVisitedView = (route: RouteNormal) => {
    for (const v of visitedViews.value) {
      if (v.path === route.path) {
        if (typeof route.name === 'string') v.name = route.name
        v.fullPath = route.fullPath
        v.meta = { ...route.meta }
        break
      }
    }
  }

  return {
    visitedViews,
    cachedViews,

    addView,
    addVisitedView,
    delView,
    delOthersViews,
    delAllViews,
    updateVisitedView,
  }
})
