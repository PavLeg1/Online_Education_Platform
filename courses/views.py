from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.list import ListView
from .models import Course
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.base import TemplateResponseMixin, View
from .forms import ModuleFormSet
from django.forms.models import modelform_factory
from django.apps import apps
from .models import Module, Content


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


# Обрабатывает набор форм, служищий для обновления, добавления, удаления
# TemplateResponseMixin - прорисовка шаблонов и возврат HTTP-ответа
# View - Базовое представление Django на основе класса
class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    # Избегаем повторения исходного кода компоновки набора форм
    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)
    
    # Метод предоставляется представлением View
    # Принимает запрос и делегирует более низкоуровневому методу, который
    # ищет совпадение HTTP-методу 
    # если GET - вызывается get(), если POST - post() 
    def dispatch(self, request, pk):
        self.course = get_object_or_404(Course,
                                        id=pk,
                                        owner=request.user)
        return super().dispatch(request, pk)
    
    # Для запросов методом GET
    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({
            'course': self.course,
            'formset': formset})

    # Для запросов методом POST
    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({
            'course': self.course,
            'formset': formset})
    

class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None 
    obj = None
    template_name = 'courses/manage/content/form.html'


    # Проверка содержимого на принадлежность к типу контента
    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses',
                                  model_name=model_name)
        return None
    
    # Создается динамическая форма с общими полями (exclude=list)
    # которые будут исключены из формы  
    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['owner',
                                                 'order',
                                                 'created',
                                                 'updated'])
        return Form(*args, **kwargs)
    
    # получает параметры URL и сохраняет модуль, модель и объект
    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(Module,
                                        id=module_id,
                                        course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model,
                                         id=id,
                                         owner=request.user)
        return super().dispatch(request, module_id, model_name, id)
    

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form,
                                        'object': self.obj})
    

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                Content.objects.create(module=self.module,
                                       item=obj)
            return redirect('module_content_list', self.module.id)
        return self.render_to_response({'form': form,
                                        'object': self.obj})
    


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content,
                                    id=id,
                                    module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)