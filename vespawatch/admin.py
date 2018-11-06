from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Species, Observation, ObservationPicture, ManagementAction, Profile, FirefightersZone


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    readonly_fields = ('inaturalist_pull_taxon_ids', 'inaturalist_push_taxon_id')


class PictureInline(admin.TabularInline):
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

    model = ObservationPicture


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    # Some observations cannot be changed nor deleted
    def has_change_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not obj.can_be_edited_or_deleted:
            return False
        return super().has_delete_permission(request, obj=obj)

    list_display = ('species', 'subject', 'inaturalist_id', 'observation_time', 'latitude', 'longitude')
    readonly_fields = ('originates_in_vespawatch',)

    list_filter = ('species', 'subject', 'originates_in_vespawatch')

    inlines = [
        PictureInline,
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

@admin.register(FirefightersZone)
class ZoneAdmin(admin.ModelAdmin):
    pass