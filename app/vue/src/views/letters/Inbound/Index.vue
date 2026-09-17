<script setup lang="ts">
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/letters/_menu/headermixin'
import {
  onBeforeRouteLeave,
  onBeforeRouteUpdate,
  type RouteLocationNormalizedLoaded as Loaded,
  useRoute,
  useRouter,
} from 'vue-router'
import { useCompany } from '@/store/pinia/company'
import type { Company } from '@/store/types/settings.ts'
import { type InboundLetterFilter, useDocs } from '@/store/pinia/docs'
import type { InboundLetter } from '@/store/types/docs'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComAuthGuard from '@/components/AuthGuard/ComAuthGuard.vue'
import LetterList from './components/LetterList.vue'
import LetterView from './components/LetterView.vue'
import LetterForm, { type LocalAttachmentItem } from './components/LetterForm.vue'

const mainViewName = ref('수신 공문 관리')

const letterFilter = ref<InboundLetterFilter>({
  company: '',
  received_date_from: '',
  received_date_to: '',
  reply_due_date_from: '',
  reply_due_date_to: '',
  status: '',
  recipient_dept: '',
  recipient_manager: '',
  ordering: '-received_date',
  search: '',
  page: 1,
  limit: 10,
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)

const docStore = useDocs()
const letter = computed<InboundLetter | null>(() => docStore.inboundLetter)
const letterList = computed(() => docStore.inboundLetterList)
const letterCount = computed(() => docStore.inboundLetterCount)

// 부서 및 직원 목록 셀렉트 옵션
const departmentOptions = computed<{ value: number; label: string }[]>(() =>
  (comStore.getPkDeparts || [])
    .filter(d => d.value !== undefined)
    .map(d => ({ value: d.value as number, label: d.label })),
)
const staffOptions = computed<{ value: number; label: string }[]>(() =>
  (comStore.getAllStaffs || [])
    .filter(s => s.value !== undefined)
    .map(s => ({ value: s.value as number, label: s.label })),
)

const fetchLetter = (pk: number) => docStore.fetchInboundLetter(pk)
const fetchLetterList = (payload: InboundLetterFilter) => docStore.fetchInboundLetterList(payload)
const createLetter = (payload: FormData) => docStore.createInboundLetter(payload)
const updateLetter = (pk: number, payload: FormData) => docStore.updateInboundLetter(pk, payload)
const deleteLetter = (pk: number, filter: InboundLetterFilter) =>
  docStore.deleteInboundLetter(pk, filter)
const patchLetter = (pk: number, payload: any) => docStore.patchInboundLetter(pk, payload)

const [route, router] = [useRoute() as Loaded & { name: string }, useRouter()]

watch(
  () => route.params.letterId,
  async val => {
    if (val) {
      await fetchLetter(Number(val))
    } else {
      docStore.removeInboundLetter()
    }
  },
)

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

const listFiltering = (payload: InboundLetterFilter) => {
  letterFilter.value = { ...letterFilter.value, ...payload }
  letterFilter.value.company = company.value as number
  fetchLetterList(letterFilter.value)
}

const pageSelect = (page: number) => {
  letterFilter.value.page = page
  fetchLetterList(letterFilter.value)
}

const onSubmit = async (
  formData: FormData,
  attachmentsToUpload?: LocalAttachmentItem[],
  pk?: number,
) => {
  if (company.value) {
    let letterPk: number | null = null

    if (pk) {
      const res = await updateLetter(pk, formData)
      letterPk = res?.pk || pk
    } else {
      const result = await createLetter(formData)
      if (result?.pk) {
        letterPk = result.pk
      }
    }

    // 대기 중인 첨부파일 순차 업로드
    if (letterPk && attachmentsToUpload && attachmentsToUpload.length > 0) {
      for (const att of attachmentsToUpload) {
        const attFormData = new FormData()
        attFormData.append('letter', String(letterPk))
        attFormData.append('file', att.file)
        if (att.name) attFormData.append('name', att.name)
        if (att.quantity) attFormData.append('quantity', att.quantity)
        await docStore.uploadInboundAttachment(letterPk, attFormData)
      }
    }

    if (letterPk) {
      await router.replace({
        name: `${mainViewName.value} - 보기`,
        params: { letterId: letterPk },
      })
    } else {
      await router.replace({ name: mainViewName.value })
    }
  }
}

const onDelete = async (pk: number) => {
  await deleteLetter(pk, letterFilter.value)
  await router.replace({ name: mainViewName.value })
}

const onStatusChange = async (pk: number, newStatus: string) => {
  await patchLetter(pk, { status: newStatus as any })
}

const dataSetup = async (pk: number, letterId?: string | string[]) => {
  letterFilter.value.company = pk
  await Promise.all([
    fetchLetterList(letterFilter.value),
    comStore.fetchAllDepartList(pk),
    comStore.fetchAllStaffList(pk),
  ])
  if (letterId) await fetchLetter(Number(letterId))
}

const dataReset = () => {
  docStore.removeInboundLetterList()
  docStore.inboundLetterCount = 0
}

const clearQueryString = () => {
  if (Object.keys(route.query).length > 0) {
    router
      .replace({
        name: route.name,
        params: route.params,
        query: {},
      })
      .catch(() => {})
  }
}

const comSelect = async (target: number | null, skipClearQuery = false) => {
  if (!skipClearQuery) clearQueryString()

  if (target) {
    localStorage.setItem('curr-company', `${target}`)
    await comStore.fetchCompany(target)

    if (route.name?.includes('보기')) {
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
            :departments="departmentOptions"
            @list-filter="listFiltering"
            @page-select="pageSelect"
          />
        </div>

        <div v-else-if="route.name?.includes('보기')">
          <LetterView
            :letter="letter as InboundLetter"
            :view-route="mainViewName"
            :letter-filter="letterFilter"
            @on-delete="onDelete"
            @on-status-change="onStatusChange"
          />
        </div>

        <div v-else-if="route.name?.includes('작성')">
          <LetterForm
            :company="company as number"
            :view-route="mainViewName"
            :departments="departmentOptions"
            :staffs="staffOptions"
            @on-submit="onSubmit"
          />
        </div>

        <div v-else-if="route.name?.includes('수정')">
          <LetterForm
            :company="company as number"
            :letter="letter as InboundLetter"
            :view-route="mainViewName"
            :departments="departmentOptions"
            :staffs="staffOptions"
            @on-submit="onSubmit"
          />
        </div>
      </CCardBody>
    </ContentBody>
  </ComAuthGuard>
</template>
