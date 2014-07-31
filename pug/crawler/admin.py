from django.contrib import admin
from django.db import models
from django import forms

admin_site = admin.sites.AdminSite()

excluded_models = []
unsearchable_field_types = ['ForeignKey', 'OneToOneField', 'TimeField', 'DateTimeField', 'DateField', 'AutoField']
unsearchable_field_names = ['id', 'pk', 'primary_key']
search_related_id = False
search_related_pk = True

app_names = ['crawler',]  # App with label pug.miner could not be found
link_suffix = '____'

for apps_models in [models.get_models(app) for app in (models.get_app(app_name) for app_name in app_names)]:
    for Model in apps_models:

        model_name = Model._meta.object_name
        if model_name in excluded_models:
            continue

        model_admin_name = model_name + 'Admin'
        if model_admin_name in globals():
            ModelAdmin = globals()[model_admin_name]
        else:
            class ModelAdmin(admin.ModelAdmin):
                pass

        if len(ModelAdmin.list_display) <= 1 or ModelAdmin.list_display[0] == '__str__':
            list_display = []
            for field in Model._meta.fields:
                if field.get_internal_type() == 'ForeignKey':
                    list_display += [field.name + link_suffix]
                elif field.get_internal_type() == 'OneToOneField':
                    list_display += [field.name + link_suffix]
                else:
                    list_display += [field.name]
            # Can do this for any OneToOneFields?
            ModelAdmin.list_display = list_display

        if ModelAdmin.search_fields == ():
            search_fields = [field.name for field in Model._meta.fields if field.get_internal_type() not in unsearchable_field_types and field.name not in unsearchable_field_names]
            
            for field in Model._meta.fields:
                if field.get_internal_type() == 'ForeignKey':
                    if search_related_id and 'id' in field.related.model._meta.get_all_field_names():
                        search_fields.append(field.name + '__id')
                    if search_related_pk and 'pk' in field.related.model._meta.get_all_field_names():
                        search_fields.append(field.name + '__pk')
                    if 'name' in [rel_field.name for rel_field in field.rel.to._meta.fields]:
                        search_fields.append(field.name+'__name')
            ModelAdmin.search_fields = search_fields

        if not ModelAdmin.date_hierarchy:
            for field in Model._meta.fields:
                if field.get_internal_type() in ('DateTimeField', 'DateField'):
                    ModelAdmin.date_hierarchy = field.name
                    break

        form_name = '%sForm' % Model._meta.object_name
        if ModelAdmin.form == forms.ModelForm and form_name in globals():
            ModelAdmin.form = globals()[form_name]

        try:
            admin_site.register(Model, ModelAdmin)
        except:
            pass
