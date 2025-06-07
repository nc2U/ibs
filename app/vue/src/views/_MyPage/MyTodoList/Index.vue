<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/_MyPage/_menu/headermixin'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import TodoListApp from '@/components/TodoListApp/index.vue'

const loading = ref(true)
onBeforeMount(() => {
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" />

  <ContentBody>
    <CCardBody>
      <CRow>
        <CCol class="text-left p-5">
          <TodoListApp />
        </CCol>
      </CRow>
    </CCardBody>
  </ContentBody>
</template>
