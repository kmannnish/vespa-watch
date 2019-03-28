import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers import serialize
from django.forms.models import model_to_dict
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
    get_observations, get_individuals, get_nests


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

def getinvolved(request):
    return render(request, 'vespawatch/simple_page_fragment.html', {'fragment_id': 'getinvolved'})

def identification(request):
    return render(request, 'vespawatch/simple_page_fragment.html', {'fragment_id': 'identification'})

def about_links(request):
    return render(request, 'vespawatch/simple_page_fragment.html', {'fragment_id': 'about_links'})

def about_management(request):
    return render(request, 'vespawatch/simple_page_fragment.html', {'fragment_id': 'about_management'})

def about_privacypolicy(request):
    return render(request, 'vespawatch/simple_page_fragment.html', {'fragment_id': 'about_privacypolicy'})

def about_project(request):
    return render(request, 'vespawatch/simple_page_fragment.html', {'fragment_id': 'about_project'})

def about_vespavelutina(request):
    return render(request, 'vespawatch/simple_page_fragment.html', {'fragment_id': 'about_vespavelutina'})

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
        card_id = request.POST.get('card_id')
        print(f'2: {card_id}')
        identif_card = IdentificationCard.objects.get(pk=card_id)
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
            messages.success(request, _("Your observation was successfully created. Thanks for your contribution!"))
            return HttpResponseRedirect(reverse_lazy(f'vespawatch:{redirect_to}'))
    else:
        redirect_to = request.GET.get('redirect_to', 'index')
        identif_card_id = request.GET.get('card_id')
        identif_card = IdentificationCard.objects.get(pk=identif_card_id)
        taxon = identif_card.represented_taxon
        print(f'1: {identif_card_id}')
        form = IndividualForm(initial={
            'redirect_to': redirect_to,
            'card_id': identif_card_id,
            'taxon': taxon})
        image_formset = IndividualImageFormset()
    return render(request, 'vespawatch/individual_create.html',
                  {'form': form, 'type': 'individual', 'image_formset': image_formset, 'identif_card': identif_card})


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
        card_id = request.POST.get('card_id')
        identif_card = IdentificationCard.objects.get(pk=card_id)

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

            messages.success(request, _("Your observation was successfully created. Thanks for your contribution!"))
            return HttpResponseRedirect(reverse_lazy(f'vespawatch:{redirect_to}'))
    else:
        redirect_to = request.GET.get('redirect_to', 'index')
        identif_card_id = request.GET.get('card_id')
        identif_card = IdentificationCard.objects.get(pk=identif_card_id)
        taxon = identif_card.represented_taxon
        form = NestForm(initial={
            'redirect_to': redirect_to,
            'card_id': identif_card_id,
            'taxon': taxon
        })
        image_formset = NestImageFormset()
    return render(request, 'vespawatch/nest_create.html',
                  {'form': form, 'image_formset': image_formset, 'type': 'nest', 'identif_card': identif_card})


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


def obs_create(request):
    # This is the step where the user select the species and type (nest/individual)
    cards = IdentificationCard.objects.all()

    return render(request, 'vespawatch/obs_create.html', {'identification_cards': cards})

# ==============
# API methods
# ==============

def observations_json(request):
    """
    Return all observations as JSON data.
    """
    # TODO: can we deprecate this function? + If so, can we remove the prefetch_related('pictures') from the get_observations function?
    zone = request.GET.get('zone', '')
    zone_id = int(zone) if zone else None

    obs_type = request.GET.get('type', None)
    include_individuals = (obs_type == 'individual' or obs_type is None)
    include_nests = (obs_type == 'nest' or obs_type is None)

    limit = request.GET.get('limit', None)
    limit = int(limit) if limit is not None else None

    obs = get_observations(include_individuals=include_individuals,
                           include_nests=include_nests,
                           zone_id=zone_id,
                           limit=limit)

    light = request.GET.get('light', None)

    if light:
        response = JsonResponse({
            'observations': [model_to_dict(x) for x in obs]
        })
    else:
        response = JsonResponse({
            'observations': [x.as_dict() for x in obs]
        })

    return response

def individuals_json(request):
    """
    Return all individuals as JSON data.
    """
    limit = request.GET.get('limit', None)
    limit = int(limit) if limit is not None else None

    obs = get_individuals(limit=limit)

    light = request.GET.get('light', None)

    if light:
        response = JsonResponse({
            'individuals': [model_to_dict(x) for x in obs]
        })
    else:
        response = JsonResponse({
            'individuals': [x.as_dict() for x in obs]
        })

    return response


def single_individual_json(request, pk=None):
    """
    Get a single individual and return it as JSON
    """
    return JsonResponse(get_object_or_404(Individual, pk=pk).as_dict())


def single_nest_json(request, pk=None):
    """
    Get a single nest and return it as JSON
    """
    return JsonResponse(get_object_or_404(Nest, pk=pk).as_dict())


def nests_json(request):
    """
    Return all nests as JSON data.
    """
    limit = request.GET.get('limit', None)
    limit = int(limit) if limit is not None else None

    obs = get_nests(limit=limit)

    light = request.GET.get('light', None)

    if light:
        response = JsonResponse({
            'nests': [model_to_dict(x) for x in obs]
        })
    else:
        response = JsonResponse({
            'nests': [x.as_dict() for x in obs]
        })

    return response


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
