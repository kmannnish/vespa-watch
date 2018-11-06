from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from page_fragments.models import PageFragment


@admin.register(PageFragment)
class PageFragmentAdmin(MarkdownxModelAdmin):
    list_display = ('identifier', 'content_nl', 'content_en')

