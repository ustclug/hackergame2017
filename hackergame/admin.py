from django.contrib import admin

from .models import Problem, Solved

admin.site.register((Problem, Solved))
