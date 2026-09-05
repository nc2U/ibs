<script lang="ts" setup>
import { computed, ref, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import { diffDate } from '@/utils/baseMixins.ts'
import type { Version } from '@/store/types/work_project.ts'
import NoData from '@/components/NoData/Index.vue'

const props = defineProps({
  versionList: { type: Array as PropType<Version[]>, default: () => [] },
})

const route = useRoute()
const projId = computed(() => (route.params.projId as string) || '')

// Collapsed state for version groups
const expandedVersions = ref<Record<number, boolean>>({})

// Toggle individual version expand
const toggleExpand = (verPk?: number) => {
  if (!verPk) return
  expandedVersions.value[verPk] = !expandedVersions.value[verPk]
}

// Expand all / Collapse all
const allExpanded = ref(true)
const toggleAll = () => {
  allExpanded.value = !allExpanded.value
  props.versionList.forEach(v => {
    if (v.pk) expandedVersions.value[v.pk] = allExpanded.value
  })
}

// Initialize all expanded by default
props.versionList.forEach(v => {
  if (v.pk && expandedVersions.value[v.pk] === undefined) {
    expandedVersions.value[v.pk] = true
  }
})

// Time Range Calculation
const viewMonthsRange = ref<3 | 6 | 12>(6)

const timelineStart = computed(() => {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  d.setDate(1)
  return d
})

const timelineEnd = computed(() => {
  const d = new Date(timelineStart.value)
  d.setMonth(d.getMonth() + viewMonthsRange.value)
  return d
})

const totalTimelineDays = computed(() => {
  const diffTime = timelineEnd.value.getTime() - timelineStart.value.getTime()
  return Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)))
})

// Generate Month columns
interface MonthCol {
  label: string
  year: number
  month: number
  widthPercent: number
}

const monthColumns = computed<MonthCol[]>(() => {
  const cols: MonthCol[] = []
  const start = new Date(timelineStart.value)
  const totalDays = totalTimelineDays.value

  for (let i = 0; i < viewMonthsRange.value; i++) {
    const currentYear = start.getFullYear()
    const currentMonth = start.getMonth()

    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate()
    const widthPct = (daysInMonth / totalDays) * 100

    cols.push({
      label: `${currentYear}.${String(currentMonth + 1).padStart(2, '0')}`,
      year: currentYear,
      month: currentMonth + 1,
      widthPercent: widthPct,
    })

    start.setMonth(start.getMonth() + 1)
  }

  return cols
})

// Position calculations
const getPositionPercent = (dateStr?: string | null) => {
  if (!dateStr) return null
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return null

  const diffTime = d.getTime() - timelineStart.value.getTime()
  const days = diffTime / (1000 * 60 * 60 * 24)
  const pct = (days / totalTimelineDays.value) * 100
  return Math.max(0, Math.min(100, pct))
}

const todayPosition = computed(() => {
  const now = new Date()
  return getPositionPercent(now.toISOString())
})

// Calculate bar left & width for items
const getBarCoordinates = (startDateStr?: string | null, dueDateStr?: string | null) => {
  let startPct = getPositionPercent(startDateStr)
  let endPct = getPositionPercent(dueDateStr)

  if (startPct === null && endPct === null) {
    return { left: '0%', width: '0%', isVisible: false }
  }

  if (startPct === null && endPct !== null) {
    startPct = Math.max(0, endPct - 8)
  } else if (startPct !== null && endPct === null) {
    endPct = Math.min(100, startPct + 8)
  }

  const left = Math.min(startPct!, endPct!)
  const width = Math.max(2.5, Math.abs(endPct! - startPct!))

  return {
    left: `${left}%`,
    width: `${width}%`,
    isVisible: true,
  }
}
</script>

<template>
  <div class="roadmap-gantt-wrapper mt-3">
    <!-- Controls Bar -->
    <div class="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
      <div class="d-flex align-items-center gap-2">
        <v-btn size="x-small" variant="tonal" color="primary" @click="toggleAll">
          <v-icon :icon="allExpanded ? 'mdi-collapse-all' : 'mdi-expand-all'" size="14" class="mr-1" />
          {{ allExpanded ? '모두 접기' : '모두 펼치기' }}
        </v-btn>

        <span class="text-muted small ml-2">
          표시 범위:
        </span>
        <v-btn-toggle
          v-model="viewMonthsRange"
          mandatory
          density="compact"
          variant="outlined"
          color="primary"
          style="height: 26px"
        >
          <v-btn :value="3" size="x-small">3개월</v-btn>
          <v-btn :value="6" size="x-small">6개월</v-btn>
          <v-btn :value="12" size="x-small">1년</v-btn>
        </v-btn-toggle>
      </div>

      <div class="d-flex align-items-center gap-3 text-muted small">
        <span class="d-flex align-items-center">
          <span class="legend-dot bg-success mr-1"></span> 완료
        </span>
        <span class="d-flex align-items-center">
          <span class="legend-dot bg-primary mr-1"></span> 진행 중
        </span>
        <span class="d-flex align-items-center">
          <span class="legend-dot bg-danger mr-1"></span> 지연/경고
        </span>
      </div>
    </div>

    <!-- Empty state -->
    <NoData v-if="!versionList.length" />

    <!-- Gantt Layout Grid -->
    <div v-else class="gantt-container border rounded bg-white shadow-sm">
      <div class="gantt-inner">
        <!-- Gantt Header -->
        <div class="gantt-header d-flex border-bottom bg-light">
          <!-- Left Label Column -->
          <div class="gantt-label-col border-end p-2 fw-bold text-secondary small">
            단계 / 업무명
          </div>

          <!-- Right Timeline Months Scale -->
          <div class="gantt-timeline-area position-relative d-flex flex-grow-1">
            <div
              v-for="m in monthColumns"
              :key="`${m.year}-${m.month}`"
              class="month-cell text-center border-end p-2 small font-weight-bold text-secondary"
              :style="{ width: `${m.widthPercent}%` }"
            >
              {{ m.label }}
            </div>

            <!-- Red Today Line -->
            <div
              v-if="todayPosition !== null"
              class="today-line"
              :style="{ left: `${todayPosition}%` }"
              title="오늘"
            >
              <span class="today-badge">오늘</span>
            </div>
          </div>
        </div>

        <!-- Gantt Rows Body -->
        <div class="gantt-body">
          <div v-for="ver in versionList" :key="ver.pk" class="version-group border-bottom">
            <!-- Version Row -->
            <div class="gantt-row version-row d-flex align-items-center">
              <!-- Version Title and Stats -->
              <div class="gantt-label-col border-end p-2 d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center text-truncate mr-2">
                  <v-btn
                    icon
                    size="x-small"
                    variant="text"
                    density="compact"
                    class="mr-1"
                    @click="toggleExpand(ver.pk)"
                  >
                    <v-icon
                      :icon="expandedVersions[ver.pk!] ? 'mdi-chevron-down' : 'mdi-chevron-right'"
                      size="16"
                    />
                  </v-btn>
                  <router-link
                    :to="{ name: '(로드맵) - 보기', params: { projId, verId: ver.pk } }"
                    class="fw-bold text-dark text-truncate text-decoration-none small"
                  >
                    {{ ver.name }}
                  </router-link>
                </div>

                <div class="d-flex align-items-center gap-1 flex-shrink-0">
                  <v-chip
                    size="x-small"
                    :color="ver.status === '3' ? 'success' : ver.status === '2' ? 'grey' : 'primary'"
                    label
                    style="font-size: 10px; height: 18px"
                  >
                    {{ ver.status_desc || '진행' }}
                  </v-chip>
                  <span class="text-muted small" style="font-size: 11px">
                    {{ (ver.done_ratio ?? 0).toFixed(0) }}%
                  </span>
                </div>
              </div>

              <!-- Version Timeline Bar -->
              <div class="gantt-timeline-area position-relative flex-grow-1 p-2">
                <template v-if="ver.effective_date">
                  <div
                    v-if="getBarCoordinates(null, ver.effective_date).isVisible"
                    class="gantt-bar version-bar"
                    :style="{
                      left: getBarCoordinates(null, ver.effective_date).left,
                      width: getBarCoordinates(null, ver.effective_date).width,
                    }"
                  >
                    <div
                      class="bar-fill bg-success"
                      :style="{ width: `${ver.done_ratio ?? 0}%` }"
                    ></div>
                    <span class="bar-label">
                      목표: {{ ver.effective_date }} ({{ (ver.done_ratio ?? 0).toFixed(0) }}%)
                    </span>
                  </div>
                </template>
                <div v-else class="text-muted small fst-italic px-2" style="font-size: 11px">
                  목표일 미지정
                </div>
              </div>
            </div>

            <!-- Issues List within Version -->
            <div v-if="expandedVersions[ver.pk!] && (ver.recent_issues?.length || ver.issues?.length)">
              <div
                v-for="issue in ver.recent_issues || ver.issues || []"
                :key="issue.pk"
                class="gantt-row issue-row d-flex align-items-center bg-light border-top"
              >
                <!-- Issue Title and Assignee -->
                <div class="gantt-label-col border-end p-2 pl-4 d-flex align-items-center justify-content-between">
                  <div class="d-flex align-items-center text-truncate mr-2">
                    <span class="badge bg-secondary-subtle text-secondary mr-1" style="font-size: 10px">
                      {{ issue.tracker?.name || '업무' }}
                    </span>
                    <router-link
                      :to="{
                        name: '(업무) - 보기',
                        params: { projId, issueId: issue.pk },
                      }"
                      class="text-truncate text-decoration-none small text-dark"
                    >
                      #{{ issue.pk }} {{ issue.subject }}
                    </router-link>
                  </div>

                  <span v-if="issue.assigned_to" class="text-muted small flex-shrink-0" style="font-size: 11px">
                    {{ issue.assigned_to.username }}
                  </span>
                </div>

                <!-- Issue Timeline Bar -->
                <div class="gantt-timeline-area position-relative flex-grow-1 p-2">
                  <div
                    class="gantt-bar issue-bar"
                    :class="{
                      'is-closed': issue.status?.closed,
                      'is-overdue': !issue.status?.closed && (issue as any).due_date && diffDate((issue as any).due_date) < 0,
                    }"
                    :style="{
                      left: getBarCoordinates((issue as any).start_date, (issue as any).due_date || ver.effective_date).left,
                      width: getBarCoordinates((issue as any).start_date, (issue as any).due_date || ver.effective_date).width,
                    }"
                  >
                    <div
                      class="bar-fill"
                      :class="issue.status?.closed ? 'bg-success' : 'bg-primary'"
                      :style="{ width: `${issue.done_ratio || 0}%` }"
                    ></div>
                    <span class="bar-label">
                      {{ issue.done_ratio || 0 }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.roadmap-gantt-wrapper {
  width: 100%;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.gantt-container {
  overflow-x: auto;
}

.gantt-inner {
  min-width: 860px;
}

.gantt-label-col {
  width: 320px;
  min-width: 320px;
  max-width: 320px;
  background-color: inherit;
}

.gantt-timeline-area {
  min-height: 38px;
}

.month-cell {
  white-space: nowrap;
}

.gantt-row {
  min-height: 42px;
  transition: background-color 0.15s ease;
}

.version-row:hover {
  background-color: #f8fafc;
}

.issue-row:hover {
  background-color: #f1f5f9;
}

.gantt-bar {
  position: absolute;
  top: 8px;
  height: 24px;
  border-radius: 4px;
  background-color: #e2e8f0;
  overflow: hidden;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  transition: width 0.2s ease, left 0.2s ease;
}

.version-bar {
  background-color: #cbd5e1;
  font-weight: 600;
  border: 1px solid #94a3b8;
}

.issue-bar {
  height: 20px;
  top: 10px;
  border: 1px solid #cbd5e1;
}

.issue-bar.is-overdue {
  border-color: #ef4444;
  background-color: #fee2e2;
}

.bar-fill {
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  opacity: 0.65;
  transition: width 0.3s ease;
}

.bar-label {
  position: relative;
  z-index: 2;
  font-size: 10px;
  padding: 0 6px;
  white-space: nowrap;
  color: #1e293b;
}

.today-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: #ef4444;
  z-index: 10;
  pointer-events: none;
}

.today-badge {
  position: absolute;
  top: -2px;
  left: -14px;
  background-color: #ef4444;
  color: #fff;
  font-size: 9px;
  padding: 1px 3px;
  border-radius: 3px;
}
</style>
