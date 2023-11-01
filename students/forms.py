from django import forms
from courses.models import Course


# Форма для зачисления студентов на курсы
class CourseEnrollForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.HiddenInput)
    
