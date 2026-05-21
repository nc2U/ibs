[1mdiff --git a/app/vue/src/router/modules/comLedger.ts b/app/vue/src/router/modules/comLedger.ts[m
[1mindex 01266eb031..8c464f4532 100644[m
[1m--- a/app/vue/src/router/modules/comLedger.ts[m
[1m+++ b/app/vue/src/router/modules/comLedger.ts[m
[36m@@ -21,7 +21,7 @@[m [mconst comLedger = {[m
       },[m
     },[m
     {[m
[31m-      path: 'index',[m
[32m+[m[32m      path: 'manage',[m
       name: '본사 거래 내역',[m
       component: () => import('@/views/comLedger/Manage/Index.vue'),[m
       meta: {[m
[1mdiff --git a/app/vue/src/router/modules/proLedger.ts b/app/vue/src/router/modules/proLedger.ts[m
[1mindex 65d0a1fa48..7f16b8d603 100644[m
[1m--- a/app/vue/src/router/modules/proLedger.ts[m
[1m+++ b/app/vue/src/router/modules/proLedger.ts[m
[36m@@ -21,7 +21,7 @@[m [mconst proLedger = {[m
       },[m
     },[m
     {[m
[31m-      path: 'index',[m
[32m+[m[32m      path: 'manage',[m
       name: 'PR 거래 내역',[m
       component: () => import('@/views/proLedger/Manage/Index.vue'),[m
       meta: {[m
