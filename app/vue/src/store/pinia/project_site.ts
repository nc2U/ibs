import api from '@/api'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import {
  type AllSite,
  type Site,
  type AllOwner,
  type SiteOwner,
  type Relation,
  type SiteContract,
} from '@/store/types/project'

export type SiteFilter = {
  project: number | null
  limit?: number | ''
  page?: number
  search?: string
}

export interface OwnerFilter {
  project: number | null
  sort?: string
  limit?: number | ''
  page?: number
  is_use_consent?: '' | '0' | '1'
  search?: string
}

export type ContFilter = {
  project: number | null
  limit?: number | ''
  page?: number
  own_sort?: string
  search?: string
}

export const useSite = defineStore('site', () => {
  const allSites = ref<AllSite[]>([])
  const getSites = computed(() =>
    allSites.value.map((s: AllSite) => ({
      value: s.pk,
      label: s.__str__,
    })),
  )
  const getSitesTotal = ref<{
    project: number
    official: number | null
    returned: number | null
  }>()

  const fetchAllSites = (project: number) => {
    api.get(`/all-site/?project=${project}`).then(res => {
      allSites.value = res.data.results
    })
  }

  const fetchSitesTotal = (project: number) => {
    api.get(`/sites-total/?project=${project}`).then(res => {
      getSitesTotal.value = res.data.results[0]
    })
  }

  const siteList = ref<Site[]>([])
  const getSiteList = computed(() =>
    siteList.value.map((s: Site) => ({
      pk: s.pk,
      project: s.project,
      order: s.order,
      district: s.district,
      lot_number: s.lot_number,
      site_purpose: s.site_purpose,
      official_area: s.official_area,
      returned_area: s.returned_area,
      rights_a: s.rights_a,
      rights_b: s.rights_b,
      dup_issue_date: s.dup_issue_date,
      owners: s.owners?.map(o => o.owner),
    })),
  )
  const siteCount = ref(0)

  const fetchSiteList = (payload: SiteFilter) => {
    const { project, limit, page, search } = payload
    api
      .get(
        `/site/?project=${project}&limit=${limit || 10}&page=${page || 1}&search=${search || ''}`,
      )
      .then(res => {
        siteList.value = res.data.results
        siteCount.value = res.data.count
        fetchSitesTotal(project as number)
      })
      .catch(err => errorHandle(err.response.data))
  }

  const createSite = (payload: { form: FormData; page?: number; search?: string }) => {
    const { page, search, form } = payload
    api
      .post(`/site/`, form)
      .then(res => {
        fetchSiteList({ project: res.data.project, page, search })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const updateSite = (pk: number, payload: { form: FormData; page?: number; search?: string }) => {
    const { page, search, form } = payload
    api
      .put(`/site/${pk}/`, form)
      .then(res => {
        fetchSiteList({ project: res.data.project, page, search })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deleteSite = (pk: number, project: number) => {
    api
      .delete(`/site/${pk}/`)
      .then(() => {
        fetchSiteList({ project })
        message('warning', '', '해당 부지 정보가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))
  }

  const allOwners = ref<AllOwner[]>([])
  const getOwners = computed(() =>
    allOwners.value.map((o: AllOwner) => ({
      value: o.pk,
      label: o.owner,
    })),
  )
  const getOwnersTotal = ref<{
    project: number
    owned_area: number | null
  }>()

  const siteOwner = ref<SiteOwner | null>(null)
  const siteOwnerList = ref<SiteOwner[]>([])
  const siteOwnerCount = ref(0)

  const fetchOwnersTotal = (project: number) => {
    api.get(`/owners-total/?project=${project}`).then(res => {
      getOwnersTotal.value = res.data.results[0]
    })
  }

  const fetchAllOwners = (project: number) => {
    api.get(`/all-owner/?project=${project}`).then(res => {
      allOwners.value = res.data.results
    })
  }

  const fetchSiteOwner = (pk: number) => {
    api
      .get(`/site-owner/${pk}/`)
      .then(res => {
        siteOwner.value = res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchSiteOwnerList = (payload: OwnerFilter) => {
    const { project, limit, page, sort, is_use_consent, search } = payload
    api
      .get(
        `/site-owner/?project=${project}&limit=${limit || 10}&page=${page || 1}&own_sort=${sort || ''}&use_consent=${is_use_consent || ''}&search=${search || ''}`,
      )
      .then(res => {
        siteOwnerList.value = res.data.results
        siteOwnerCount.value = res.data.count
        fetchOwnersTotal(project as number)
      })
      .catch(err => errorHandle(err.response.data))
  }

  const findSiteOwnerPage = async (highlightId: number, filters: OwnerFilter) => {
    let url = `/site-owner/find_page/?highlight_id=${highlightId}`
    url += `&project=${filters.project}`
    if (filters.sort) url += `&own_sort=${filters.sort}`
    if (filters.is_use_consent) url += `&use_consent=${filters.is_use_consent}`
    if (filters.search) url += `&search=${filters.search}`

    try {
      const response = await api.get(url)
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  const createSiteOwner = (payload: SiteOwner & OwnerFilter) => {
    const { limit, page, sort, is_use_consent, search, ...formData } = payload
    api
      .post(`/site-owner/`, formData)
      .then(res => {
        fetchSiteOwnerList({ project: res.data.project, limit, page, sort, is_use_consent, search })
        message()
        console.log('--->', res.data, res.data.sites)
      })
      .catch(err => errorHandle(err.response.data))
  }

  const updateSiteOwner = (payload: SiteOwner & OwnerFilter) => {
    const { pk, limit, page, sort, is_use_consent, search, ...formData } = payload
    api
      .put(`/site-owner/${pk}/`, formData)
      .then(res => {
        fetchSiteOwnerList({ project: res.data.project, limit, page, sort, is_use_consent, search })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deleteSiteOwner = (pk: number, project: number) => {
    api
      .delete(`/site-owner/${pk}/`)
      .then(() => {
        fetchSiteOwnerList({ project })
        message('warning', '', '해당 소유자 정보가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))
  }

  const relationList = ref<Relation[]>([])

  const patchRelation = (payload: Relation & OwnerFilter) => {
    const { pk, project, limit, page, sort, is_use_consent, search, ...relationData } = payload
    api
      .patch(`/site-relation/${pk}/`, relationData)
      .then(() => {
        fetchSiteOwnerList({ project, limit, page, sort, is_use_consent, search })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const siteContList = ref<SiteContract[]>([])
  const siteContCount = ref(0)
  const getContsTotal = ref<{
    project: number
    contracted_area: number | null
  }>()

  const fetchContsTotal = (project: number) => {
    api.get(`/conts-total/?project=${project}`).then(res => {
      getContsTotal.value = res.data.results[0]
    })
  }

  const fetchSiteContList = (payload: ContFilter) => {
    const { project, limit, page, own_sort, search } = payload
    api
      .get(
        `/site-contract/?project=${project}&limit=${limit || 10}&page=${page || 1}&owner__own_sort=${own_sort || ''}&search=${search || ''}`,
      )
      .then(res => {
        siteContList.value = res.data.results
        siteContCount.value = res.data.count
        fetchContsTotal(project as number)
      })
      .catch(err => errorHandle(err.response.data))
  }

  const findSiteContractPage = async (highlightId: number, filters: ContFilter) => {
    let url = `/site-contract/find_page/?highlight_id=${highlightId}`
    url += `&project=${filters.project}`
    if (filters.own_sort) url += `&owner__own_sort=${filters.own_sort}`
    if (filters.search) url += `&search=${filters.search}`

    try {
      const response = await api.get(url)
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  const createSiteCont = (payload: FormData) => {
    api
      .post(`/site-contract/`, payload)
      .then(res => {
        fetchSiteContList({ project: res.data.project })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const updateSiteCont = (pk: number, payload: FormData) => {
    api
      .put(`/site-contract/${pk}/`, payload)
      .then(res => {
        fetchSiteContList({ project: res.data.project })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deleteSiteCont = (pk: number, project: number) => {
    api
      .delete(`/site-contract/${pk}/`)
      .then(() => {
        fetchSiteContList({ project })
        message('warning', '', '해당 부지 매입계약 정보가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))
  }

  return {
    allSites,
    getSites,
    getSitesTotal,
    siteList,
    getSiteList,
    siteCount,

    fetchAllSites,
    fetchSitesTotal,
    fetchSiteList,
    createSite,
    updateSite,
    deleteSite,

    getOwners,
    getOwnersTotal,
    siteOwner,
    siteOwnerList,
    siteOwnerCount,

    fetchAllOwners,
    fetchOwnersTotal,
    fetchSiteOwner,
    fetchSiteOwnerList,
    findSiteOwnerPage,
    createSiteOwner,
    updateSiteOwner,
    deleteSiteOwner,

    relationList,

    patchRelation,

    siteContList,
    siteContCount,
    getContsTotal,

    fetchSiteContList,
    findSiteContractPage,
    createSiteCont,
    updateSiteCont,
    deleteSiteCont,
  }
})
