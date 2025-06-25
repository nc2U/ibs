export function buildGraphData(dag: Record<string, any>) {
  const visited = new Set<string>()
  const positions: Record<string, { x: number; y: number }> = {}
  const columns: Record<string, number> = {}

  let y = 0
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
      x: columns[sha] * 0,
      y: y++ * 20,
    }
  }

  Object.keys(dag).forEach(visit)

  return positions
}
