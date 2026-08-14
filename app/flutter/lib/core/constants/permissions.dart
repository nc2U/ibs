/// IBS 권한 상수 (Vue @/store/constants/permissions.ts 와 100% 일치)
abstract class Perm {
  // Project permissions
  static const String projectCreate    = 'project.create';
  static const String projectUpdate    = 'project.update';
  static const String projectClose     = 'project.close';
  static const String projectDelete    = 'project.delete';
  static const String projectPublic    = 'project.public';
  static const String projectModule    = 'project.module';
  static const String projectMember    = 'project.member';
  static const String projectVersion   = 'project.version';
  static const String projectCreateSub = 'project.create_sub';
  static const String projectPubQuery  = 'project.pub_query';
  static const String projectSaveQuery = 'project.save_query';

  // Meeting permissions
  static const String meetingRead          = 'meeting.read';
  static const String meetingCreate        = 'meeting.create';
  static const String meetingUpdate        = 'meeting.update';
  static const String meetingOwnUpdate     = 'meeting.own_update';
  static const String meetingEditConfirmed = 'meeting.edit_confirmed';
  static const String meetingDelete        = 'meeting.delete';
  static const String meetingConfirm       = 'meeting.confirm';

  // Issue permissions
  static const String issueRead                 = 'issue.read';
  static const String issueCreate               = 'issue.create';
  static const String issueUpdate               = 'issue.update';
  static const String issueOwnUpdate            = 'issue.own_update';
  static const String issueCopy                 = 'issue.copy';
  static const String issueRelManage            = 'issue.rel_manage';
  static const String issueSubManage            = 'issue.sub_manage';
  static const String issuePrivate              = 'issue.private';
  static const String issueOwnPrivate           = 'issue.own_private';
  static const String issueCommentCreate        = 'issue.comment_create';
  static const String issueCommentUpdate        = 'issue.comment_update';
  static const String issueCommentOwnUpdate     = 'issue.comment_own_update';
  static const String issuePrivateCommentRead   = 'issue.private_comment_read';
  static const String issuePrivateCommentSet    = 'issue.private_comment_set';
  static const String issueDelete               = 'issue.delete';
  static const String issueWatcherRead          = 'issue.watcher_read';
  static const String issueWatcherCreate        = 'issue.watcher_create';
  static const String issueWatcherDelete        = 'issue.watcher_delete';
  static const String issueImport               = 'issue.import';
  static const String issueCategoryManage       = 'issue.category_manage';

  // News permissions
  static const String newsRead    = 'news.read';
  static const String newsManage  = 'news.manage';
  static const String newsComment = 'news.comment';

  // Docs permissions
  static const String docsRead   = 'docs.read';
  static const String docsCreate = 'docs.create';
  static const String docsUpdate = 'docs.update';
  static const String docsDelete = 'docs.delete';

  // Forum permissions
  static const String forumRead      = 'forum.read';
  static const String forumCreate    = 'forum.create';
  static const String forumUpdate    = 'forum.update';
  static const String forumOwnUpdate = 'forum.own_update';
  static const String forumDelete    = 'forum.delete';
  static const String forumOwnDelete = 'forum.own_delete';
  static const String forumManage    = 'forum.manage';

  // Calendar permissions
  static const String calendarRead = 'calendar.read';

  // Contract permissions
  static const String contractRead       = 'contract.read';
  static const String contractCreate     = 'contract.create';
  static const String contractUpdate     = 'contract.update';
  static const String contractDelete     = 'contract.delete';
  static const String contractSuccession = 'contract.succession';
  static const String contractRelease    = 'contract.release';

  // Payment permissions
  static const String paymentRead   = 'payment.read';
  static const String paymentCreate = 'payment.create';
  static const String paymentUpdate = 'payment.update';
  static const String paymentDelete = 'payment.delete';

  // Notice permissions
  static const String noticeRead   = 'notice.read';
  static const String noticeCreate = 'notice.create';
  static const String noticeUpdate = 'notice.update';
  static const String noticeDelete = 'notice.delete';

  // Ledger permissions
  static const String ledgerRead   = 'ledger.read';
  static const String ledgerCreate = 'ledger.create';
  static const String ledgerUpdate = 'ledger.update';
  static const String ledgerDelete = 'ledger.delete';

  // Site permissions
  static const String siteRead   = 'site.read';
  static const String siteCreate = 'site.create';
  static const String siteUpdate = 'site.update';
  static const String siteDelete = 'site.delete';

  // HR Work permissions
  static const String hrWorkRead   = 'hr_work.read';
  static const String hrWorkCreate = 'hr_work.create';
  static const String hrWorkUpdate = 'hr_work.update';
  static const String hrWorkDelete = 'hr_work.delete';
}
