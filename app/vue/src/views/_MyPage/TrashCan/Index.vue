<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/_MyPage/_menu/headermixin'
import { useDocs } from '@/store/pinia/docs'
import type { TrashDocs as TP } from '@/store/types/docs'
import { type RouteLocationNormalizedLoaded as LoadedRoute, useRoute, useRouter } from 'vue-router'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import TrashDocsList from './components/TrashDocsList.vue'
import TrashDocsView from './components/TrashDocsView.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const mainViewName = ref('휴지통')
const category = ref()
const sort = ref<'docs' | 'board'>('docs')
const page = ref<number>(1)

const docStore = useDocs()
const trashDocs = computed(() => docStore.trashDocs)
const trashDocsList = computed(() => docStore.trashDocsList)
const trashDocsCount = computed(() => docStore.trashDocsCount)

const fetchTrashDocs = (pk: number) => docStore.fetchTrashDocs(pk)
const fetchTrashDocsList = (page?: number) => docStore.fetchTrashDocsList(page)
const restoreDocs = (pk: number) => docStore.restoreDocs(pk)
const deleteTrashDocs = (pk: number, page: number) => docStore.deleteTrashDocs(pk, page)

const [route, router] = [
  useRoute() as LoadedRoute & {
    name: string
  },
  useRouter(),
]

watch(route, val => {
  if (val.params.docsId) fetchTrashDocs(Number(val.params.docsId))
  else docStore.removeTrashDocs()
})

const pageSelect = (p: number) => {
  page.value = p
  fetchTrashDocsList(p)
}

const restoreId = ref<number | null>(null)
const refRestoreModal = ref()
const callRestoreDocs = (pk: number) => {
  restoreId.value = pk
  refRestoreModal.value.callModal()
}

const resModalAction = () => {
  restoreDocs(restoreId.value as number)
  refRestoreModal.value.close()
  router.replace({ name: mainViewName.value })
}

const deleteId = ref<number | null>(null)
const refDeleteModal = ref()
const deleteDocs = (pk: number) => {
  deleteId.value = pk
  refDeleteModal.value.callModal()
}

const delModalAction = () => {
  deleteTrashDocs(deleteId.value as number, page.value)
  refDeleteModal.value.close()
  router.replace({ name: mainViewName.value })
}

const docsId = computed(() => Number(route.params.docsId))

const loading = ref(true)
onBeforeMount(async () => {
  await fetchTrashDocsList(page.value)
  if (docsId.value) await fetchTrashDocs(docsId.value)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

  <ContentBody>
    <CCardBody class="pb-5">
      <div v-if="route.name === mainViewName" class="pt-3">
        <CRow class="pb-2">
          <CCol sm="12" lg="9" xl="6">
            <CRow>
              <CCol class="d-grid gap-2 pr-0">
                <CFormCheck
                  v-model="sort"
                  value="docs"
                  :button="{
                    color: 'primary',
                    variant: 'outline',
                    shape: 'rounded-0',
                  }"
                  type="radio"
                  name="options-outlined"
                  id="primary-outlined"
                  label="문서"
                />
              </CCol>
              <CCol class="d-grid gap-2 pl-0">
                <CFormCheck
                  v-model="sort"
                  value="board"
                  :button="{ color: 'success', variant: 'outline', shape: 'rounded-0' }"
                  type="radio"
                  name="options-outlined"
                  id="success-outlined"
                  label="게시글"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <TrashDocsList
          v-if="sort === 'docs'"
          :trash-docs-list="trashDocsList"
          :trash-docs-count="trashDocsCount"
          :view-route="mainViewName"
          :page="page"
          @page-select="pageSelect"
          @restore-docs="callRestoreDocs"
          @delete-docs="deleteDocs"
        />
        <div v-else>??</div>
      </div>

      <div v-else-if="route.name.includes('보기')" class="pt-3">
        <TrashDocsView
          v-if="sort === 'docs'"
          :category="category as undefined"
          :docs="trashDocs as TP"
          :view-route="mainViewName"
          :curr-page="page"
          @restore-docs="callRestoreDocs"
          @delete-docs="deleteDocs"
        />
      </div>
      <div v-else>??</div>
    </CCardBody>
  </ContentBody>

  <ConfirmModal ref="refRestoreModal">
    <template #header>알림</template>
    <template #default>이 게시물을 휴지통으로부터 복원 하시겠습니까?</template>
    <template #footer>
      <v-btn color="success" @click="resModalAction">삭제 복원</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="refDeleteModal">
    <template #header>알림</template>
    <template #default>삭제 후 복원할 수 없읍니다. 이 게시물을 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="delModalAction">완전 삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
