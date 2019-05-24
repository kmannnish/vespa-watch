from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from .models import Taxon, Nest, Individual, NestPicture, IndividualPicture, ManagementAction, Profile, \
    FirefightersZone, IdentificationCard, IndividualObservationWarning, NestObservationWarning


class IdentificationCardInline(TranslationTabularInline):
    model = IdentificationCard
    max_num = 2

@admin.register(Taxon)
class TaxonAdmin(admin.ModelAdmin):

    inlines = (IdentificationCardInline, )


class NestPictureInline(admin.TabularInline):
    # We cannot add/edit/delete pictures of non-editable observations
    def has_add_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_add_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_delete_permission(request, obj=obj)

    model = NestPicture


class IndividualPictureInline(admin.TabularInline):
    # We cannot add/edit/delete pictures of non-editable observations
    def has_add_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_add_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_delete_permission(request, obj=obj)

    model = IndividualPicture


class IndividualObservationWarningInline(admin.TabularInline):
    model = IndividualObservationWarning


class NestObservationWarningInline(admin.TabularInline):
    model = NestObservationWarning


class DeleteObjectsOneByOneMixin():
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()


@admin.register(Nest)
class NestAdmin(DeleteObjectsOneByOneMixin, admin.ModelAdmin):
    # Some observations cannot be changed nor deleted
    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_in_admin:
            return False
        return super().has_change_permission(request, obj=obj)

    def get_readonly_fields(self, request, obj=None):
        r = super().get_readonly_fields(request, obj)
        if obj and not obj.taxon_can_be_locally_changed:
            r = r + ('taxon', )
        return r

    list_display = ('taxon', 'inaturalist_id', 'observation_time', 'latitude', 'longitude', 'originates_in_vespawatch', 'has_warnings', 'inat_vv_confirmed')
    readonly_fields = ('originates_in_vespawatch', 'created_at')

    list_filter = ('taxon', 'originates_in_vespawatch')

    inlines = [
        NestPictureInline,
        NestObservationWarningInline
    ]


@admin.register(Individual)
class IndividualAdmin(DeleteObjectsOneByOneMixin, admin.ModelAdmin):
    # Some observations cannot be changed nor deleted
    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_in_admin:
            return False
        return super().has_change_permission(request, obj=obj)

    def get_readonly_fields(self, request, obj=None):
        r = super().get_readonly_fields(request, obj)
        if obj and not obj.taxon_can_be_locally_changed:
            r = r + ('taxon', )
        return r

    list_display = ('taxon', 'inaturalist_id', 'observation_time', 'latitude', 'longitude', 'originates_in_vespawatch', 'has_warnings', 'inat_vv_confirmed')
    readonly_fields = ('originates_in_vespawatch', 'created_at')

    list_filter = ('taxon', 'originates_in_vespawatch')

    inlines = [
        IndividualPictureInline,
        IndividualObservationWarningInline
    ]

@admin.register(ManagementAction)
class ManagementActionAdmin(admin.ModelAdmin):
    pass


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_zone')
    list_select_related = ('profile',)

    def get_zone(self, instance):
        try:
            return instance.profile.zone.name
        except AttributeError:
            return '-'
    get_zone.short_description = 'Zone'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(IdentificationCard)
class IdentificationCardAdmin(TranslationAdmin):
    list_display = ('order', 'represented_taxon', 'represents_nest')

@admin.register(FirefightersZone)
class ZoneAdmin(admin.ModelAdmin):
    pass