<script setup lang="ts">
import { ref, reactive, onBeforeMount } from 'vue'
import { GridLayout, type LayoutItem } from 'grid-layout-plus'
import MultiSelect from '@/components/MultiSelect/index.vue'

const showItems = ref<number[]>([1, 2])

const selectOptions = [
  { value: 1, label: '내가 맡은 업무' },
  { value: 2, label: '보고한 업무' },
  { value: 3, label: '수정한 업무' },
  { value: 4, label: '지켜 보고 있는 업무' },
  { value: 5, label: '업무' },
  { value: 6, label: '최근 뉴스' },
  { value: 7, label: '달력' },
  { value: 8, label: '문서' },
  { value: 9, label: '소요시간' },
  { value: 10, label: '작업내역' },
]

const getTitle = (n: number | string) =>
  selectOptions.filter(o => o.value === n).map(o => o.label)[0]

const layouts = reactive<LayoutItem[]>([])

const item1 = reactive({ x: 0, y: 0, w: 6, h: 3, i: 1 })
const item2 = reactive({ x: 6, y: 0, w: 6, h: 3, i: 2 })
const item3 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 3 })
const item4 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 4 })
const item5 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 5 })
const item6 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 6 })
const item7 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 7 })
const item8 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 8 })
const item9 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 9 })
const item10 = reactive({ x: 0, y: 0, w: 12, h: 3, i: 10 })

const itemPush = (i: number) => {
  // const item = eval(`item${i}`) as LayoutItemRequired
  if (i === 1) layouts.push(item1)
  if (i === 2) layouts.push(item2)
  if (i === 3) layouts.push(item3)
  if (i === 4) layouts.push(item4)
  if (i === 5) layouts.push(item5)
  if (i === 6) layouts.push(item6)
  if (i === 7) layouts.push(item7)
  if (i === 8) layouts.push(item8)
  if (i === 9) layouts.push(item9)
  if (i === 10) layouts.push(item10)
}

const itemRemove = (item: number) => {
  let index = layouts.indexOf(eval(`item${item}`))
  if (index > -1) layouts.splice(index, 1)
}

const itemClose = (n: number) => {
  const sIndex = showItems.value.indexOf(n)
  showItems.value.splice(sIndex, 1)

  const lIndex = layouts.findIndex(layout => layout.i === n)
  if (lIndex > -1) layouts.splice(lIndex, 1)
}

onBeforeMount(() => {
  showItems.value.forEach(item => {
    layouts.push(eval(`item${item}`))
  })
})
</script>

<template>
  <CCard>
    <CCardBody>
      <CRow class="px-2">
        <CCol style="display: flex; justify-content: flex-end">
          <MultiSelect
            v-model="showItems"
            :options="selectOptions"
            placeholder="추가하기"
            class="multiselect-blue"
            @select="itemPush($event)"
            @deselect="itemRemove($event)"
            @clear="layouts.length = 0"
          />
        </CCol>
      </CRow>
      <!-- Item slot usage -->
      <GridLayout
        v-model:layout="layouts"
        :col-num="12"
        :row-height="30"
        is-draggable
        is-resizable
        vertical-compact
        use-css-transforms
      >
        <template #item="{ item }">
          <div class="w-100 h-100 border p-3">
            <CRow class="px-2 mb-1">
              <CCol>
                <router-link to="">{{ getTitle(item.i) }}</router-link>
                (0)
              </CCol>
              <CCol class="text-right">
                <span class="p-1">
                  <v-icon icon="mdi-cog" color="grey" size="sm" class="pointer mr-2" />
                  <v-icon
                    :icon="'mdi-close-box-outline'"
                    color="grey"
                    size="16"
                    class="pointer"
                    @click="itemClose(Number(item.i))"
                  />
                </span>
              </CCol>
            </CRow>
            <CAlert color="warning"> 표시할 데이터가 없습니다.</CAlert>
          </div>
        </template>
      </GridLayout>
    </CCardBody>
  </CCard>
</template>

<style lang="scss" scoped>
.multiselect-blue {
  --ms-tag-bg: #dbeafe;
  --ms-tag-color: #2563eb;
}

.vgl-layout {
  --vgl-placeholder-bg: green;
}
</style>
