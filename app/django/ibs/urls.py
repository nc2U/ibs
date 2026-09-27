from django.urls import path, include
from django.views.generic import RedirectView

from .views import *

app_name = 'ibs'

urlpatterns = [
    path('', RedirectView.as_view(url='/#/dashboard'), name='home'),
    path('project/', include('project.urls')),
    path('notice/', include('notice.urls')),
    # path('docs/', include('document.urls')),
]
