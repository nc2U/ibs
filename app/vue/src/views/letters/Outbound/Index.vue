<script setup lang="ts">
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/letters/_menu/headermixin.ts'
import {
  onBeforeRouteUpdate,
  type RouteLocationNormalizedLoaded as Loaded,
  useRoute,
  useRouter,
} from 'vue-router'
import { useCompany } from '@/store/pinia/company.ts'
import { type LetterFilter, useDocs } from '@/store/pinia/docs.ts'
import type { OfficialLetter } from '@/store/types/docs'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComAuthGuard from '@/components/AuthGuard/ComAuthGuard.vue'
import LetterList from './components/LetterList.vue'
import LetterView from './components/LetterView.vue'
import LetterForm, { type LocalAttachmentItem } from './components/LetterForm.vue'

const mainViewName = ref('발송 공문 관리')

const createDefaultFilter = (companyId: number | '' = ''): LetterFilter => ({
  company: companyId,
  issue_date_from: '',
  issue_date_to: '',
  approval_status: '',
  dispatch_method: '',
  creator: '',
  ordering: '-created',
  search: '',
  page: 1,
  limit: 10,
})

const letterFilter = ref<LetterFilter>(createDefaultFilter())

const comStore = useCompany()
const company = computed(() => comStore.company?.pk)

const docStore = useDocs()
const letter = computed<OfficialLetter | null>(() => docStore.letter)
const letterList = computed(() => docStore.letterList)
const letterCount = computed(() => docStore.letterCount)

const fetchLetter = (pk: number) => docStore.fetchLetter(pk)
const fetchLetterList = (payload: LetterFilter) => docStore.fetchLetterList(payload)
const createLetter = (payload: OfficialLetter, filter?: LetterFilter) =>
  docStore.createLetter(payload, filter)
const updateLetter = (pk: number, payload: OfficialLetter, filter?: LetterFilter) =>
  docStore.updateLetter(pk, payload, filter)
const deleteLetter = (pk: number, filter: LetterFilter) => docStore.deleteLetter(pk, filter)
const generatePdf = (pk: number) => docStore.generatePdf(pk)

const [route, router] = [useRoute() as Loaded & { name: string }, useRouter()]

const submitting = ref(false)
const pdfGenerating = ref(false)
const headerKey = ref(0)
const isInitializing = ref(true)
const loadedLetterPk = ref<number | null>(null)

const redirectIfEditLocked = (letterId?: string | string[]) => {
  if (!letterId || !route.name?.includes('수정') || !letter.value) return false
  if (
    letter.value.approval_status === 'pending' ||
    letter.value.approval_status === 'approved' ||
    letter.value.dispatched_at
  ) {
    router.replace({
      name: `${mainViewName.value} - 보기`,
      params: { letterId },
    })
    return true
  }
  return false
}

const loadSingleLetter = async (letterId?: string | string[]) => {
  if (letterId) {
    const numId = Number(letterId)
    if (loadedLetterPk.value === numId && letter.value?.pk === numId) {
      redirectIfEditLocked(letterId)
      return
    }
    loadedLetterPk.value = numId
    await fetchLetter(numId)
    redirectIfEditLocked(letterId)
  } else {
    loadedLetterPk.value = null
    docStore.removeLetter()
  }
}

watch(
  () => route.params.letterId,
  async val => {
    if (isInitializing.value) return
    await loadSingleLetter(val)
  },
)

watch(
  company,
  async (newCompany, oldCompany) => {
    if (isInitializing.value) return
    if (newCompany && newCompany !== oldCompany && oldCompany !== undefined) {
      letterFilter.value = createDefaultFilter(newCompany)
      await dataSetup(newCompany, route.params?.letterId)
    }
  },
  { immediate: false },
)

const listFiltering = (payload: LetterFilter) => {
  letterFilter.value = { ...letterFilter.value, ...payload }
  letterFilter.value.company = company.value as number
  fetchLetterList(letterFilter.value)
}

const pageSelect = (page: number) => {
  letterFilter.value.page = page
  fetchLetterList(letterFilter.value)
}

const onSubmit = async (
  payload: OfficialLetter,
  attachmentsToUpload?: LocalAttachmentItem[],
  isDirectSubmit = false,
) => {
  if (submitting.value || !company.value) return
  submitting.value = true
  try {
    const data = { ...payload, company: company.value }
    let letterPk: number | null = null

    if (payload.pk) {
      const updated = await updateLetter(payload.pk, data, letterFilter.value)
      if (!updated?.pk) return
      letterPk = updated.pk
    } else {
      const created = await createLetter(data, letterFilter.value)
      if (!created?.pk) return
      letterPk = created.pk
    }

    if (attachmentsToUpload && attachmentsToUpload.length > 0) {
      for (const att of attachmentsToUpload) {
        const formData = new FormData()
        formData.append('letter', String(letterPk))
        formData.append('file', att.file)
        if (att.name) formData.append('name', att.name)
        if (att.quantity) formData.append('quantity', att.quantity)
        await docStore.uploadLetterAttachment(letterPk, formData)
      }
    }

    if (isDirectSubmit === true) {
      await docStore.submitApproval(letterPk)
    }

    loadedLetterPk.value = letterPk
    await router.replace({
      name: `${mainViewName.value} - 보기`,
      params: { letterId: letterPk },
    })
  } finally {
    submitting.value = false
  }
}

const onDelete = async (pk: number) => {
  const deleted = await deleteLetter(pk, letterFilter.value)
  if (deleted) {
    loadedLetterPk.value = null
    await router.replace({ name: mainViewName.value })
  }
}

const onGeneratePdf = async (pk: number) => {
  pdfGenerating.value = true
  try {
    await generatePdf(pk)
  } finally {
    pdfGenerating.value = false
  }
}

const dataSetup = async (pk: number, letterId?: string | string[]) => {
  letterFilter.value.company = pk
  loadedLetterPk.value = letterId ? Number(letterId) : null
  await Promise.all([
    fetchLetterList(letterFilter.value),
    comStore.fetchCompanySealList(pk),
    letterId ? fetchLetter(Number(letterId)) : Promise.resolve(),
  ])
  if (!letterId) {
    docStore.removeLetter()
  } else {
    redirectIfEditLocked(letterId)
  }
}

const dataReset = () => {
  letterFilter.value = createDefaultFilter()
  loadedLetterPk.value = null
  docStore.removeLetterList()
  docStore.letterCount = 0
}

const clearCompanyQueryParam = () => {
  if (route.query.company !== undefined) {
    const nextQuery = { ...route.query }
    delete nextQuery.company
    router
      .replace({
        name: route.name,
        params: route.params,
        query: nextQuery,
      })
      .catch(() => {})
  }
}

const comSelect = async (target: number | null, skipClearQuery = false) => {
  if (!skipClearQuery) clearCompanyQueryParam()

  if (target) {
    localStorage.setItem('curr-company', `${target}`)
    if (company.value !== target) {
      await comStore.fetchCompany(target)
    }

    if (route.name?.includes('보기') || route.name?.includes('수정')) {
      await router.replace({ name: mainViewName.value })
    }

    if (isInitializing.value) {
      letterFilter.value = createDefaultFilter(target)
      await dataSetup(target, route.params?.letterId)
      headerKey.value++
    }
  } else {
    dataReset()
  }
}

onBeforeRouteUpdate(async to => {
  const toCompanyId = to.query.company ? parseInt(to.query.company as string, 10) : null

  if (toCompanyId && toCompanyId !== company.value) {
    await comSelect(toCompanyId, true)
  } else if (to.name === mainViewName.value && company.value) {
    await fetchLetterList(letterFilter.value)
  }
})

const urlCompanyId = computed(() => {
  const id = route.query.company
  return id ? parseInt(id as string, 10) : null
})

const loading = ref(true)
onBeforeMount(async () => {
  const companyId = company.value ?? comStore.initComId

  if (urlCompanyId.value) {
    await comSelect(urlCompanyId.value, true)
  } else {
    await dataSetup(companyId, route.params?.letterId)
  }

  isInitializing.value = false
  loading.value = false
})
</script>

<template>
  <ComAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :key="headerKey"
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <div v-if="route.name === mainViewName" class="pt-3">
          <LetterList
            :company="company as number"
            :letter-list="letterList"
            :letter-count="letterCount"
            :letter-filter="letterFilter"
            :view-route="mainViewName"
            @list-filter="listFiltering"
            @page-select="pageSelect"
          />
        </div>

        <div v-else-if="route.name?.includes('보기')">
          <LetterView
            :letter="letter as OfficialLetter"
            :view-route="mainViewName"
            :letter-filter="letterFilter"
            :pdf-loading="pdfGenerating"
            @on-delete="onDelete"
            @generate-pdf="onGeneratePdf"
          />
        </div>

        <div v-else-if="route.name?.includes('작성')">
          <LetterForm
            :company="company as number"
            :view-route="mainViewName"
            :submitting="submitting"
            @on-submit="onSubmit"
          />
        </div>

        <div v-else-if="route.name?.includes('수정')">
          <LetterForm
            :company="company as number"
            :letter="letter as OfficialLetter"
            :view-route="mainViewName"
            :submitting="submitting"
            @on-submit="onSubmit"
          />
        </div>
      </CCardBody>
    </ContentBody>
  </ComAuthGuard>
</template>
