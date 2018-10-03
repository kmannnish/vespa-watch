from django.contrib import admin

from .models import Species, Observation, ObservationPicture, ManagementAction

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    pass


class PictureInline(admin.TabularInline):
    model = ObservationPicture


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ('species', 'inaturalist_id', 'observation_time', 'latitude', 'longitude')

    list_filter = ('species', )

    inlines = [
        PictureInline,
    ]

@admin.register(ManagementAction)
class ManagementActionAdmin(admin.ModelAdmin):
    pass