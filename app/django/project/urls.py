from django.urls import path

from .views import *

app_name = 'project'

urlpatterns = [
    path('', ProjectList.as_view(), name='index'),
    path('create/', ProjectCreate.as_view(), name='create'),
    path('update/<int:pk>/', ProjectUpdate.as_view(), name='update'),
    path('delete/<int:pk>/', ProjectDelete.as_view(), name='delete'),
    path('settings-ordergroup/', SettingsOrderGroup.as_view(), name='set-ordergroup'),
    path('settings-unit-type/', SettingsUnitType.as_view(), name='set-unit-type'),
    path('settings-floor-type/', SettingsFloorType.as_view(), name='set-floor-type'),
    path('settings-sales-price/', SettingsSalesPrice.as_view(), name='set-sales-price'),
    path('settings-payment-order/', SettingsPaymentOrder.as_view(), name='set-payment-order'),
    path('settings-down-payment/', SettingsDownPayment.as_view(), name='set-down-payment'),
    path('site-manage/', SiteManage.as_view(), name='site'),
    path('site-del/<int:pk>/', site_delete, name='site-del'),
    path('site-owner/', SiteOwnerManage.as_view(), name='site-owner'),
    path('site-relation/', site_relationship_update, name='site-relation'),
    path('site-relation-delete/<int:pk>', site_relationship_delete, name='site-relateion-delete'),
    path('site-contract/', SiteContractManage.as_view(), name='site-contract'),
    path('site-contract-delete/<int:pk>', site_contract_delete, name='site-contract-delete'),
]
