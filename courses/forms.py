from django import forms 
from django.forms.models import inlineformset_factory
from .models import Course, Module


# Создание модельного набора форм динамически для объектов Module,
# связанных с Course 
ModuleFormSet = inlineformset_factory(Course,
                                      Module,
                                      fields=['title',
                                              'description'],
                                      extra=2,
                                      can_delete=True)