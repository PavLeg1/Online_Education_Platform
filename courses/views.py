from django.shortcuts import render
from django.views.generic.list import ListView
from .models import Course
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


# Примесный класс
# Получение базового набора запросов по текущему пользователю 
class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


# Примесный класс
# Устанавливаем текущего пользователя в атрибуте owner 
class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    model = Course

    # Поля модели для компоновки CreateView, UpdateView
    fields = ['subject', 'title', 'slug', 'overview']

    # Используется CreateView, UpdateView, DeleteView
    # чтобы перенаправить пользователя после передачи формы на обработку или удаления  
    success_url = reverse_lazy('manage_course_list')


# template_name - шаблон, который будет использоваться для Creare / Update
class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/form.html'


# # Извлечение курсов созданных текущим пользователем
# class ManageCourseListView(ListView):
#     model = Course
#     template_name = 'courses/manage/course/list.html'

#     def get_queryset(self):
#         qs = super().get_queryset()
#         return qs.filter(owner=self.request.user)
class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'
    permission_required = 'courses.view_course'


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    permission_required = 'courses.delete_course'