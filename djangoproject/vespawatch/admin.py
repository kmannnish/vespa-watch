from django.contrib import admin

from .models import Species, Observation, ObservationPicture, ManagementAction

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    pass


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

    list_display = ('species', 'inaturalist_id', 'observation_time', 'latitude', 'longitude')
    readonly_fields = ('originates_in_vespawatch',)

    list_filter = ('species', )

    inlines = [
        PictureInline,
    ]

@admin.register(ManagementAction)
class ManagementActionAdmin(admin.ModelAdmin):
    pass