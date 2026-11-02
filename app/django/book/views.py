from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Max
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .forms import ImageFormSet
from .models import Book, Subject, Image


class BookOwnerOrStaffRequiredMixin(UserPassesTestMixin):
    """도서 등록자(creator) 또는 관리자(staff/superuser)만 수정/삭제 허용"""

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        return user.is_authenticated and (user == obj.creator or user.is_staff or user.is_superuser)


class SubjectOwnerOrStaffRequiredMixin(UserPassesTestMixin):
    """단원 등록자, 도서 등록자, 또는 관리자(staff/superuser)만 단원 수정/삭제 허용"""

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        return user.is_authenticated and (
            user == obj.creator or user == obj.book.creator or user.is_staff or user.is_superuser
        )


class BookScopedMixin:
    """도서 존재 여부 및 비공개 도서 열람 권한 검증 공통 믹스인"""

    def get_book(self):
        if not hasattr(self, '_cached_book'):
            book = get_object_or_404(Book, id=self.kwargs['book'])
            user = self.request.user
            if not (book.disclosure or user == book.creator or user.is_staff or user.is_superuser):
                raise PermissionDenied('비공개 도서에 접근할 권한이 없습니다.')
            self._cached_book = book
        return self._cached_book


class BooksListView(LoginRequiredMixin, ListView):
    model = Book
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(Q(disclosure=True) | Q(creator=user))

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(author__icontains=q) |
                Q(translator__icontains=q) |
                Q(description__icontains=q)
            ).distinct()

        return queryset


class BooksDetailView(LoginRequiredMixin, DetailView):
    model = Book

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(Q(disclosure=True) | Q(creator=user))
        return queryset


class BooksCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Book
    fields = ('title', 'disclosure', 'author', 'translator', 'publisher', 'pub_date', 'description')
    success_message = "새 게시물이 등록되었습니다."

    def get_success_url(self):
        return reverse_lazy('book:detail', args=[self.object.id])

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class BooksUpdateView(SuccessMessageMixin, LoginRequiredMixin, BookOwnerOrStaffRequiredMixin, UpdateView):
    model = Book
    fields = ('title', 'disclosure', 'author', 'translator', 'publisher', 'pub_date', 'description')
    success_message = "수정하신 내용이 저장되었습니다."

    def get_success_url(self):
        return reverse_lazy('book:detail', args=[self.object.id])


class BooksDeleteView(LoginRequiredMixin, BookOwnerOrStaffRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('book:index')


class Breadcrumb:
    def get_breadcrumb(self, book_id=None, current_subject=None, subjects_list=None):
        book_id = book_id or self.kwargs.get('book')
        pk = self.kwargs.get('pk')

        sub = current_subject
        if not sub and pk:
            if subjects_list:
                sub = next((s for s in subjects_list if s.id == pk), None)
            if not sub:
                try:
                    sub = Subject.objects.get(book_id=book_id, id=pk)
                except (Subject.DoesNotExist, KeyError):
                    pass
        if not sub:
            if subjects_list:
                sub = subjects_list[0] if subjects_list else None
            else:
                sub = Subject.objects.filter(book_id=book_id).order_by('seq', 'id').first()

        breadcrumb = []
        if sub:
            for i in range(1, int(sub.level) + 1):
                if sub.level == i:
                    bread_sub = sub
                elif subjects_list:
                    # 메모리 내에서 level=i, seq <= sub.seq 인 마지막 단원 탐색 (추가 쿼리 0회)
                    candidates = [s for s in subjects_list if s.level == i and s.seq <= sub.seq]
                    bread_sub = candidates[-1] if candidates else None
                else:
                    bread_subs = Subject.objects.filter(book_id=book_id, level=i, seq__lte=sub.seq)
                    bread_sub = bread_subs.order_by('-seq', '-id').first()

                if not bread_sub:
                    continue

                url = bread_sub.get_absolute_url()
                label = bread_sub.title
                is_current = (sub.level == i)
                cls1 = 'active' if is_current else ''
                cls2 = 'aria-current=page' if is_current else ''

                breadcrumb.append({'url': url, 'label': label, 'cls1': cls1, 'cls2': cls2})
        return breadcrumb


class SearchResult:
    def get_search_list(self):
        q = self.request.GET.get('q')
        if q:
            return Subject.objects.filter(
                Q(book_id=self.kwargs['book']) &
                (Q(title__icontains=q) | Q(content__icontains=q))
            ).distinct()
        return Subject.objects.none()


class SubjectsIndexView(LoginRequiredMixin, BookScopedMixin, TemplateView, Breadcrumb, SearchResult):
    template_name = 'book/subjects/index.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_book()
        subjects = list(Subject.objects.filter(book=book).order_by('seq', 'id'))
        first_sub = subjects[0] if subjects else None
        context['book'] = book
        context['subjects'] = subjects
        context['total'] = len(subjects)
        context['object'] = first_sub
        context['breadcrumb'] = self.get_breadcrumb(book.id, current_subject=first_sub, subjects_list=subjects)
        context['search_list'] = self.get_search_list()
        return context


class SubjectsDetailView(LoginRequiredMixin, BookScopedMixin, DetailView, Breadcrumb, SearchResult):
    model = Subject
    template_name = 'book/subjects/index.html'

    def get_queryset(self):
        # Cross-Resource Mismatch 방지: URL의 book 파라미터와 일치하는 단원만 조회
        return super().get_queryset().filter(book_id=self.kwargs['book']).select_related('book', 'creator')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_book()
        subjects = list(Subject.objects.filter(book=book).order_by('seq', 'id'))
        context['book'] = book
        context['subjects'] = subjects
        context['total'] = len(subjects)
        context['breadcrumb'] = self.get_breadcrumb(book.id, current_subject=self.object, subjects_list=subjects)
        context['search_list'] = self.get_search_list()
        return context


class SubjectsCreateView(SuccessMessageMixin, LoginRequiredMixin, BookScopedMixin, CreateView):
    model = Subject
    fields = ('title', 'level', 'content')
    success_message = "새 게시물이 등록되었습니다."
    template_name = 'book/subjects/subject_form.html'

    def get_success_url(self):
        return reverse('book:subject_detail', args=(self.kwargs['book'], self.object.id))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_book()
        subjects = Subject.objects.filter(book=book).order_by('seq', 'id')
        context['book'] = book
        context['last_level'] = subjects.last().level if subjects.exists() else 0
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = ImageFormSet(self.request.POST, self.request.FILES)
            else:
                context['formset'] = ImageFormSet(queryset=Image.objects.none())
        return context

    def form_valid(self, form):
        book = self.get_book()
        formset = ImageFormSet(self.request.POST, self.request.FILES)

        if not formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            # 동시 단원 생성 시 seq 중복 방지를 위한 배타적 행 락킹(select_for_update)
            locked_book = Book.objects.select_for_update().get(id=book.id)
            form.instance.creator = self.request.user
            form.instance.book = locked_book
            max_seq = Subject.objects.filter(book=locked_book).aggregate(Max('seq'))['seq__max'] or 0
            form.instance.seq = max_seq + 1
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()

        return response


class SubjectsUpdateView(SuccessMessageMixin, LoginRequiredMixin, BookScopedMixin, SubjectOwnerOrStaffRequiredMixin, UpdateView):
    model = Subject
    fields = ('title', 'level', 'content')
    success_message = "수정하신 내용이 저장되었습니다."
    template_name = 'book/subjects/subject_form.html'

    def get_queryset(self):
        # Cross-Resource Mismatch 방지: URL의 book 파라미터와 일치하는 단원만 조회
        return super().get_queryset().filter(book_id=self.kwargs['book'])

    def get_success_url(self):
        return reverse('book:subject_detail', args=(self.kwargs['book'], self.kwargs['pk']))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_book()
        subjects = Subject.objects.filter(book=book).order_by('seq', 'id')
        context['book'] = book
        context['last_level'] = subjects.last().level if subjects.exists() else 0
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = ImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
            else:
                context['formset'] = ImageFormSet(instance=self.object, queryset=Image.objects.filter(subject=self.object))
        return context

    def form_valid(self, form):
        formset = ImageFormSet(self.request.POST, self.request.FILES, instance=self.object)

        if not formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()

        return response


class SubjectsDeleteView(LoginRequiredMixin, BookScopedMixin, SubjectOwnerOrStaffRequiredMixin, DeleteView, Breadcrumb, SearchResult):
    model = Subject
    template_name = 'book/subjects/index.html'

    def get_queryset(self):
        # Cross-Resource Mismatch 방지: URL의 book 파라미터와 일치하는 단원만 조회
        return super().get_queryset().filter(book_id=self.kwargs['book'])

    def get_success_url(self):
        return reverse('book:subject_index', args=[self.kwargs['book']])

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_book()
        subjects = list(Subject.objects.filter(book=book).order_by('seq', 'id'))
        context['book'] = book
        context['subjects'] = subjects
        context['total'] = len(subjects)
        context['breadcrumb'] = self.get_breadcrumb(book.id, current_subject=self.object, subjects_list=subjects)
        context['search_list'] = self.get_search_list()
        return context
