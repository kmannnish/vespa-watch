from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import ManagementActionForm, ObservationForm, ImageFormset
from .models import Observation, ManagementAction, ObservationPicture


def index(request):
    return render(request, 'vespawatch/index.html')


@login_required
def management(request):
    return render(request, 'vespawatch/management.html')


def create_observation(request):
    if request.method == 'POST':
        form = ObservationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = ObservationForm()

    return render(request, 'vespawatch/observation_create.html', {'form': form})


@login_required
def update_observation(request, pk):
    observation = get_object_or_404(Observation, pk=pk)
    if request.method == 'POST':
        image_formset = ImageFormset(request.POST, request.FILES, instance=observation)
        form = ObservationForm(request.POST, files=request.FILES, instance=observation)
        if form.is_valid():
            form.save()
            if image_formset.is_valid():
                instances = image_formset.save()
                print(instances)
                for obj in image_formset.deleted_objects:
                    print('to delete')
                    print(obj)
                    if obj.pk:
                        obj.delete()
                print('done')
            return HttpResponseRedirect('/')

    elif request.method == 'GET':
        form = ObservationForm(instance=observation)
        image_formset = ImageFormset(instance=observation)
    return render(request, 'vespawatch/observation_update.html',
                  {'form': form, 'object': observation, 'image_formset': image_formset})


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
