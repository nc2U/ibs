from django.db.models import Q
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from . forms import ImageFormSet
from . models import Book, Subject, Image


class BooksListView(LoginRequiredMixin, ListView):
    model = Book
    paginate_by = 5

    def get_queryset(self):
        queryset = super(BooksListView, self).get_queryset()  # 기본 구현을 호출해 queryset을 가져온다.
        q = self.request.GET.get('q')

        if q:
            queryset = Book.objects.filter(
                Q(title__icontains=q) |
                Q(author__icontains=q) |
                Q(translator__icontains=q) |
                Q(description__icontains=q)
            ).distinct()

        return queryset


class BooksDetailView(LoginRequiredMixin, DetailView):
    model = Book


class BooksCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Book
    fields = ('title', 'disclosure', 'author', 'translator', 'publisher', 'pub_date', 'description')
    success_message = "새 게시물이 등록되었습니다."

    def get_success_url(self):
        return reverse_lazy('book:detail', args=[self.object.id])

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class BooksUpdateView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = Book
    fields = ('title', 'disclosure', 'author', 'translator', 'publisher', 'pub_date', 'description')
    success_message = "수정하신 내용이 저장되었습니다."

    def get_success_url(self):
        return reverse_lazy('book:detail', args=[self.object.id])


class BooksDeleteView(LoginRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('book:index')


class Breadcrumb:
    def get_breadcrumb(self):
        breadcrumb = []
        try:
            sub = Subject.objects.get(book=self.kwargs['book'], id=self.kwargs['pk'])
        except:
            sub = Subject.objects.filter(book=self.kwargs['book']).first()

        if sub:
            for i in range(1, int(sub.level) + 1):  # 1부터 현재 게시물의 레벨 수만큼 실행(3이면 1, 2, 3)
                bread_subs = Subject.objects.filter(book=self.kwargs['book'], level=i, id__lte=sub.id)
                bread_sub = bread_subs.order_by('-id').first() if sub.level != i else sub
                url = bread_sub.get_absolute_url()
                label = bread_sub.title
                cls1 = 'active' if (sub.level != i) else ''  # 레벨1 제목이 아이디와 같으면 활성 아니면 비활성
                cls2 = 'aria-current=page' if (sub.level != i) else ''

                breadcrumb.append({'url': url, 'label': label, 'cls1': cls1, 'cls2': cls2})
        return breadcrumb


class SearchResult:
    def get_search_list(self):
        search_list = {}
        q = self.request.GET.get('q')

        if q:
            search_list = Subject.objects.filter(
                Q(book_id=self.kwargs['book']) &
                (Q(title__icontains=q) | Q(content__icontains=q))
            ).distinct()
        return search_list


class SubjectsIndexView(LoginRequiredMixin, TemplateView, Breadcrumb, SearchResult):
    template_name = 'book/subjects/index.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SubjectsIndexView, self).get_context_data(**kwargs)
        context['book'] = Book.objects.get(id=self.kwargs['book'])
        context['subjects'] = Subject.objects.filter(book=self.kwargs['book'])
        context['total'] = Subject.objects.filter(book=self.kwargs['book']).count()
        context['object'] = context['subjects'].first()
        context['breadcrumb'] = self.get_breadcrumb()
        context['search_list'] = self.get_search_list()
        return context


class SubjectsDetailView(LoginRequiredMixin, DetailView, Breadcrumb, SearchResult):
    model = Subject
    template_name = 'book/subjects/index.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SubjectsDetailView, self).get_context_data(**kwargs)
        context['book'] = Book.objects.get(id=self.kwargs['book'])
        context['subjects'] = Subject.objects.filter(book=self.kwargs['book'])
        context['total'] = Subject.objects.filter(book=self.kwargs['book']).count()
        context['breadcrumb'] = self.get_breadcrumb()
        context['search_list'] = self.get_search_list()
        return context


class SubjectsCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Subject
    fields = ('title', 'level', 'content')
    success_message = "새 게시물이 등록되었습니다."
    template_name = 'book/subjects/subject_form.html'

    def get_success_url(self):
        return reverse('book:subject_detail', args=(self.kwargs['book'], self.object.id))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SubjectsCreateView, self).get_context_data(**kwargs)
        context['book'] = Book.objects.get(id=self.kwargs['book'])
        subjects = Subject.objects.filter(book=self.kwargs['book'])
        context['last_level'] = subjects.last().level if subjects else 0
        context['formset'] = ImageFormSet(queryset=Image.objects.none())
        return context

    def form_valid(self, form):
        formset = ImageFormSet(self.request.POST, self.request.FILES)
        form.instance.creator = self.request.user
        form.instance.book = Book.objects.get(id=self.kwargs['book'])
        seq_num = Subject.objects.filter(book=self.kwargs['book']).count()
        form.instance.seq = seq_num + 1
        return super(SubjectsCreateView, self).form_valid(form)


class SubjectsUpdateView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = Subject
    fields = ('title', 'level', 'content')
    success_message = "수정하신 내용이 저장되었습니다."
    template_name = 'book/subjects/subject_form.html'

    def get_success_url(self):
        return reverse('book:subject_detail', args=(self.kwargs['book'], self.kwargs['pk']))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SubjectsUpdateView, self).get_context_data(**kwargs)
        context['book'] = Book.objects.get(id=self.kwargs['book'])
        subjects = Subject.objects.filter(book=self.kwargs['book'])
        context['last_level'] = subjects.last().level if subjects else 0
        context['formset'] = ImageFormSet(instance=self.object, queryset=Image.objects.filter(subject=self.object))
        return context

    def form_valid(self, form):
        with transaction.atomic():
            formset = ImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
            # for img in formset:
            #     img.save()
            form.instance.creator = self.request.user
            form.instance.book = Book.objects.get(id=self.kwargs['book'])
            return super(SubjectsUpdateView, self).form_valid(form)


class SubjectsDeleteView(LoginRequiredMixin, DeleteView, Breadcrumb, SearchResult):
    model = Subject
    template_name = 'book/subjects/index.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SubjectsDeleteView, self).get_context_data(**kwargs)
        context['book'] = Book.objects.get(id=self.kwargs['book'])
        context['subjects'] = Subject.objects.filter(book=self.kwargs['book'])
        context['total'] = Subject.objects.filter(book=self.kwargs['book']).count()
        context['breadcrumb'] = self.get_breadcrumb()
        context['search_list'] = self.get_search_list()
        return context
