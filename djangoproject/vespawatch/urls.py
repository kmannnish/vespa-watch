from django.urls import path
from . import views

app_name = 'vespawatch'

urlpatterns = [
    path('', views.index, name='index'),
    path('actions/add/', views.create_action, name='action-add'),
    path('actions/<int:pk>/', views.update_action, name='action-update'),
    path('actions/<int:pk>/delete/', views.ManagmentActionDelete.as_view(), name='action-delete'),
    path('observations/add/', views.create_observation, name='observation-add'),
    path('observations/<int:pk>/', views.update_observation, name='observation-update'),
    path('observations/<int:pk>/delete/', views.ObservationDelete.as_view(), name='observation-delete'),
    path('api/observations', views.observations_json, name='api_observations'),

    path('geocoding_test/', views.geocoding_test)
]