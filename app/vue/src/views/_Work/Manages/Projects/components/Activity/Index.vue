<script lang="ts" setup>
import { onBeforeMount, type PropType, ref } from 'vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ActivityLogList from '@/views/_Work/Manages/Activity/components/ActivityLogsComponent.vue'
import AsideActivity from '@/views/_Work/Manages/Activity/components/aside/AsideActivity.vue'

defineProps({
  toDate: { type: Date, required: true },
  activityFilter: { type: Object as PropType<any>, default: () => null },
})

const emit = defineEmits(['aside-visible', 'to-back', 'to-next'])

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const toDate = ref(new Date())

const toBack = (date: Date) => emit('to-back', date)
const toNext = (date: Date) => emit('to-next', date)

onBeforeMount(() => {
  emit('aside-visible', true)
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <ActivityLogList
        :to-date="toDate"
        :activity-filter="activityFilter"
        @to-back="toBack"
        @to-next="toNext"
      />
    </template>

    <template v-slot:aside>
      <AsideActivity :to-date="toDate" />
      <!--        :has-subs="!!issueProject?.sub_projects?.length"-->
      <!--        @filter-activity="filterActivity"-->
    </template>
  </ContentBody>
</template>
