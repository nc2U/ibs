export function buildGraphData(dag: Record<string, any>) {
  const visited = new Set<string>()
  const positions: Record<string, { x: number; y: number }> = {}
  const columns: Record<string, number> = {}

  let y = Object.keys(dag).length // 최신 커밋이 위로 올라가게 하기 위해 높은 값부터 시작
  let column = 0

  function visit(sha: string, depth = 0) {
    if (visited.has(sha)) return
    visited.add(sha)

    const parents = dag[sha]?.parents || []

    for (const parent of parents) {
      visit(parent, depth + 1)
    }

    // 좌표 지정
    columns[sha] = column++
    positions[sha] = {
      x: 0, // columns[sha] * 0,
      y: y-- * 30, // y 값을 감소 시킴
    }
  }

  Object.keys(dag).forEach(visit)

  return positions
}
