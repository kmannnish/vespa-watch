from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from .forms import ObservationForm, PublicObservationForm
from .models import Observation


def index(request):
    return render(request, 'vespawatch/index.html')


def create_observation(request):
    if request.method == 'POST':
        form = PublicObservationForm(request.POST)
        if form.is_valid():
            observation = Observation(**form.cleaned_data)
            print(observation)
            observation.save()
            return HttpResponseRedirect('/')
    else:
        if request.user.is_authenticated:
            form = ObservationForm()
        else:
            form = PublicObservationForm()

    return render(request, 'vespawatch/observation_create.html', {'form': form})


def update_observation(request, pk):
    observation = get_object_or_404(Observation, pk=pk)
    if request.method == 'POST':
        form = PublicObservationForm(request.POST, instance=observation)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')

    elif request.method == 'GET':
        if request.user.is_authenticated:
            form = ObservationForm(instance=observation)
        else:
            form = PublicObservationForm(instance=observation)
    return render(request, 'vespawatch/observation_update.html', {'form': form, 'object': observation})


class ObservationDelete(DeleteView):
    model = Observation
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


def geocoding_test(request):
    return render(request, 'vespawatch/geocoding_test.html')