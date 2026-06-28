<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'

const route = useRoute()
const workStore = useWork()
const issueStore = useIssue()

const loading = ref(true)

// 프로젝트 식별자 추출 (Slug)
const projSlug = computed(() => route.params.projId as string | undefined)

onMounted(async () => {
  loading.value = true
  try {
    // 공통 메타데이터 조회
    await issueStore.fetchTrackerList()
    await issueStore.fetchStatusList()
    await issueStore.fetchPriorityList()

    if (projSlug.value) {
      await workStore.fetchIssueProject(projSlug.value)
      await workStore.fetchVersionList({ project: projSlug.value })
      await issueStore.fetchCategoryList(projSlug.value)
      // status__closed='' 로 진행중/완료 통합 전체 로드 (최대 1000개)
      await issueStore.fetchAllIssueList(projSlug.value, '')
    } else {
      await issueStore.fetchAllIssueList('', '')
    }
  } catch (err) {
    console.error('리포트 데이터를 불러오는 도중 오류 발생:', err)
  } finally {
    loading.value = false
  }
})

// 전체 이슈 목록 캐싱
const allIssues = computed(() => issueStore.allIssueList || [])

// 1. 유형별 (Tracker)
const trackerReport = computed(() => {
  return issueStore.trackerList.map(t => {
    const list = allIssues.value.filter(i => i.tracker?.pk === t.pk)
    const open = list.filter(i => !i.status?.closed).length
    const closed = list.filter(i => i.status?.closed).length
    return { name: t.name, open, closed, total: open + closed }
  })
})

// 2. 우선순위별 (Priority)
const priorityReport = computed(() => {
  return issueStore.priorityList.map(p => {
    const list = allIssues.value.filter(i => i.priority?.pk === p.pk)
    const open = list.filter(i => !i.status?.closed).length
    const closed = list.filter(i => i.status?.closed).length
    return { name: p.name, open, closed, total: open + closed }
  })
})

// 3. 담당자별 (Assignee)
const assigneeReport = computed(() => {
  const assigneesMap = new Map()
  allIssues.value.forEach(i => {
    if (i.assigned_to) {
      const key =
        typeof i.assigned_to === 'object' && i.assigned_to !== null
          ? (i.assigned_to as any).pk
          : i.assigned_to
      assigneesMap.set(key, i.assigned_to)
    }
  })
  const assignees = Array.from(assigneesMap.values())

  const report = assignees.map(a => {
    const aPk = typeof a === 'object' && a !== null ? (a as any).pk : a
    const aName = typeof a === 'object' && a !== null ? (a as any).username : `User #${a}`
    const list = allIssues.value.filter(i => {
      const val =
        typeof i.assigned_to === 'object' && i.assigned_to !== null
          ? (i.assigned_to as any).pk
          : i.assigned_to
      return val === aPk
    })
    const open = list.filter(i => !i.status?.closed).length
    const closed = list.filter(i => i.status?.closed).length
    return { name: aName, open, closed, total: open + closed }
  })

  // 미지정 일감 카운트 추가
  const unassignedList = allIssues.value.filter(i => !i.assigned_to)
  if (unassignedList.length > 0) {
    const open = unassignedList.filter(i => !i.status?.closed).length
    const closed = unassignedList.filter(i => i.status?.closed).length
    report.push({ name: '미지정', open, closed, total: open + closed })
  }

  return report
})

// 4. 작성자/생성자별 (Author)
const creatorReport = computed(() => {
  const creatorsMap = new Map()
  allIssues.value.forEach(i => {
    if (i.creator) {
      const key =
        typeof i.creator === 'object' && i.creator !== null ? (i.creator as any).pk : i.creator
      creatorsMap.set(key, i.creator)
    }
  })
  const creators = Array.from(creatorsMap.values())
  return creators.map(c => {
    const cPk = typeof c === 'object' && c !== null ? (c as any).pk : c
    const cName = typeof c === 'object' && c !== null ? (c as any).username : `User #${c}`
    const list = allIssues.value.filter(i => {
      const val =
        typeof i.creator === 'object' && i.creator !== null ? (i.creator as any).pk : i.creator
      return val === cPk
    })
    const open = list.filter(i => !i.status?.closed).length
    const closed = list.filter(i => i.status?.closed).length
    return { name: cName, open, closed, total: open + closed }
  })
})

// 5. 버전별 (Version)
const versionReport = computed(() => {
  const versions = workStore.versionList || []
  const report = versions.map(v => {
    const list = allIssues.value.filter(i => {
      const val =
        typeof i.fixed_version === 'object' && i.fixed_version !== null
          ? (i.fixed_version as any)?.pk
          : i.fixed_version
      return val === v.pk
    })
    const open = list.filter(i => !i.status?.closed).length
    const closed = list.filter(i => i.status?.closed).length
    return { name: v.name, open, closed, total: open + closed }
  })

  // 미정 버전 추가
  const noVersionList = allIssues.value.filter(i => !i.fixed_version)
  if (noVersionList.length > 0) {
    const open = noVersionList.filter(i => !i.status?.closed).length
    const closed = noVersionList.filter(i => i.status?.closed).length
    report.push({ name: '미지정', open, closed, total: open + closed })
  }
  return report
})

// 6. 범주별 (Category)
const categoryReport = computed(() => {
  const categories = issueStore.categoryList || []
  const report = categories.map(c => {
    const list = allIssues.value.filter(i => {
      const val =
        typeof i.category === 'object' && i.category !== null ? (i.category as any)?.pk : i.category
      return val === c.pk
    })
    const open = list.filter(i => !i.status?.closed).length
    const closed = list.filter(i => i.status?.closed).length
    return { name: c.name, open, closed, total: open + closed }
  })

  // 미지정 카테고리 추가
  const noCatList = allIssues.value.filter(i => !i.category)
  if (noCatList.length > 0) {
    const open = noCatList.filter(i => !i.status?.closed).length
    const closed = noCatList.filter(i => i.status?.closed).length
    report.push({ name: '미지정', open, closed, total: open + closed })
  }
  return report
})

// 요약 수치
const totalOpen = computed(() => allIssues.value.filter(i => !i.status?.closed).length)
const totalClosed = computed(() => allIssues.value.filter(i => i.status?.closed).length)
const totalAll = computed(() => allIssues.value.length)
</script>

<template>
  <CRow class="py-2 mb-3 align-items-center">
    <CCol>
      <h5 class="mb-0 font-weight-bold">
        <v-icon icon="mdi-chart-bar" color="primary" class="mr-2" size="24" />
        업무 보고서
      </h5>
    </CCol>
  </CRow>

  <!-- 로딩바 -->
  <v-row v-if="loading">
    <v-col cols="12" class="text-center py-5">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-3 text-grey-darken-1 font-weight-light">통계 데이터를 분석 중입니다...</div>
    </v-col>
  </v-row>

  <div v-else>
    <!-- 상단 전체 종합 요약 카드 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="4">
        <v-card class="summary-card bg-open" elevation="1">
          <div class="d-flex justify-between align-center p-3">
            <div>
              <span class="text-subtitle-2 text-uppercase text-grey-darken-1">진행중인 업무</span>
              <h3 class="text-h3 font-weight-bold text-success mt-1">{{ totalOpen }}</h3>
            </div>
            <v-icon icon="mdi-folder-open-outline" size="48" color="success" class="opacity-30" />
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card class="summary-card bg-closed" elevation="1">
          <div class="d-flex justify-between align-center p-3">
            <div>
              <span class="text-subtitle-2 text-uppercase text-grey-darken-1">완료된 업무</span>
              <h3 class="text-h3 font-weight-bold text-blue mt-1">{{ totalClosed }}</h3>
            </div>
            <v-icon icon="mdi-check-circle-outline" size="48" color="blue" class="opacity-30" />
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="4">
        <v-card class="summary-card bg-total" elevation="1">
          <div class="d-flex justify-between align-center p-3">
            <div>
              <span class="text-subtitle-2 text-uppercase text-grey-darken-1">전체 업무 수</span>
              <h3 class="text-h3 font-weight-bold text-secondary mt-1">{{ totalAll }}</h3>
            </div>
            <v-icon icon="mdi-library-shelves" size="48" color="secondary" class="opacity-30" />
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- 다차원 리포트 테이블 그리드 -->
    <v-row>
      <!-- 1. 유형별 -->
      <v-col cols="12" md="6" class="mb-4">
        <v-card class="report-card" elevation="2">
          <v-card-title class="bg-light d-flex align-center py-2 px-3">
            <v-icon icon="mdi-tag-multiple" color="amber" class="mr-2" size="20" />
            <span class="text-subtitle-1 font-weight-bold">유형별 요약</span>
          </v-card-title>
          <v-table density="comfortable" class="report-table">
            <thead>
              <tr>
                <th class="text-left font-weight-bold text-grey-darken-2">유형</th>
                <th class="text-right font-weight-bold text-success">진행중</th>
                <th class="text-right font-weight-bold text-blue">완료됨</th>
                <th class="text-right font-weight-bold text-grey-darken-3">합계</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in trackerReport" :key="item.name" class="hover-row">
                <td class="font-weight-medium">{{ item.name }}</td>
                <td class="text-right text-success font-weight-medium">{{ item.open }}</td>
                <td class="text-right text-blue font-weight-medium">{{ item.closed }}</td>
                <td class="text-right font-weight-bold">{{ item.total }}</td>
              </tr>
              <tr v-if="!trackerReport.length">
                <td colspan="4" class="text-center text-grey py-3">유형별 데이터가 없습니다.</td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>

      <!-- 2. 우선순위별 -->
      <v-col cols="12" md="6" class="mb-4">
        <v-card class="report-card" elevation="2">
          <v-card-title class="bg-light d-flex align-center py-2 px-3">
            <v-icon icon="mdi-alert-circle-outline" color="red" class="mr-2" size="20" />
            <span class="text-subtitle-1 font-weight-bold">우선순위별 요약</span>
          </v-card-title>
          <v-table density="comfortable" class="report-table">
            <thead>
              <tr>
                <th class="text-left font-weight-bold text-grey-darken-2">우선순위</th>
                <th class="text-right font-weight-bold text-success">진행중</th>
                <th class="text-right font-weight-bold text-blue">완료됨</th>
                <th class="text-right font-weight-bold text-grey-darken-3">합계</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in priorityReport" :key="item.name" class="hover-row">
                <td class="font-weight-medium">{{ item.name }}</td>
                <td class="text-right text-success font-weight-medium">{{ item.open }}</td>
                <td class="text-right text-blue font-weight-medium">{{ item.closed }}</td>
                <td class="text-right font-weight-bold">{{ item.total }}</td>
              </tr>
              <tr v-if="!priorityReport.length">
                <td colspan="4" class="text-center text-grey py-3">
                  우선순위별 데이터가 없습니다.
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>

      <!-- 3. 담당자별 -->
      <v-col cols="12" md="6" class="mb-4">
        <v-card class="report-card" elevation="2">
          <v-card-title class="bg-light d-flex align-center py-2 px-3">
            <v-icon icon="mdi-account-cowboy-hat" color="blue" class="mr-2" size="20" />
            <span class="text-subtitle-1 font-weight-bold">담당자별 요약</span>
          </v-card-title>
          <v-table density="comfortable" class="report-table">
            <thead>
              <tr>
                <th class="text-left font-weight-bold text-grey-darken-2">담당자</th>
                <th class="text-right font-weight-bold text-success">진행중</th>
                <th class="text-right font-weight-bold text-blue">완료됨</th>
                <th class="text-right font-weight-bold text-grey-darken-3">합계</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in assigneeReport" :key="item.name" class="hover-row">
                <td class="font-weight-medium">{{ item.name }}</td>
                <td class="text-right text-success font-weight-medium">{{ item.open }}</td>
                <td class="text-right text-blue font-weight-medium">{{ item.closed }}</td>
                <td class="text-right font-weight-bold">{{ item.total }}</td>
              </tr>
              <tr v-if="!assigneeReport.length">
                <td colspan="4" class="text-center text-grey py-3">
                  담당자가 지정된 데이터가 없습니다.
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>

      <!-- 4. 생성자별 -->
      <v-col cols="12" md="6" class="mb-4">
        <v-card class="report-card" elevation="2">
          <v-card-title class="bg-light d-flex align-center py-2 px-3">
            <v-icon icon="mdi-account-edit" color="teal" class="mr-2" size="20" />
            <span class="text-subtitle-1 font-weight-bold">업무 생성자별 요약</span>
          </v-card-title>
          <v-table density="comfortable" class="report-table">
            <thead>
              <tr>
                <th class="text-left font-weight-bold text-grey-darken-2">생성자</th>
                <th class="text-right font-weight-bold text-success">진행중</th>
                <th class="text-right font-weight-bold text-blue">완료됨</th>
                <th class="text-right font-weight-bold text-grey-darken-3">합계</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in creatorReport" :key="item.name" class="hover-row">
                <td class="font-weight-medium">{{ item.name }}</td>
                <td class="text-right text-success font-weight-medium">{{ item.open }}</td>
                <td class="text-right text-blue font-weight-medium">{{ item.closed }}</td>
                <td class="text-right font-weight-bold">{{ item.total }}</td>
              </tr>
              <tr v-if="!creatorReport.length">
                <td colspan="4" class="text-center text-grey py-3">생성자별 데이터가 없습니다.</td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>

      <!-- 5. 버전별 -->
      <v-col cols="12" md="6" class="mb-4">
        <v-card class="report-card" elevation="2">
          <v-card-title class="bg-light d-flex align-center py-2 px-3">
            <v-icon icon="mdi-git-branch" color="indigo" class="mr-2" size="20" />
            <span class="text-subtitle-1 font-weight-bold">버전별 요약</span>
          </v-card-title>
          <v-table density="comfortable" class="report-table">
            <thead>
              <tr>
                <th class="text-left font-weight-bold text-grey-darken-2">버전</th>
                <th class="text-right font-weight-bold text-success">진행중</th>
                <th class="text-right font-weight-bold text-blue">완료됨</th>
                <th class="text-right font-weight-bold text-grey-darken-3">합계</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in versionReport" :key="item.name" class="hover-row">
                <td class="font-weight-medium">{{ item.name }}</td>
                <td class="text-right text-success font-weight-medium">{{ item.open }}</td>
                <td class="text-right text-blue font-weight-medium">{{ item.closed }}</td>
                <td class="text-right font-weight-bold">{{ item.total }}</td>
              </tr>
              <tr v-if="!versionReport.length">
                <td colspan="4" class="text-center text-grey py-3">지정된 버전이 없습니다.</td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>

      <!-- 6. 범주별 -->
      <v-col cols="12" md="6" class="mb-4">
        <v-card class="report-card" elevation="2">
          <v-card-title class="bg-light d-flex align-center py-2 px-3">
            <v-icon icon="mdi-folder-grid-outline" color="purple" class="mr-2" size="20" />
            <span class="text-subtitle-1 font-weight-bold">범주별 요약</span>
          </v-card-title>
          <v-table density="comfortable" class="report-table">
            <thead>
              <tr>
                <th class="text-left font-weight-bold text-grey-darken-2">범주</th>
                <th class="text-right font-weight-bold text-success">진행중</th>
                <th class="text-right font-weight-bold text-blue">완료됨</th>
                <th class="text-right font-weight-bold text-grey-darken-3">합계</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in categoryReport" :key="item.name" class="hover-row">
                <td class="font-weight-medium">{{ item.name }}</td>
                <td class="text-right text-success font-weight-medium">{{ item.open }}</td>
                <td class="text-right text-blue font-weight-medium">{{ item.closed }}</td>
                <td class="text-right font-weight-bold">{{ item.total }}</td>
              </tr>
              <tr v-if="!categoryReport.length">
                <td colspan="4" class="text-center text-grey py-3">지정된 범주가 없습니다.</td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.summary-card {
  border-radius: 5px !important;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1) !important;
}

.bg-open {
  background: linear-gradient(135deg, #f1fbf4 0%, #ffffff 100%);
}

.bg-closed {
  background: linear-gradient(135deg, #f3f7fd 0%, #ffffff 100%);
}

.bg-total {
  background: linear-gradient(135deg, #f7f8f9 0%, #ffffff 100%);
}

.opacity-30 {
  opacity: 0.35;
}

.report-card {
  border-radius: 5px !important;
  border: 1px solid rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.report-card:hover {
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08) !important;
}

.bg-light {
  background-color: #fafbfc !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.report-table th {
  font-size: 0.85rem !important;
  border-bottom: 2px solid rgba(0, 0, 0, 0.08) !important;
}

.report-table td {
  font-size: 0.9rem !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
}

.hover-row {
  transition: background-color 0.2s ease;
}

.hover-row:hover {
  background-color: rgba(24, 103, 192, 0.03) !important;
}
</style>
