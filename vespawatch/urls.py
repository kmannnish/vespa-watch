from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'vespawatch'

#TODO: Review this file to make sure all those URLs / views are still in use (management actions for example).

urlpatterns = [
    path('', views.index, name='index'),
    path('get-involved/', views.getinvolved, name='getinvolved'),
    path('identification/', views.identification, name='identification'),

    path('about/links/', views.about_links, name='about_links'),
    path('about/management/', views.about_management, name='about_management'),
    path('about/privacy-policy/', views.about_privacypolicy, name='about_privacypolicy'),
    path('about/project/', views.about_project, name='about_project'),
    path('about/vespa-velutina/', views.about_vespavelutina, name='about_vespavelutina'),

    path('management/', views.management, name='management'),
    path('actions/add/', views.create_action, name='action-add'),
    path('actions/<int:pk>/', views.update_action, name='action-update'),
    path('actions/<int:pk>/delete/', views.ManagmentActionDelete.as_view(), name='action-delete'),

    path('obs/', views.latest_observations, name='latest-observations'),
    path('obs/add/', views.obs_create, name='observation-add'),

    path('obs/individual/', RedirectView.as_view(pattern_name='vespawatch:individual-add')),
    path('obs/individual/add/', views.create_individual, name='individual-add'),
    path('obs/individual/<int:pk>/', views.IndividualDetail.as_view(), name='individual-detail'),
    path('obs/individual/<int:pk>/delete/', views.IndividualDelete.as_view(), name='individual-delete'),

    path('obs/nest/', RedirectView.as_view(pattern_name='vespawatch:nest-add')),
    path('obs/nest/add/', views.create_nest, name='nest-add'),
    path('obs/nest/<int:pk>/', views.NestDetail.as_view(), name='nest-detail'),
    path('obs/nest/<int:pk>/delete/', views.NestDelete.as_view(), name='nest-delete'),

    # API paths
    path('api/observations/', views.observations_json, name='api_observations'),
    path('api/individuals/', views.individuals_json, name='api_individuals'),
    path('api/individuals/<int:pk>', views.single_individual_json, name='api_single_individual'),
    path('api/individual_pictures/', views.save_individual_picture, name='api_individual_picture'),
    path('api/individual_pictures/<int:pk>', views.get_individual_picture, name='api_single_individual_picture'),
    path('api/nests/', views.nests_json, name='api_nests'),
    path('api/nests/<int:pk>/', views.single_nest_json, name='api_single_nest'),
    path('api/nest_pictures/', views.save_nest_picture, name='api_nest_picture'),
    path('api/nest_pictures/<int:pk>', views.get_nest_picture, name='api_single_nest_picture'),

    path('api/action_outcomes/', views.management_actions_outcomes_json, name='api_action_outcomes'),
    path('api/save_management_action/', views.save_management_action, name='api_action_save'),
    path('api/get_management_action/', views.get_management_action, name='api_action_get'),
    path('api/delete_management_action/', views.delete_management_action, name='api_action_delete'),
    path('api/get_zone/', views.get_zone, name='api_zone_get'),

    path('send_test_email', views.send_test_email)
]