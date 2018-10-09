from django.urls import path

from . import views

app_name = 'vespawatch'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/observations', views.observations_json, name='api_observations'),
]