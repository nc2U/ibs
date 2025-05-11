<script lang="ts" setup>
import { inject, type PropType, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import WatcherAdd from './WatcherAdd.vue'

const props = defineProps({
  issuePk: { type: Number, required: true },
  watchers: { type: Array as PropType<{ pk: number; username: string }[]>, default: () => [] },
})

const refWatcherAdd = ref()

const workManager = inject('workManager')

const route = useRoute()

const workStore = useWork()
const watcherAddSubmit = (payload: number[]) => {
  const form = new FormData()
  payload.forEach(val => form.append('watchers', JSON.stringify(val)))
  workStore.patchIssue(props.issuePk as number, form)
}

const delWatcher = (pk: number) => {
  const form = new FormData()
  form.append('del_watcher', JSON.stringify(pk))
  workStore.patchIssue(props.issuePk as number, form)
}
</script>

<template>
  <!--  <CRow class="mb-3">-->
  <!--    <CCol><h6 class="asideTitle">검색양식</h6></CCol>-->
  <!--  </CRow>-->
  <!--  <CRow class="mb-2">-->
  <!--    <CCol class="col-xxl-5"></CCol>-->
  <!--  </CRow>-->

  <template v-if="workManager && route.name === '(업무) - 보기'">
    <CRow class="mb-1">
      <CCol>
        <h6 class="asideTitle">업무 관람자 ({{ watchers.length }})</h6>
      </CCol>
      <CCol class="text-right">
        <router-link to="" @click="refWatcherAdd.callModal()">추가</router-link>
      </CCol>
    </CRow>
    <CRow v-for="watcher in watchers" :key="watcher.pk">
      <CCol class="col-xxl-5">
        <router-link :to="{ name: '사용자 - 보기', params: { userId: watcher.pk } }">
          {{ watcher.username }}
        </router-link>
        <span @click="delWatcher(watcher.pk)">
          <v-icon icon="mdi-trash-can-outline" size="sm" color="grey" class="ml-2 pointer" />
          <v-tooltip activator="parent" location="right">삭제</v-tooltip>
        </span>
      </CCol>
    </CRow>
  </template>

  <WatcherAdd ref="refWatcherAdd" :watchers="watchers" @watcher-add-submit="watcherAddSubmit" />
</template>

<style lang="scss" scoped>
.asideTitle {
  font-size: 1.1em;
}
</style>
