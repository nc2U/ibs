<script lang="ts" setup>
import { type PropType } from 'vue'
import type { Forum } from '@/store/types/forum'
import { useRoute } from 'vue-router'
import { elapsedTime } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'

defineProps({
  forumList: { type: Array as PropType<Forum[]>, default: () => [] },
})

const route = useRoute()

const { can, PERM } = usePerms()
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 35%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 45%" />
    </colgroup>
    <CTableHead>
      <CTableRow color="light" class="text-center border-top">
        <CTableHeaderCell scope="col">게시판</CTableHeaderCell>
        <CTableHeaderCell scope="col">주제</CTableHeaderCell>
        <CTableHeaderCell scope="col">글</CTableHeaderCell>
        <CTableHeaderCell scope="col">최근 게시물</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-for="frm in forumList" :key="frm.pk as number">
        <CTableDataCell class="pl-4">
          <router-link
            :to="{
              name: '(게시판) - 보기',
              params: { projId: route.params.projId, forumId: frm.pk },
            }"
            class="strong"
          >
            {{ frm.name }}
          </router-link>
        </CTableDataCell>
        <CTableDataCell class="text-center">{{ frm.post_count }}</CTableDataCell>
        <CTableDataCell class="text-center">{{ frm.all_post_count }}</CTableDataCell>
        <CTableDataCell class="form-text pl-4">
          <template v-if="frm.last_post">
            <v-chip
              v-if="frm.last_post.is_notice"
              variant="elevated"
              color="primary"
              size="x-small"
              class="mr-2"
            >
              공지
            </v-chip>
            <router-link
              v-if="can(PERM.FORUM_READ)"
              :to="{
                name: '(게시판) - 게시물 보기',
                params: {
                  projId: route.params.projId,
                  forumId: frm.pk,
                  postId: frm.last_post.pk,
                },
              }"
            >
              {{ frm.last_post.title }}
            </router-link>
            <span v-else>{{ frm.last_post.title }}</span>
            <span class="text-grey ml-2">
              by {{ frm.last_post.creator }}, {{ elapsedTime(frm.last_post.created) }}
            </span>
          </template>
          <template v-else>-</template>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
