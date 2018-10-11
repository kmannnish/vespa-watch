from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import ManagementActionForm, ObservationForm, PublicObservationForm
from .models import Observation, ManagementAction


def index(request):
    return render(request, 'vespawatch/index.html')


def create_observation(request):
    if request.method == 'POST':
        form = PublicObservationForm(request.POST)
        if form.is_valid():
            observation = Observation(
                species=form.cleaned_data['species'],
                individual_count=form.cleaned_data['individual_count'],
                behaviour=form.cleaned_data['behaviour'],
                subject=form.cleaned_data['subject'],
                observation_time=form.cleaned_data['observation_time'],
                location=form.cleaned_data['location'],
                latitude=form.cleaned_data['latitude'],
                longitude=form.cleaned_data['longitude'],
                comments=form.cleaned_data['comments'],
                observer_title=form.cleaned_data['observer_title'],
                observer_last_name=form.cleaned_data['observer_last_name'],
                observer_first_name=form.cleaned_data['observer_first_name'],
                observer_email=form.cleaned_data['observer_email'],
                observer_phone=form.cleaned_data['observer_phone'],
                observer_is_beekeeper=form.cleaned_data['observer_is_beekeeper'],
                observer_approve_data_process=form.cleaned_data['observer_approve_data_process'],
                observer_approve_display=form.cleaned_data['observer_approve_display'],
                observer_approve_data_distribution=form.cleaned_data['observer_approve_data_distribution']
            )
            print(observation)
            observation.save()
            if form.cleaned_data['file_field']:
                raise NotImplemented('I still have to figure out how to save images now')
            return HttpResponseRedirect('/')
    else:
        if request.user.is_authenticated:
            form = ObservationForm()
        else:
            form = PublicObservationForm()

    return render(request, 'vespawatch/observation_create.html', {'form': form})


@login_required
def update_observation(request, pk):
    observation = get_object_or_404(Observation, pk=pk)
    if request.method == 'POST':
        form = PublicObservationForm(request.POST, instance=observation)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')

    elif request.method == 'GET':
        form = PublicObservationForm(instance=observation)
    return render(request, 'vespawatch/observation_update.html', {'form': form, 'object': observation})


class ObservationDetail(DetailView):
    model = Observation


class ObservationDelete(LoginRequiredMixin, DeleteView):
    model = Observation
    success_url = reverse_lazy('vespawatch:index')


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


# ==============
# API methods
# ==============

def observations_json(request):
    """
    Return all observations as json data
    """
    observations = Observation.objects.all()
    return JsonResponse({
        'observations': [x.as_dict() for x in observations]
    })
