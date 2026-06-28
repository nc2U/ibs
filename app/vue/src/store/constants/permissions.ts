// Project permissions
export const PERM = {
  PROJECT_CREATE: 'project.create',
  PROJECT_UPDATE: 'project.update',
  PROJECT_CLOSE: 'project.close',
  PROJECT_DELETE: 'project.delete',
  PROJECT_PUBLIC: 'project.public',
  PROJECT_MODULE: 'project.module',
  PROJECT_MEMBER: 'project.member',
  PROJECT_VERSION: 'project.version',
  PROJECT_CREATE_SUB: 'project.create_sub',
  PROJECT_PUB_QUERY: 'project.pub_query',
  PROJECT_SAVE_QUERY: 'project.save_query',

  // Meeting permissions
  MEETING_READ: 'meeting.read',
  MEETING_CREATE: 'meeting.create',
  MEETING_UPDATE: 'meeting.update',
  MEETING_OWN_UPDATE: 'meeting.own_update',
  MEETING_EDIT_CONFIRMED: 'meeting.edit_confirmed',
  MEETING_DELETE: 'meeting.delete',
  MEETING_CONFIRM: 'meeting.confirm',

  // Issue permissions
  ISSUE_READ: 'issue.read',
  ISSUE_CREATE: 'issue.create',
  ISSUE_UPDATE: 'issue.update',
  ISSUE_OWN_UPDATE: 'issue.own_update',
  ISSUE_COPY: 'issue.copy',
  ISSUE_REL_MANAGE: 'issue.rel_manage',
  ISSUE_SUB_MANAGE: 'issue.sub_manage',
  ISSUE_PUBLIC: 'issue.public',
  ISSUE_OWN_PUBLIC: 'issue.own_public',
  ISSUE_COMMENT_CREATE: 'issue.comment_create',
  ISSUE_COMMENT_UPDATE: 'issue.comment_update',
  ISSUE_COMMENT_OWN_UPDATE: 'issue.comment_own_update',
  ISSUE_PRIVATE_COMMENT_READ: 'issue.private_comment_read',
  ISSUE_PRIVATE_COMMENT_SET: 'issue.private_comment_set',
  ISSUE_DELETE: 'issue.delete',
  ISSUE_WATCHER_READ: 'issue.watcher_read',
  ISSUE_WATCHER_CREATE: 'issue.watcher_create',
  ISSUE_WATCHER_DELETE: 'issue.watcher_delete',
  ISSUE_IMPORT: 'issue.import',
  ISSUE_CATEGORY_MANAGE: 'issue.category_manage',

  // News permissions
  NEWS_READ: 'news.read',
  NEWS_MANAGE: 'news.manage',
  NEWS_COMMENT: 'news.comment',

  // Docs permissions
  DOCS_READ: 'docs.read',
  DOCS_CREATE: 'docs.create',
  DOCS_UPDATE: 'docs.update',
  DOCS_DELETE: 'docs.delete',

  // Forum permissions
  FORUM_READ: 'forum.read',
  FORUM_CREATE: 'forum.create',
  FORUM_UPDATE: 'forum.update',
  FORUM_OWN_UPDATE: 'forum.own_update',
  FORUM_DELETE: 'forum.delete',
  FORUM_OWN_DELETE: 'forum.own_delete',
  FORUM_WATCHER_READ: 'forum.watcher_read',
  FORUM_WATCHER_CREATE: 'forum.watcher_create',
  FORUM_WATCHER_DELETE: 'forum.watcher_delete',
  FORUM_MANAGE: 'forum.manage',

  // Calendar permissions
  CALENDAR_READ: 'calendar.read',
} as const

export type PermissionCode = (typeof PERM)[keyof typeof PERM]
