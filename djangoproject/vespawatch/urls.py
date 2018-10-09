from django.urls import path
from . import views

app_name = 'vespawatch'

urlpatterns = [
    path('', views.index, name='index'),
    path('observations/add/', views.create_observation, name='observation-add'),
    path('observations/<int:pk>/', views.update_observation, name='observation-update'),
    path('observations/<int:pk>/delete/', views.ObservationDelete.as_view(), name='observation-delete'),
    path('api/observations', views.observations_json, name='api_observations'),

    path('geocoding_test/', views.geocoding_test)
]