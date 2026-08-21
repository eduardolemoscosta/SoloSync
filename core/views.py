from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from .models import Talhao, Plantio, Manejo, Irrigacao, Ocorrencia
from .forms import TalhaoForm, PlantioForm, ManejoForm, IrrigacaoForm, OcorrenciaForm
from django.contrib.auth import login

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        plantios = Plantio.objects.filter(talhao__usuario=user)
        context['plantios_ativos'] = plantios.filter(status='ATIVO').count()
        context['areas_preparo'] = plantios.filter(status='PREPARO').count()
        context['total_talhoes'] = Talhao.objects.filter(usuario=user).count()
        context['plantios_andamento'] = plantios.exclude(status='FINALIZADO').order_by('-data_plantio')
        return context

# Talhao Views
class TalhaoListView(LoginRequiredMixin, ListView):
    model = Talhao
    template_name = 'core/talhao_list.html'
    context_object_name = 'talhoes'
    def get_queryset(self):
        return Talhao.objects.filter(usuario=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import json
        talhoes_data = []
        for t in context['talhoes']:
            if t.coordenadas:
                talhoes_data.append({
                    'id': t.id,
                    'nome': t.nome,
                    'area': str(t.area_m2),
                    'geojson': t.coordenadas
                })
        context['talhoes_json'] = json.dumps(talhoes_data)
        return context

class TalhaoCreateView(LoginRequiredMixin, CreateView):
    model = Talhao
    form_class = TalhaoForm
    template_name = 'core/talhao_form.html'
    success_url = reverse_lazy('talhao_list')
    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Novo Talhão'
        return context

class TalhaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Talhao
    form_class = TalhaoForm
    template_name = 'core/talhao_form.html'
    success_url = reverse_lazy('talhao_list')
    def get_queryset(self):
        return Talhao.objects.filter(usuario=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Talhão'
        return context

class TalhaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Talhao
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('talhao_list')
    def get_queryset(self):
        return Talhao.objects.filter(usuario=self.request.user)

# Plantio Views
class PlantioListView(LoginRequiredMixin, ListView):
    model = Plantio
    template_name = 'core/plantio_list.html'
    context_object_name = 'plantios'
    def get_queryset(self):
        return Plantio.objects.filter(talhao__usuario=self.request.user)

class PlantioDetailView(LoginRequiredMixin, DetailView):
    model = Plantio
    template_name = 'core/plantio_detail.html'
    context_object_name = 'plantio'
    def get_queryset(self):
        return Plantio.objects.filter(talhao__usuario=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # unificar historico
        manejos = list(self.object.manejos.all())
        irrigacoes = list(self.object.irrigacoes.all())
        ocorrencias = list(self.object.ocorrencias.all())
        historico = []
        for m in manejos: historico.append({'data': m.data, 'tipo': 'Manejo: ' + m.tipo_operacao, 'detalhe': f"{m.produto_insumo} - {m.dosagem_quantidade}"})
        for i in irrigacoes: historico.append({'data': i.data_hora.date(), 'tipo': 'Irrigação', 'detalhe': f"{i.duracao_minutos} min - {i.lamina_ou_volume or ''}"})
        for o in ocorrencias: historico.append({'data': o.data, 'tipo': 'Ocorrência: ' + o.tipo, 'detalhe': o.descricao})
        historico.sort(key=lambda x: x['data'], reverse=True)
        context['historico'] = historico
        return context

class PlantioCreateView(LoginRequiredMixin, CreateView):
    model = Plantio
    form_class = PlantioForm
    template_name = 'core/form_generic.html'
    success_url = reverse_lazy('plantio_list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Novo Plantio'
        return context

class PlantioUpdateView(LoginRequiredMixin, UpdateView):
    model = Plantio
    form_class = PlantioForm
    template_name = 'core/form_generic.html'
    success_url = reverse_lazy('plantio_list')
    def get_queryset(self):
        return Plantio.objects.filter(talhao__usuario=self.request.user)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Plantio'
        return context

class PlantioDeleteView(LoginRequiredMixin, DeleteView):
    model = Plantio
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('plantio_list')
    def get_queryset(self):
        return Plantio.objects.filter(talhao__usuario=self.request.user)

# Manejo, Irrigacao, Ocorrencia Create Views
class ManejoCreateView(LoginRequiredMixin, CreateView):
    model = Manejo
    form_class = ManejoForm
    template_name = 'core/form_generic.html'
    success_url = reverse_lazy('dashboard')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registrar Manejo'
        return context

class IrrigacaoCreateView(LoginRequiredMixin, CreateView):
    model = Irrigacao
    form_class = IrrigacaoForm
    template_name = 'core/form_generic.html'
    success_url = reverse_lazy('dashboard')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registrar Irrigação'
        return context

class OcorrenciaCreateView(LoginRequiredMixin, CreateView):
    model = Ocorrencia
    form_class = OcorrenciaForm
    template_name = 'core/form_generic.html'
    success_url = reverse_lazy('dashboard')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registrar Ocorrência'
        return context
