from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import ManagementActionForm, IndividualForm, NestForm, IndividualImageFormset, NestImageFormset
from .models import Individual, Nest, ManagementAction, IndividualPicture, NestPicture


def index(request):
    return render(request, 'vespawatch/index.html')


@login_required
def management(request):
    return render(request, 'vespawatch/management.html')


def new_observation(request):
    return render(request, 'vespawatch/new_observation.html')




# CREATE UPDATE INDIVIDUAL OBSERVATIONS

def create_individual(request):
    if request.method == 'POST':
        form = IndividualForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = IndividualForm()
    return render(request, 'vespawatch/observation_create.html', {'form': form, 'type': 'individual'})

@login_required
def update_individual(request, pk):
    indiv = get_object_or_404(Individual, pk=pk)
    if request.method == 'POST':
        image_formset = IndividualImageFormset(request.POST, request.FILES, instance=indiv)
        form = IndividualForm(request.POST, files=request.FILES, instance=indiv)
        if form.is_valid():
            form.save()
            if image_formset.is_valid():
                instances = image_formset.save()
                for obj in image_formset.deleted_objects:
                    if obj.pk:
                        obj.delete()
            return HttpResponseRedirect('/')
    elif request.method == 'GET':
        form = IndividualForm(instance=indiv)
        image_formset = IndividualImageFormset(instance=indiv)
    return render(request, 'vespawatch/observation_update.html',
                  {'form': form, 'object': indiv, 'type': 'individual', 'image_formset': image_formset})


class IndividualDetail(DetailView):
    model = Individual


class IndividualDelete(LoginRequiredMixin, DeleteView):
    model = Individual
    success_url = reverse_lazy('vespawatch:index')



# CREATE UPDATE NEST OBSERVATIONS

def create_nest(request):
    if request.method == 'POST':
        form = NestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = NestForm()
    return render(request, 'vespawatch/observation_create.html', {'form': form, 'type': 'nest'})


@login_required
def update_nest(request, pk):
    nest = get_object_or_404(Nest, pk=pk)
    if request.method == 'POST':
        image_formset = NestImageFormset(request.POST, request.FILES, instance=nest)
        form = NestForm(request.POST, files=request.FILES, instance=nest)
        if form.is_valid():
            form.save()
            if image_formset.is_valid():
                instances = image_formset.save()
                for obj in image_formset.deleted_objects:
                    if obj.pk:
                        obj.delete()
            return HttpResponseRedirect('/')
    elif request.method == 'GET':
        form = NestForm(instance=nest)
        image_formset = NestImageFormset(instance=nest)
    return render(request, 'vespawatch/observation_update.html',
                  {'form': form, 'object': nest, 'type': 'nest', 'image_formset': image_formset})


class NestDetail(DetailView):
    model = Nest


class NestDelete(LoginRequiredMixin, DeleteView):
    model = Nest
    success_url = reverse_lazy('vespawatch:index')


# CREATE/UPDATE/DELETE MANAGEMENT ACTIONS

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
    individuals = list(Individual.objects.all())
    nests = list(Nest.objects.all())

    return JsonResponse({
        'observations': [x.as_dict() for x in individuals + nests]
    })
