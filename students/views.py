from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CourseEnrollForm
from django.views.generic.list import ListView
from courses.models import Course
from django.views.generic.detail import DetailView



# Представление для регистрации студентов
class StudentRegistrationView(CreateView):
    template_name = 'students/student/registration.html'

    # Форма для создания объектов (должна быть ModelForm)
    form_class = UserCreationForm

    success_url = reverse_lazy('student_course_list')

    # При отправке валидной формы - допускает пользователя
    def form_valid(self, form):
        result = super().form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd['username'],
                            password=cd['password1'])
        login(self.request, user)
        return result


# Представление обслуживающее зачисляемых на курс студентов 
# (доступ получают только авторизованные пользователи)
class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('student_course_detail',
                            args=[self.course.id])
    

# Представление для просмотра курсов, на которые зачислены студенты
class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])
    

# Ограничивет базовый набор запросов курсами, на которые зачислен студент
class StudentCourseDetailView(DetailView):
    model = Course
    template_name = 'students/course/detail.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получить объект Course
        course = self.get_object()
        if 'module_id' in self.kwargs:
            # Взять текущий модуль 
            context['module'] = course.modules.get(
                id=self.kwargs['module_id'])
        else:
            # Взять первый модуль
            context['module'] = course.modules.all()[0]
        return context