from django.urls import path

from .views import (BooksListView, BooksDetailView, BooksCreateView,
                    BooksUpdateView, BooksDeleteView, SubjectsIndexView,
                    SubjectsDetailView, SubjectsCreateView, SubjectsUpdateView,
                    SubjectsDeleteView)

app_name = 'book'

urlpatterns = [
    path('', BooksListView.as_view(), name='index'),
    path('<int:pk>/', BooksDetailView.as_view(), name='detail'),
    path('add/', BooksCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', BooksUpdateView.as_view(), name='edit'),
    path('delete/<int:pk>/', BooksDeleteView.as_view(), name='delete'),

    path('<int:book>/subject/', SubjectsIndexView.as_view(), name='subject_index'),
    path('<int:book>/subject/<int:pk>/', SubjectsDetailView.as_view(), name='subject_detail'),
    path('<int:book>/subject/add/', SubjectsCreateView.as_view(), name='subject_add'),
    path('<int:book>/subject/edit/<int:pk>/', SubjectsUpdateView.as_view(), name='subject_edit'),
    path('<int:book>/subject/delete/<int:pk>/', SubjectsDeleteView.as_view(), name='subject_delete'),
]
