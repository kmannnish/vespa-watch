from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import ManagementActionForm, ManagementFormset, IndividualForm, NestForm, IndividualImageFormset, NestImageFormset
from .models import Individual, FirefightersZone, Nest, ManagementAction, Species


def index(request):
    return render(request, 'vespawatch/index.html')


@login_required
def management(request):
    profile = request.user.profile
    zone = profile.zone
    if not (zone or request.user.is_staff):
        raise Http404()
    nests = Nest.objects.filter(zone=zone).order_by('-observation_time')
    context = {'nests': nests, 'zone': zone}
    if request.user.is_staff:
        context['zones'] = FirefightersZone.objects.all().order_by('name')

    return render(request, 'vespawatch/management.html', context)


# @staff_member_required
# def management(request):
#     zone = request.GET.get('zone', '')
#     nests = Nest.objects.filter(zone=zone).order_by('-observation_time')
#     return render(request, 'vespawatch/management.html', {'nests': nests, 'zone': zone})
#

def new_observation(request):
    return render(request, 'vespawatch/new_observation.html')




# CREATE UPDATE INDIVIDUAL OBSERVATIONS

def create_individual(request):
    if request.method == 'POST':
        form = IndividualForm(request.POST, request.FILES)
        if request.user.is_authenticated:
            # set to terms_of_service to true if the user is authenticated
            form_data_copy = form.data.copy()
            form_data_copy['terms_of_service'] = True
            form.data = form_data_copy
        if form.is_valid():
            form.save()
            messages.success(request, _("You're observation was successfully created."))
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
    return render(request, 'vespawatch/observation_update.html',
                  {'form': form, 'object': indiv, 'type': 'individual', 'image_formset': image_formset})


class IndividualDetail(DetailView):
    model = Individual


class IndividualDelete(LoginRequiredMixin, DeleteView):
    model = Individual
    success_url = reverse_lazy('vespawatch:index')
    success_message = "The observation was successfully deleted."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _(self.success_message))
        return super(IndividualDelete, self).delete(request, *args, **kwargs)


# CREATE UPDATE NEST OBSERVATIONS

def create_nest(request):
    if request.method == 'POST':
        form = NestForm(request.POST, request.FILES)
        if request.user.is_authenticated:
            # set to terms_of_service to true if the user is authenticated
            form_data_copy = form.data.copy()
            form_data_copy['terms_of_service'] = True
            form.data = form_data_copy
        if form.is_valid():
            form.save()
            if request.user.is_authenticated:
                management_formset = ManagementFormset(request.POST, request.FILES, instance=form.instance)
                if management_formset.is_valid():
                    management_formset.save()
            messages.success(request, _("You're observation was successfully created."))
            return HttpResponseRedirect('/')
        else:
            management_formset = ManagementFormset()
    else:
        form = NestForm()
        management_formset = ManagementFormset()
    return render(request, 'vespawatch/observation_create.html', {'form': form, 'management_formset': management_formset, 'type': 'nest'})


@login_required
def update_nest(request, pk):
    nest = get_object_or_404(Nest, pk=pk)
    if request.method == 'POST':
        image_formset = NestImageFormset(request.POST, request.FILES, instance=nest)
        management_formset = ManagementFormset(request.POST, request.FILES, instance=nest)
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
            if request.user.is_authenticated:
                if management_formset.is_valid():
                    instances = management_formset.save()
                    for obj in management_formset.deleted_objects:
                        if obj.pk:
                            obj.delete()
            return HttpResponseRedirect(reverse_lazy('vespawatch:nest-detail', kwargs={'pk': pk}))
        else:
            management_formset = ManagementFormset(instance=nest)
    elif request.method == 'GET':
        form = NestForm(instance=nest)
        image_formset = NestImageFormset(instance=nest)
        management_formset = ManagementFormset(instance=nest)
    return render(request, 'vespawatch/observation_update.html',
                  {'form': form, 'object': nest, 'type': 'nest', 'image_formset': image_formset, 'management_formset': management_formset,})


class NestDetail(DetailView):
    model = Nest


class NestDelete(LoginRequiredMixin, DeleteView):
    model = Nest
    success_url = reverse_lazy('vespawatch:index')
    success_message = "The observation was successfully deleted."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _(self.success_message))
        return super(NestDelete, self).delete(request, *args, **kwargs)


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

def species_json(request):
    """
    Return all species as JSON data.
    """
    return JsonResponse([s.to_json() for s in Species.objects.all()], safe=False)

def observations_json(request):
    """
    Return all observations as JSON data.
    """
    zone = request.GET.get('zone', '')
    obs_type = request.GET.get('type', '')

    output = {}

    if obs_type != 'nest':
        # only add individuals to the output if the type is not 'nest'
        output['individuals'] = Individual.objects.all()

    if obs_type != 'individual':
        # only add nests to the output if the type is not 'individual'
        output['nests'] = Nest.objects.all()

    if zone:
        # if a zone is given, filter the observations. This works for both individuals and nests
        for obs_type, qs in output.items():
            output[obs_type] = qs.filter(zone__pk=zone)

    return JsonResponse({
        obs_type: [x.as_dict() for x in list(qs.order_by('observation_time'))] for obs_type, qs in output.items()
    })

@staff_member_required
def zones_json(request):
    """
    Return all firefighter zones as json data
    """
    return JsonResponse({'zones': [{'id': x.pk, 'name': x.name} for x in list(FirefightersZone.objects.all().order_by('name'))]})