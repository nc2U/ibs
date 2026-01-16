<script setup lang="ts">
import { computed, onBeforeMount, ref, watch } from 'vue'
import Cookies from 'js-cookie'
import { navMenu, pageTitle } from '@/views/comDocs/_menu/headermixin'
import {
  onBeforeRouteUpdate,
  onBeforeRouteLeave,
  type RouteLocationNormalizedLoaded as Loaded,
  useRoute,
  useRouter,
} from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import type { Company } from '@/store/types/settings.ts'
import { type LetterFilter, useDocs } from '@/store/pinia/docs'
import type { OfficialLetter } from '@/store/types/docs'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComDocsAuthGuard from '@/components/AuthGuard/ComDocsAuthGuard.vue'
import LetterList from './components/LetterList.vue'
import LetterView from './components/LetterView.vue'
import LetterForm from './components/LetterForm.vue'

const mainViewName = ref('본사 공문 발송')

const letterFilter = ref<LetterFilter>({
  company: '',
  issue_date_from: '',
  issue_date_to: '',
  creator: '',
  ordering: '-created',
  search: '',
  page: 1,
  limit: 10,
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeComDocs)

const docStore = useDocs()
const letter = computed<OfficialLetter | null>(() => docStore.letter)
const letterList = computed(() => docStore.letterList)
const letterCount = computed(() => docStore.letterCount)

const fetchLetter = (pk: number) => docStore.fetchLetter(pk)
const fetchLetterList = (payload: LetterFilter) => docStore.fetchLetterList(payload)
const createLetter = (payload: OfficialLetter) => docStore.createLetter(payload)
const updateLetter = (pk: number, payload: OfficialLetter) => docStore.updateLetter(pk, payload)
const deleteLetter = (pk: number, filter: LetterFilter) => docStore.deleteLetter(pk, filter)
const generatePdf = (pk: number) => docStore.generatePdf(pk)

const [route, router] = [
  useRoute() as Loaded & { name: string },
  useRouter(),
]

watch(route, val => {
  if (val.params.letterId) fetchLetter(Number(val.params.letterId))
  else docStore.removeLetter()
})

const headerKey = ref(0)
const isInitializing = ref(true)

watch(
  company,
  async (newCompany, oldCompany) => {
    if (isInitializing.value) return
    if (newCompany && newCompany !== oldCompany && oldCompany !== undefined)
      await dataSetup(newCompany, route.params?.letterId)
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

const onSubmit = async (payload: OfficialLetter) => {
  if (company.value) {
    const data = { ...payload, company: company.value }

    if (payload.pk) {
      await updateLetter(payload.pk, data)
      await router.replace({ name: `${mainViewName.value} - 보기`, params: { letterId: payload.pk } })
    } else {
      const result = await createLetter(data)
      if (result?.pk) {
        await router.replace({ name: `${mainViewName.value} - 보기`, params: { letterId: result.pk } })
      } else {
        await router.replace({ name: mainViewName.value })
      }
    }
  }
}

const onDelete = async (pk: number) => {
  await deleteLetter(pk, letterFilter.value)
  await router.replace({ name: mainViewName.value })
}

const onGeneratePdf = async (pk: number) => {
  await generatePdf(pk)
}

const dataSetup = async (pk: number, letterId?: string | string[]) => {
  letterFilter.value.company = pk
  await fetchLetterList(letterFilter.value)
  if (letterId) await fetchLetter(Number(letterId))
}

const dataReset = () => {
  docStore.removeLetterList()
  docStore.letterCount = 0
}

const clearQueryString = () => {
  if (Object.keys(route.query).length > 0) {
    router.replace({
      name: route.name,
      params: route.params,
      query: {},
    }).catch(() => {})
  }
}

const comSelect = async (target: number | null, skipClearQuery = false) => {
  if (!skipClearQuery) clearQueryString()

  if (target) {
    Cookies.set('curr-company', `${target}`)
    await comStore.fetchCompany(target)

    const isSlackEntry = skipClearQuery && route.name?.includes('보기')
    if (!isSlackEntry && route.name?.includes('보기')) {
      await router.replace({ name: mainViewName.value })
    }

    if (isInitializing.value) {
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
  } else {
    await dataSetup(company.value ?? comStore.initComId, to.params?.letterId)
  }
})

const urlCompanyId = computed(() => {
  const id = route.query.company
  return id ? parseInt(id as string, 10) : null
})

const loading = ref(true)
onBeforeMount(async () => {
  let companyId = company.value ?? comStore.initComId

  if (urlCompanyId.value) {
    await comSelect(urlCompanyId.value, true)
  } else {
    await dataSetup(companyId, route.params?.letterId)
  }

  isInitializing.value = false
  loading.value = false
})

onBeforeRouteLeave(() => {
  clearQueryString()
})
</script>

<template>
  <ComDocsAuthGuard>
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
            :write-auth="writeAuth"
            @list-filter="listFiltering"
            @page-select="pageSelect"
          />
        </div>

        <div v-else-if="route.name?.includes('보기')">
          <LetterView
            :letter="letter as OfficialLetter"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            :letter-filter="letterFilter"
            @on-delete="onDelete"
            @generate-pdf="onGeneratePdf"
          />
        </div>

        <div v-else-if="route.name?.includes('작성')">
          <LetterForm
            :company="company as number"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @on-submit="onSubmit"
          />
        </div>

        <div v-else-if="route.name?.includes('수정')">
          <LetterForm
            :company="company as number"
            :letter="letter as OfficialLetter"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @on-submit="onSubmit"
          />
        </div>
      </CCardBody>
    </ContentBody>
  </ComDocsAuthGuard>
</template>
