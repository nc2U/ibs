from django.urls import path

from .views import (install_check_step, create_superuser, create_company,
                    create_project, pass_create_project)

app_name = 'install'

urlpatterns = [
    path('', install_check_step),
    path('create/superuser/', create_superuser, name='create_superuser'),
    path('create/company/', create_company, name='create_company'),
    path('create/project/', create_project, name='create_project'),
    path('create/pass_project/', pass_create_project, name='pass_create_project')
    # path('', include('django.contrib.auth.urls')),
    # path('register/', UserCreateView.as_view(), name='register'),
    # path('register/done/', UserCreateDoneTV.as_view(), name='register_done'),
]
