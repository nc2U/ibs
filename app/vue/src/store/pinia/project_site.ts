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
    incorporated: number | null
  }>()

  const fetchAllSites = (project: number) =>
    api
      .get(`/all-site/?project=${project}`)
      .then(res => {
        allSites.value = res.data.results
      })
      .catch(err => errorHandle(err))

  const fetchSitesTotal = (project: number) =>
    api
      .get(`/sites-total/?project=${project}`)
      .then(res => {
        getSitesTotal.value = res.data.results?.[0]
      })
      .catch(err => errorHandle(err))

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
      incorporated_area: s.incorporated_area,
      rights_a: s.rights_a,
      rights_b: s.rights_b,
      dup_issue_date: s.dup_issue_date,
      owners: s.owners?.map(o => o.owner),
    })),
  )
  const siteCount = ref(0)

  const fetchSiteList = (payload: SiteFilter) => {
    const { project, limit, page, search } = payload
    const params = new URLSearchParams({
      project: String(project ?? ''),
      limit: String(limit || 10),
      page: String(page || 1),
      search: search || '',
    })
    return api
      .get(`/site/?${params.toString()}`)
      .then(res => {
        siteList.value = res.data.results
        siteCount.value = res.data.count
        return fetchSitesTotal(project as number)
      })
      .catch(err => errorHandle(err))
  }

  const createSite = (payload: {
    form: FormData
    limit?: number | ''
    page?: number
    search?: string
  }): Promise<boolean> => {
    const { limit, page, search, form } = payload
    return api
      .post(`/site/`, form)
      .then(res =>
        fetchSiteList({ project: res.data.project, limit, page, search }).then(() => {
          message()
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })
  }

  const updateSite = (
    pk: number,
    payload: { form: FormData; limit?: number | ''; page?: number; search?: string },
  ): Promise<boolean> => {
    const { limit, page, search, form } = payload
    return api
      .put(`/site/${pk}/`, form)
      .then(res =>
        fetchSiteList({ project: res.data.project, limit, page, search }).then(() => {
          message()
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })
  }

  const deleteSite = (
    pk: number,
    project: number,
    filters?: Partial<SiteFilter>,
  ): Promise<boolean> =>
    api
      .delete(`/site/${pk}/`)
      .then(() =>
        fetchSiteList({ ...filters, project }).then(() => {
          message('warning', '', '해당 부지 정보가 삭제되었습니다.')
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })

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

  const fetchOwnersTotal = (project: number) =>
    api
      .get(`/owners-total/?project=${project}`)
      .then(res => {
        getOwnersTotal.value = res.data.results?.[0]
      })
      .catch(err => errorHandle(err))

  const fetchAllOwners = (project: number) =>
    api
      .get(`/all-owner/?project=${project}`)
      .then(res => {
        allOwners.value = res.data.results
      })
      .catch(err => errorHandle(err))

  const fetchSiteOwner = (pk: number) =>
    api
      .get(`/site-owner/${pk}/`)
      .then(res => {
        siteOwner.value = res.data
      })
      .catch(err => errorHandle(err))

  const fetchSiteOwnerList = (payload: OwnerFilter) => {
    const { project, limit, page, sort, is_use_consent, search } = payload
    const params = new URLSearchParams({
      project: String(project ?? ''),
      limit: String(limit || 10),
      page: String(page || 1),
      own_sort: sort || '',
      use_consent: is_use_consent || '',
      search: search || '',
    })
    return api
      .get(`/site-owner/?${params.toString()}`)
      .then(res => {
        siteOwnerList.value = res.data.results
        siteOwnerCount.value = res.data.count
        return fetchOwnersTotal(project as number)
      })
      .catch(err => errorHandle(err))
  }

  const findSiteOwnerPage = async (highlightId: number, filters: OwnerFilter) => {
    const params = new URLSearchParams({
      highlight_id: String(highlightId),
      project: String(filters.project ?? ''),
    })
    if (filters.sort) params.append('own_sort', filters.sort)
    if (filters.is_use_consent) params.append('use_consent', filters.is_use_consent)
    if (filters.search) params.append('search', filters.search)

    try {
      const response = await api.get(`/site-owner/find_page/?${params.toString()}`)
      return response.data.page
    } catch (err: unknown) {
      errorHandle(err)
      return 1
    }
  }

  const createSiteOwner = (payload: SiteOwner & OwnerFilter): Promise<boolean> => {
    const { limit, page, sort, is_use_consent, search, ...formData } = payload
    return api
      .post(`/site-owner/`, formData)
      .then(res =>
        fetchSiteOwnerList({
          project: res.data.project,
          limit,
          page,
          sort,
          is_use_consent,
          search,
        }).then(() => {
          message()
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })
  }

  const updateSiteOwner = (payload: SiteOwner & OwnerFilter): Promise<boolean> => {
    const { pk, limit, page, sort, is_use_consent, search, ...formData } = payload
    return api
      .put(`/site-owner/${pk}/`, formData)
      .then(res =>
        fetchSiteOwnerList({
          project: res.data.project,
          limit,
          page,
          sort,
          is_use_consent,
          search,
        }).then(() => {
          message()
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })
  }

  const deleteSiteOwner = (
    pk: number,
    project: number,
    filters?: Partial<OwnerFilter>,
  ): Promise<boolean> =>
    api
      .delete(`/site-owner/${pk}/`)
      .then(() =>
        fetchSiteOwnerList({ ...filters, project }).then(() => {
          message('warning', '', '해당 소유자 정보가 삭제되었습니다.')
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })

  const relationList = ref<Relation[]>([])

  const patchRelation = (payload: Relation & OwnerFilter): Promise<boolean> => {
    const { pk, project, limit, page, sort, is_use_consent, search, ...relationData } = payload
    return api
      .patch(`/site-relation/${pk}/`, relationData)
      .then(() =>
        fetchSiteOwnerList({ project, limit, page, sort, is_use_consent, search }).then(() => {
          message()
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })
  }

  const siteContList = ref<SiteContract[]>([])
  const siteContCount = ref(0)
  const getContsTotal = ref<{
    project: number
    contracted_area: number | null
  }>()

  const fetchContsTotal = (project: number) =>
    api
      .get(`/conts-total/?project=${project}`)
      .then(res => {
        getContsTotal.value = res.data.results?.[0]
      })
      .catch(err => errorHandle(err))

  const fetchSiteContList = (payload: ContFilter) => {
    const { project, limit, page, own_sort, search } = payload
    const params = new URLSearchParams({
      project: String(project ?? ''),
      limit: String(limit || 10),
      page: String(page || 1),
      owner__own_sort: own_sort || '',
      search: search || '',
    })
    return api
      .get(`/site-contract/?${params.toString()}`)
      .then(res => {
        siteContList.value = res.data.results
        siteContCount.value = res.data.count
        return fetchContsTotal(project as number)
      })
      .catch(err => errorHandle(err))
  }

  const findSiteContractPage = async (highlightId: number, filters: ContFilter) => {
    const params = new URLSearchParams({
      highlight_id: String(highlightId),
      project: String(filters.project ?? ''),
    })
    if (filters.own_sort) params.append('owner__own_sort', filters.own_sort)
    if (filters.search) params.append('search', filters.search)

    try {
      const response = await api.get(`/site-contract/find_page/?${params.toString()}`)
      return response.data.page
    } catch (err: unknown) {
      errorHandle(err)
      return 1
    }
  }

  const createSiteCont = (payload: FormData, filters?: Partial<ContFilter>): Promise<boolean> =>
    api
      .post(`/site-contract/`, payload)
      .then(res =>
        fetchSiteContList({ ...filters, project: res.data.project }).then(() => {
          message()
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })

  const updateSiteCont = (
    pk: number,
    payload: FormData,
    filters?: Partial<ContFilter>,
  ): Promise<boolean> =>
    api
      .put(`/site-contract/${pk}/`, payload)
      .then(res =>
        fetchSiteContList({ ...filters, project: res.data.project }).then(() => {
          message()
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })

  const deleteSiteCont = (
    pk: number,
    project: number,
    filters?: Partial<ContFilter>,
  ): Promise<boolean> =>
    api
      .delete(`/site-contract/${pk}/`)
      .then(() =>
        fetchSiteContList({ ...filters, project }).then(() => {
          message('warning', '', '해당 부지 매입계약 정보가 삭제되었습니다.')
          return true
        }),
      )
      .catch(err => {
        errorHandle(err)
        return false
      })

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
