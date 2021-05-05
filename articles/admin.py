from django.contrib import admin

from articles.models import Writer, Article

# Register your models here.

admin.site.register(Writer)
admin.site.register(Article)
