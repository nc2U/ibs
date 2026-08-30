export const PERM = {
  // WORK_SPACE PERMISSION ---------------------
  // Project permissions
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
  ISSUE_PRIVATE: 'issue.private',
  ISSUE_OWN_PRIVATE: 'issue.own_private',
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
  FORUM_MANAGE: 'forum.manage',

  // Calendar permissions
  CALENDAR_READ: 'calendar.read',
  // WORK_SPACE PERMISSION ---------------------

  // HQ PERMISSION -----------------------------
  // HR Work permissions
  HQ_HR_WORK_READ: 'hq.hr_work.read',
  HQ_HR_WORK_CREATE: 'hq.hr_work.create',
  HQ_HR_WORK_UPDATE: 'hq.hr_work.update',
  HQ_HR_WORK_DELETE: 'hq.hr_work.delete',

  // Company Ledger permissions
  HQ_LEDGER_READ: 'hq.ledger.read',
  HQ_LEDGER_CREATE: 'hq.ledger.create',
  HQ_LEDGER_UPDATE: 'hq.ledger.update',
  HQ_LEDGER_DELETE: 'hq.ledger.delete',
  HQ_LEDGER_MANAGE: 'hq.ledger.manage',
  // HQ PERMISSION -----------------------------

  // PROJECT PERMISSION ------------------------
  // Ledger permissions
  LEDGER_READ: 'ledger.read',
  LEDGER_CREATE: 'ledger.create',
  LEDGER_UPDATE: 'ledger.update',
  LEDGER_DELETE: 'ledger.delete',
  LEDGER_MANAGE: 'ledger.manage',

  // Contract permissions
  CONTRACT_READ: 'contract.read',
  CONTRACT_CREATE: 'contract.create',
  CONTRACT_UPDATE: 'contract.update',
  CONTRACT_DELETE: 'contract.delete',
  CONTRACT_SUCCESSION: 'contract.succession',
  CONTRACT_RELEASE: 'contract.release',

  // Payment permissions
  PAYMENT_READ: 'payment.read',
  PAYMENT_CREATE: 'payment.create',
  PAYMENT_UPDATE: 'payment.update',
  PAYMENT_DELETE: 'payment.delete',

  // Notice permissions
  NOTICE_READ: 'notice.read',
  NOTICE_CREATE: 'notice.create',
  NOTICE_UPDATE: 'notice.update',
  NOTICE_DELETE: 'notice.delete',

  // Site permissions
  SITE_READ: 'site.read',
  SITE_CREATE: 'site.create',
  SITE_UPDATE: 'site.update',
  SITE_DELETE: 'site.delete',
  // PROJECT PERMISSION ------------------------
} as const

export type PermissionCode = (typeof PERM)[keyof typeof PERM]
