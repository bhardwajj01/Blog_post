from django.contrib import admin
from .models import Tag, Blog, Comment


admin.site.register(Tag)
admin.site.register(Blog)
admin.site.register(Comment)