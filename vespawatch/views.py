import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers import serialize
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView
from django.views.generic.base import View
from django.views.generic.detail import BaseDetailView, SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic.edit import DeletionMixin
from django.urls import reverse_lazy

from vespawatch.utils import ajax_login_required
from .forms import ManagementActionForm, IndividualForm, NestForm, IndividualImageFormset, NestImageFormset
from .models import Individual, Nest, ManagementAction, Taxon, FirefightersZone, IdentificationCard, \
    get_observations


class CustomBaseDetailView(SingleObjectMixin, View):
    """Subclassing this one to pass the request parameters to the kwargs of get_context_data"""
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object, **request.GET)
        return self.render_to_response(context)


class CustomBaseDeleteView(DeletionMixin, BaseDetailView):
    """Overriding the BaseDeleteView to add the redirect_to param from the request to the View object"""
    def delete(self, request, *args, **kwargs):
        r = request.GET.get('redirect_to', '')
        if r:
            self.requested_success_url = r
        return super(CustomBaseDeleteView, self).delete(request, *args, **kwargs)


class CustomDeleteView(SingleObjectTemplateResponseMixin, CustomBaseDeleteView):
    """Also had to override this one for adding the redirect_to param to the View object"""
    template_name_suffix = '_confirm_delete'


def index(request):
    return render(request, 'vespawatch/index.html', {'observations': get_observations(limit=4)})

def latest_observations(request):
    return render(request, 'vespawatch/obs.html', {'observations': get_observations(limit=40)})

@login_required
def management(request):
    profile = request.user.profile
    zone = profile.zone
    if not (zone or request.user.is_staff):
        raise Http404()
    print(zone)
    if zone:
        nests = Nest.objects.filter(zone=zone).order_by('-observation_time')
    else:
        nests = Nest.objects.all().order_by('-observation_time')
    context = {'nests': json.dumps([x.as_dict() for x in nests]), 'zone': zone}
    print(context)

    return render(request, 'vespawatch/management.html', context)


# CREATE UPDATE INDIVIDUAL OBSERVATIONS

def create_individual(request):
    if request.method == 'POST':
        redirect_to = request.POST.get('redirect_to')
        form = IndividualForm(request.POST, request.FILES)
        image_formset = IndividualImageFormset()
        if request.user.is_authenticated:
            # set to terms_of_service to true if the user is authenticated
            form_data_copy = form.data.copy()
            form_data_copy['terms_of_service'] = True
            form.data = form_data_copy
        if form.is_valid():
            form.save()
            image_formset = IndividualImageFormset(request.POST, request.FILES, instance=form.instance)
            if image_formset.is_valid():
                instances = image_formset.save()
            messages.success(request, _("Your observation was successfully created."))
            return HttpResponseRedirect(reverse_lazy(f'vespawatch:{redirect_to}'))
    else:
        redirect_to = request.GET.get('redirect_to', 'index')
        form = IndividualForm(initial={'redirect_to': redirect_to})
        image_formset = IndividualImageFormset()
    return render(request, 'vespawatch/individual_create.html', {'form': form, 'type': 'individual', 'image_formset': image_formset})


@login_required
def update_individual(request, pk):
    indiv = get_object_or_404(Individual, pk=pk)
    if request.method == 'POST':
        image_formset = IndividualImageFormset(request.POST, request.FILES, instance=indiv)
        form = IndividualForm(request.POST, files=request.FILES, instance=indiv)
        if request.user.is_authenticated:
            # set to terms_of_service to true if the user is authenticated
            form_data_copy = form.data.copy()
            form_data_copy['terms_of_service'] = True
            form.data = form_data_copy
        if form.is_valid():
            form.save()
            if image_formset.is_valid():
                instances = image_formset.save()
                for obj in image_formset.deleted_objects:
                    if obj.pk:
                        obj.delete()
            return HttpResponseRedirect(reverse_lazy('vespawatch:individual-detail', kwargs={'pk': pk}))
    elif request.method == 'GET':
        form = IndividualForm(instance=indiv)
        image_formset = IndividualImageFormset(instance=indiv)
    return render(request, 'vespawatch/individual_update.html',
                  {'form': form, 'object': indiv, 'type': 'individual', 'image_formset': image_formset})


class IndividualDetail(SingleObjectTemplateResponseMixin, CustomBaseDetailView):
    model = Individual

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        r = kwargs.get('redirect_to', ['index'])
        context['redirect_to'] = r[0]
        return context


class IndividualDelete(LoginRequiredMixin, CustomDeleteView):
    model = Individual
    success_url = reverse_lazy('vespawatch:index')
    success_message = "The observation was successfully deleted."
    requested_success_url = None

    def get_success_url(self, **kwargs):
        if self.requested_success_url:
            return reverse_lazy(f'vespawatch:{self.requested_success_url}').format(**self.object.__dict__)

        return super(IndividualDelete, self).get_success_url()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _(self.success_message))
        return super(IndividualDelete, self).delete(request, *args, **kwargs)


# CREATE UPDATE NEST OBSERVATIONS

def create_nest(request):
    if request.method == 'POST':
        redirect_to = request.POST.get('redirect_to')

        new_nest_from_anonymous = not request.user.is_authenticated
        form = NestForm(request.POST, request.FILES, new_nest_from_anonymous=new_nest_from_anonymous)
        image_formset = NestImageFormset()
        if request.user.is_authenticated:
            # set to terms_of_service to true if the user is authenticated
            form_data_copy = form.data.copy()
            form_data_copy['terms_of_service'] = True
            form.data = form_data_copy
        if form.is_valid():
            form.save()
            image_formset = NestImageFormset(request.POST, request.FILES, instance=form.instance)
            if image_formset.is_valid():
                instances = image_formset.save()

            messages.success(request, _("Your observation was successfully created."))
            return HttpResponseRedirect(reverse_lazy(f'vespawatch:{redirect_to}'))
    else:
        redirect_to = request.GET.get('redirect_to', 'index')
        form = NestForm(initial={'redirect_to': redirect_to})
        image_formset = NestImageFormset()
    return render(request, 'vespawatch/nest_create.html', {'form': form, 'image_formset': image_formset, 'type': 'nest'})


@login_required
def update_nest(request, pk):
    nest = get_object_or_404(Nest, pk=pk)
    if request.method == 'POST':
        image_formset = NestImageFormset(request.POST, request.FILES, instance=nest)
        form = NestForm(request.POST, files=request.FILES, instance=nest)
        if request.user.is_authenticated:
            # set to terms_of_service to true if the user is authenticated
            form_data_copy = form.data.copy()
            form_data_copy['terms_of_service'] = True
            form.data = form_data_copy
        if form.is_valid():
            form.save()
            if image_formset.is_valid():
                instances = image_formset.save()
                for obj in image_formset.deleted_objects:
                    if obj.pk:
                        obj.delete()
            return HttpResponseRedirect(reverse_lazy('vespawatch:nest-detail', kwargs={'pk': pk}))
    elif request.method == 'GET':
        form = NestForm(instance=nest)
        image_formset = NestImageFormset(instance=nest)

    return render(request, 'vespawatch/nest_update.html',
                  {'form': form, 'object': nest, 'type': 'nest', 'image_formset': image_formset})


class NestDetail(SingleObjectTemplateResponseMixin, CustomBaseDetailView):
    model = Nest

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        r = kwargs.get('redirect_to', ['index'])
        context['redirect_to'] = r[0]
        return context


class NestDelete(LoginRequiredMixin, CustomDeleteView):
    model = Nest
    success_url = reverse_lazy('vespawatch:index')
    success_message = "The observation was successfully deleted."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _(self.success_message))
        return super(NestDelete, self).delete(request, *args, **kwargs)


# CREATE/UPDATE/DELETE MANAGEMENT ACTIONS
# TODO: Check if those 3 actions are still used.
@login_required
def create_action(request):
    if request.method == 'POST':
        form = ManagementActionForm(request.POST)
        if form.is_valid():
            action = ManagementAction(**form.cleaned_data)
            action.save()
        return HttpResponseRedirect('/')

    else:
        form = ManagementActionForm()
    return render(request, 'vespawatch/action_create.html', {'form': form})


@login_required
def update_action(request, pk=None):
    action = get_object_or_404(ManagementAction, pk=pk)
    if request.method == 'POST':
        form = ManagementActionForm(request.POST, instance=action)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = ManagementActionForm(instance=action)

    return render(request, 'vespawatch/action_update.html', {'form': form, 'object': action})


class ManagmentActionDelete(LoginRequiredMixin, DeleteView):
    model = ManagementAction
    success_url = reverse_lazy('vespawatch:index')


def create_obs_step_1(request):
    # This is the step where the user select the species and type (nest/individual)
    cards = IdentificationCard.objects.all()

    return render(request, 'vespawatch/create_obs_step_1.html', {'identification_cards': cards})

# ==============
# API methods
# ==============

def taxa_json(request):
    """
    Return all taxa as JSON data.
    """
    return JsonResponse([s.to_json() for s in Taxon.objects.all()], safe=False)

def observations_json(request):
    # TODO: refactor to use models.get_recent_observations() (except if this is not needed anymore -> delete)
    """
    Return all observations as JSON data.
    """
    zone = request.GET.get('zone', '')
    obs_type = request.GET.get('type', '')
    limit = request.GET.get('limit', None)

    obs = []

    if obs_type == 'individual' or obs_type == '':
        obs = obs + list(Individual.objects.all())
    if obs_type == 'nest' or obs_type == '':
        obs = obs + list(Nest.objects.all())

    if zone:
        # if a zone is given, filter the observations. This works for both individuals and nests
        obs = [x for x in obs if x.zone_id == int(zone)]

    obs.sort(key=lambda x: x.observation_time, reverse=True)
    if limit:
        obs = obs[:int(limit)]

    return JsonResponse({
        'observations': [x.as_dict() for x in obs]
    })
#
# @staff_member_required
# def zones_json(request):
#     """
#     Return all firefighter zones as json data
#     """
#     return JsonResponse({'zones': [{'id': x.pk, 'name': x.name} for x in list(FirefightersZone.objects.all().order_by('name'))]})

def management_actions_outcomes_json(request):
    #TODO: Implements sorting?
    #TODO: Implements i18n?
    outcomes = ManagementAction.OUTCOME_CHOICE
    return JsonResponse([{'value': outcome[0], 'label': outcome[1]} for outcome in outcomes], safe=False)


@ajax_login_required
@csrf_exempt
def delete_management_action(request):
    if request.method == 'DELETE':
        ManagementAction.objects.get(pk=request.GET.get('action_id')).delete()
        return JsonResponse({'result': 'OK'})

@ajax_login_required
@csrf_exempt
def save_management_action(request):
    if request.method == 'POST':
        existing_action_id = request.POST.get('action_id', None)

        if existing_action_id:  # We want to update an existing action
            form = ManagementActionForm(request.POST, instance=get_object_or_404(ManagementAction, pk=existing_action_id))
        else:  # We want to create a new action
            form = ManagementActionForm(request.POST)

        try:
            form.save()
            return JsonResponse({'result': 'OK'}, status=201)
        except ValueError:
            return JsonResponse({'result': 'NOTOK', 'errors': form.errors}, status=422)

def get_management_action(request):
    if request.method == 'GET':
        action_id = request.GET.get('action_id')
        action = get_object_or_404(ManagementAction, pk=action_id)

        return JsonResponse({'action_time': action.action_time,
                             'outcome':action.outcome,
                             'duration': action.duration_in_seconds,
                             'person_name': action.person_name})

def get_zone(request):
    if request.method == 'GET':
        zone_id = request.GET.get('zone_id')
        zone = get_object_or_404(FirefightersZone, pk=zone_id)

        return HttpResponse(serialize('geojson', [zone],
                  geometry_field='mpolygon',
                  fields=('pk', 'name')))
