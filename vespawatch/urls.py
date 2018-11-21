from django.urls import path
from . import views

app_name = 'vespawatch'

urlpatterns = [
    path('', views.index, name='index'),
    path('management', views.management, name='management'),
    path('actions/add/', views.create_action, name='action-add'),
    path('actions/<int:pk>/', views.update_action, name='action-update'),
    path('actions/<int:pk>/delete/', views.ManagmentActionDelete.as_view(), name='action-delete'),
    path('individuals/add/', views.create_individual, name='individual-add'),
    path('individuals/<int:pk>/', views.IndividualDetail.as_view(), name='individual-detail'),
    path('individuals/<int:pk>/edit/', views.update_individual, name='individual-update'),
    path('individuals/<int:pk>/delete/', views.IndividualDelete.as_view(), name='individual-delete'),
    path('new/', views.new_observation, name='new'),
    path('nests/add/', views.create_nest, name='nest-add'),
    path('nests/<int:pk>/', views.NestDetail.as_view(), name='nest-detail'),
    path('nests/<int:pk>/edit/', views.update_nest, name='nest-update'),
    path('nests/<int:pk>/delete/', views.NestDelete.as_view(), name='nest-delete'),

    # API paths
    path('api/observations', views.observations_json, name='api_observations'),
    path('api/species', views.species_json, name='api_species'),
    path('api/zones', views.zones_json, name='api_zones'),
]