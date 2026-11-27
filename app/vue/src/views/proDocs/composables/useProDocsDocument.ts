import { computed, ref, watch } from 'vue'
import { type RouteLocationNormalizedLoaded as Loaded, useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useProject } from '@/store/pinia/project.ts'
import { useDocs, type DocsFilter } from '@/store/pinia/docs.ts'
import type { AFile, Docs, Link, SuitCase } from '@/store/types/docs.ts'

export type ProDocsSubmitPayload = Docs & {
  issue_project?: number | null
  files?: AFile[]
  links?: Link[]
  newFiles?: Array<{ file: File | null; description: string }>
  cngFiles?: Array<{ pk: number; file: File }>
  newLinks?: Array<Link | string>
}

interface UseProDocsDocumentOptions {
  typeNumber: 1 | 2
  mainViewName: string
  withLawsuits?: boolean
}

export function useProDocsDocument(options: UseProDocsDocumentOptions) {
  const { can, PERM } = usePerms()
  const projStore = useProject()
  const accStore = useAccount()
  const docStore = useDocs()
  const [route, router] = [useRoute() as Loaded & { name: string }, useRouter()]

  const fController = ref<{ resetForm: (isFilter?: boolean) => void } | null>(null)
  const formRef = ref<{ setLawsuit?: (pk: number) => void } | null>(null)
  const typeNumber = ref<1 | 2>(options.typeNumber)
  const mainViewName = ref(options.mainViewName)
  const heatedPage = ref<number[]>([])
  const loading = ref(true)

  const createDefaultFilter = (projectPk: number | '' = ''): DocsFilter => ({
    project: projectPk,
    is_real_dev: 'true',
    doc_type: typeNumber.value,
    category: '',
    lawsuit: '',
    ordering: '-created',
    search: '',
    page: 1,
    limit: '',
  })

  const docsFilter = ref<DocsFilter>(createDefaultFilter())

  const project = computed(() => projStore.project?.pk)
  const projName = computed(() => projStore.project?.name)
  const canDocsRead = computed(() => can(PERM.DOCS_READ))

  const docs = computed(() => docStore.docs)
  const canUpdateCurrentDoc = computed(
    () =>
      can(PERM.DOCS_UPDATE) ||
      (can(PERM.DOCS_OWN_UPDATE) &&
        !!docs.value?.creator?.pk &&
        docs.value.creator.pk === accStore.userInfo?.pk),
  )
  const docsList = computed(() => docStore.docsList)
  const categoryList = computed(() => docStore.categoryList)
  const getSuitCase = computed(() => docStore.getSuitCase)

  const listFiltering = (payload: DocsFilter) => {
    docsFilter.value.limit = payload.limit || 10
    docsFilter.value.ordering = payload.ordering || '-created'
    docsFilter.value.lawsuit = payload.lawsuit ?? ''
    docsFilter.value.search = payload.search ?? ''
    docsFilter.value.page = payload.page || 1
    if (project.value && canDocsRead.value) {
      docStore.fetchDocsList({ ...docsFilter.value })
    }
  }

  const selectCate = (cate: number) => {
    docsFilter.value.page = 1
    docsFilter.value.category = cate || ''
    if (project.value && canDocsRead.value) {
      docStore.fetchDocsList({ ...docsFilter.value })
    }
  }

  const pageSelect = (page: number) => {
    docsFilter.value.page = page
    if (project.value && canDocsRead.value) {
      docStore.fetchDocsList({ ...docsFilter.value })
    }
  }

  const docsRenewal = (page: number) => pageSelect(page)

  const docsScrape = (docsPk: number) => {
    const user = accStore.userInfo?.pk
    if (user) accStore.createDocScrape({ docs: docsPk, user })
  }

  const buildDocsFormData = (payload: ProDocsSubmitPayload) => {
    const { pk, ...rest } = payload
    const getData: Record<string, unknown> = { ...rest }
    if (!getData.issue_project || options.withLawsuits) {
      getData.issue_project = projStore.project?.issue_project ?? getData.issue_project
    }

    const form = new FormData()
    for (const [key, rawVal] of Object.entries(getData)) {
      if (key === 'links' || key === 'files') {
        const items = Array.isArray(rawVal) ? rawVal : []
        items.forEach(val => form.append(key, JSON.stringify(val)))
      } else if (key === 'newFiles') {
        const items = Array.isArray(rawVal)
          ? (rawVal as Array<{ file: File | null; description: string }>)
          : []
        items.forEach(val => {
          if (val.file) {
            form.append('new_files', val.file)
            form.append('new_descs', val.description ?? '')
          }
        })
      } else if (key === 'cngFiles') {
        const items = Array.isArray(rawVal) ? (rawVal as Array<{ pk: number; file: File }>) : []
        items.forEach(val => {
          form.append('cngPks', String(val.pk))
          form.append('cngFiles', val.file)
        })
      } else if (key === 'newLinks') {
        const items = Array.isArray(rawVal) ? (rawVal as Array<Link | string>) : []
        items.forEach(val => {
          const linkStr = typeof val === 'string' ? val : val?.link
          if (linkStr) form.append('newLinks', linkStr)
        })
      } else if (rawVal !== undefined) {
        form.append(key, rawVal === null ? '' : String(rawVal))
      }
    }
    return { pk, form }
  }

  const onSubmit = async (payload: ProDocsSubmitPayload) => {
    if (!project.value) return
    const { pk, form } = buildDocsFormData(payload)

    if (pk) {
      const updated = await docStore.updateDocs({ pk, form, isProject: true })
      if (!updated) return
      await router.replace({ name: `${mainViewName.value} - 보기`, params: { docsId: pk } })
    } else {
      const created = await docStore.createDocs({ form, isProject: true })
      if (!created) return
      docsFilter.value.page = 1
      await router.replace({ name: mainViewName.value })
      fController.value?.resetForm(false)
    }
  }

  const createLawSuit = async (payload: SuitCase & { is_real_dev?: boolean }) => {
    if (!payload.issue_project) payload.issue_project = projStore.project?.issue_project ?? null
    payload.is_real_dev = true
    const created = await docStore.createSuitCase(payload)
    if (created?.pk) formRef.value?.setLawsuit?.(created.pk)
  }

  const docsHit = async (pk: number) => {
    if (!heatedPage.value.includes(pk)) {
      heatedPage.value.push(pk)
      await docStore.hitDocs(pk)
    }
  }

  const linkHit = async (pk: number) => {
    await docStore.hitLink(pk)
  }

  const fileHit = async (pk: number) => {
    await docStore.hitFile(pk)
  }

  const dataSetup = async (pk: number, docsId?: string | string[]) => {
    if (!canDocsRead.value) return
    docsFilter.value.project = pk
    const tasks: Promise<unknown>[] = [
      docStore.fetchCategoryList(typeNumber.value),
      docStore.fetchDocsList({ ...docsFilter.value }),
    ]
    if (docsId) tasks.push(docStore.fetchDocs(Number(docsId)))
    if (options.withLawsuits) {
      tasks.push(docStore.fetchAllSuitCaseList({ project: pk, is_real_dev: 'true' }))
    }
    await Promise.all(tasks)
  }

  const dataReset = async (resetRoute = true) => {
    docStore.removeDocs()
    docStore.removeDocsList()
    docStore.docsCount = 0
    docsFilter.value = createDefaultFilter(project.value ?? '')
    fController.value?.resetForm(false)
    if (resetRoute && route.name !== mainViewName.value) {
      await router.replace({ name: mainViewName.value, query: route.query })
    }
  }

  watch(
    project,
    async (newPk, oldPk) => {
      const switched = oldPk !== undefined && newPk !== oldPk
      loading.value = true
      try {
        if (switched) await dataReset(true)
        if (newPk && canDocsRead.value) {
          await dataSetup(newPk, route.params?.docsId)
        } else if (!newPk) {
          await dataReset(false)
        }
      } finally {
        loading.value = false
      }
    },
    { immediate: true },
  )

  watch(
    () => route.params.docsId,
    async newId => {
      if (newId && project.value && canDocsRead.value) {
        await docStore.fetchDocs(Number(newId))
      } else if (!newId) {
        docStore.removeDocs()
      }
    },
  )

  return {
    can,
    PERM,
    fController,
    formRef,
    typeNumber,
    mainViewName,
    docsFilter,
    heatedPage,
    loading,
    project,
    projName,
    canDocsRead,
    canUpdateCurrentDoc,
    docs,
    docsList,
    categoryList,
    getSuitCase,
    route,
    listFiltering,
    selectCate,
    pageSelect,
    docsRenewal,
    docsScrape,
    onSubmit,
    createLawSuit,
    docsHit,
    linkHit,
    fileHit,
  }
}
