import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account'
import type { TrashDocs } from '@/store/types/docs'

export function useTrashPermissions() {
  const { can, canGlobal, PERM } = usePerms()
  const accStore = useAccount()

  const isOwnerOrAdmin = (doc: TrashDocs | null | undefined) =>
    !!doc &&
    (!!accStore.superAuth ||
      !!accStore.workManager ||
      (!!doc.creator && doc.creator === accStore.userInfo?.username))

  const canManageTrashDoc = (
    doc: TrashDocs | null | undefined,
    action: 'update' | 'delete',
  ): boolean => {
    if (!doc || !isOwnerOrAdmin(doc)) return false
    const allPerm = action === 'update' ? PERM.DOCS_UPDATE : PERM.DOCS_DELETE
    const ownPerm = action === 'update' ? PERM.DOCS_OWN_UPDATE : PERM.DOCS_OWN_DELETE
    if (doc.project_slug) {
      return can(allPerm, doc.project_slug) || can(ownPerm, doc.project_slug)
    }
    return (
      !!accStore.superAuth || !!accStore.workManager || canGlobal(allPerm) || canGlobal(ownPerm)
    )
  }

  return {
    canManageTrashDoc,
  }
}
