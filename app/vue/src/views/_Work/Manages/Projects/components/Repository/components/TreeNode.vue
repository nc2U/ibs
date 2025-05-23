<script lang="ts" setup>
import { onMounted, ref } from 'vue'
import TreeNode from './TreeNode.vue'

const treeData = ref({})

// GitHub Tree API 호출
const fetchTreeData = async () => {
  const repo = 'owner/repo' // 예: 'octocat/hello-world'
  const sha = 'main' // 브랜치 또는 커밋 SHA
  const token = import.meta.env.VITE_GITHUB_TOKEN // 환경 변수로 토큰 관리

  try {
    const response = await fetch(
      `https://api.github.com/repos/${repo}/git/trees/${sha}?recursive=1`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/vnd.github+json',
        },
      },
    )
    const data = await response.json()
    // API 응답을 트리 구조로 변환
    treeData.value = convertToTree(data.tree)
  } catch (error) {
    console.error('Error fetching tree data:', error)
  }
}

// 트리 데이터를 계층 구조로 변환
const convertToTree = items => {
  const root = { path: '', type: 'tree', children: [] }
  const map = {}

  // 모든 항목을 맵에 저장
  items.forEach(item => {
    map[item.path] = { ...item, children: [] }
  })

  // 계층 구조 생성
  items.forEach(item => {
    const parts = item.path.split('/')
    const parentPath = parts.slice(0, -1).join('/')
    if (parentPath === '') {
      root.children.push(map[item.path])
    } else if (map[parentPath]) {
      map[parentPath].children.push(map[item.path])
    }
  })

  return root
}

onMounted(() => fetchTreeData())
</script>

<template>
  <div class="tree-view">
    <ul class="tree-list">
      <TreeNode :node="treeData" :depth="0" />
    </ul>
  </div>
</template>

<style lang="scss" scoped>
.tree-view {
  font-family: Arial, sans-serif;
}

.tree-list {
  list-style: none;
  padding-left: 0;
}
</style>
