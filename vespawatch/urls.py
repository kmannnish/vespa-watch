from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'vespawatch'

urlpatterns = [
    path('', views.index, name='index'),
    path('management', views.management, name='management'),
    path('actions/add/', views.create_action, name='action-add'),
    path('actions/<int:pk>/', views.update_action, name='action-update'),
    path('actions/<int:pk>/delete/', views.ManagmentActionDelete.as_view(), name='action-delete'),

    path('obs/', views.latest_observations, name='latest-observations'),
    path('obs/add', views.create_obs_step_1, name='observation-add'),

    path('obs/individual/', RedirectView.as_view(pattern_name='vespawatch:individual-add')),
    path('obs/individual/add/', views.create_individual, name='individual-add'),
    path('obs/individual/<int:pk>/', views.IndividualDetail.as_view(), name='individual-detail'),
    path('obs/individual/<int:pk>/edit/', views.update_individual, name='individual-update'),
    path('obs/individual/<int:pk>/delete/', views.IndividualDelete.as_view(), name='individual-delete'),

    path('obs/nest/', RedirectView.as_view(pattern_name='vespawatch:nest-add')),
    path('obs/nest/add/', views.create_nest, name='nest-add'),
    path('obs/nest/<int:pk>/', views.NestDetail.as_view(), name='nest-detail'),
    path('obs/nest/<int:pk>/edit/', views.update_nest, name='nest-update'),
    path('obs/nest/<int:pk>/delete/', views.NestDelete.as_view(), name='nest-delete'),

    # API paths
    path('api/observations', views.observations_json, name='api_observations'),
    path('api/taxa', views.taxa_json, name='api_taxa'),
    # path('api/zones', views.zones_json, name='api_zones'),
    path('api/action_outcomes', views.management_actions_outcomes_json, name='api_action_outcomes'),
    path('api/save_management_action', views.save_management_action, name='api_action_save'),
    path('api/get_management_action', views.get_management_action, name='api_action_get'),
    path('api/delete_management_action', views.delete_management_action, name='api_action_delete'),
    path('api/get_zone', views.get_zone, name='api_zone_get')
]