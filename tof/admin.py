# -*- coding: utf-8 -*-
# @Author: MaxST
# @Date:   2019-10-28 12:30:45
# @Last Modified by:   MaxST
# @Last Modified time: 2019-11-18 18:21:06
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .forms import TranslatableFieldsForm, TranslationsForm
from .models import Language, TranslatableField, Translation


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    search_fields = ('app_label', 'model')


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    search_fields = ('iso', )
    list_display = ('iso', 'is_active')
    list_editable = ('is_active', )

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset.filter(is_active=True), use_distinct


@admin.register(TranslatableField)
class TranslatableFieldsAdmin(admin.ModelAdmin):
    form = TranslatableFieldsForm
    search_fields = ('name', 'title')
    list_display = ('content_type', 'name', 'title')

    fieldsets = ((None, {
        'fields': (
            'content_type',
            'name',
            'title',
        ),
    }), )

    autocomplete_fields = ('content_type', )
    url_name = '%s:%s_%s_autocomplete'

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

    def _changeform_view(self, request, object_id, form_url, extra_context):
        id_ct = request.GET.get('id_ct')
        if id_ct:
            try:
                ct = ContentType.objects.get_for_id(id_ct)
                model = ct.model_class()
                return JsonResponse({
                    'pk': ct.pk,
                    'fields': [f.attname for f in model._meta.get_fields()],
                })
            except Exception:
                return JsonResponse({'errors': _('You choose wrong content type')})
        return super()._changeform_view(request, object_id, form_url, extra_context)


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    form = TranslationsForm
    list_display = ('content_object', 'lang', 'field', 'value')
    list_filter = ('content_type', )
    fieldsets = ((None, {
        'fields': (
            ('field', 'lang'),
            'object_id',
            'value',
        ),
    }), (
        'hidden',
        {
            'classes': ('hidden', ),
            'fields': ('content_type', ),
        },
    ))
    autocomplete_fields = ('field', 'lang')
    url_name = '%s:%s_%s_autocomplete'

    def _changeform_view(self, request, object_id, form_url, extra_context):
        fld_id = request.GET.get('field_id')
        if fld_id:
            try:
                ct = TranslatableField.objects.get(id=fld_id).content_type
                id_obj = request.GET.get('id_obj')
                model = ct.model_class()
                url = reverse(self.url_name % (self.admin_site.name, model._meta.app_label, model._meta.model_name))
                return JsonResponse({
                    'pk': ct.pk,
                    'url': url,
                    'text': str(model.objects.get(pk=id_obj)) if id_obj else '',
                })
            except Exception:
                return JsonResponse({'errors': _('You choose wrong content type')})
        return super()._changeform_view(request, object_id, form_url, extra_context)
