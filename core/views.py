from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import json
from .models import Talhao, Plantio, Manejo, Irrigacao, Ocorrencia, PerfilUsuario
from .forms import TalhaoForm, PlantioForm, ManejoForm, IrrigacaoForm, OcorrenciaForm, PerfilUsuarioForm
from django.contrib.auth import login


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            PerfilUsuario.objects.get_or_create(usuario=user)
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Configure a localização da sua propriedade.')
            return redirect('configurar_propriedade')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def configurar_propriedade(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=perfil)
        if form.is_valid():
            perfil = form.save(commit=False)
            perfil.propriedade_configurada = True
            perfil.save()
            messages.success(request, 'Localização da propriedade configurada com sucesso!')
            return redirect('dashboard')
    else:
        form = PerfilUsuarioForm(instance=perfil)

    return render(request, 'core/configurar_propriedade.html', {
        'form': form,
        'perfil': perfil,
        'is_onboarding': not perfil.propriedade_configurada
    })


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
        import json
        existentes = Talhao.objects.filter(usuario=self.request.user).exclude(coordenadas__isnull=True)
        data = [{'nome': t.nome, 'geojson': t.coordenadas} for t in existentes]
        context['talhoes_existentes_json'] = json.dumps(data)
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
        import json
        existentes = Talhao.objects.filter(usuario=self.request.user).exclude(pk=self.object.pk).exclude(coordenadas__isnull=True)
        data = [{'nome': t.nome, 'geojson': t.coordenadas} for t in existentes]
        context['talhoes_existentes_json'] = json.dumps(data)
        return context

class TalhaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Talhao
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('talhao_list')
    def get_queryset(self):
        return Talhao.objects.filter(usuario=self.request.user)

from django.db import transaction
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from decimal import Decimal

@login_required
@require_POST
def unir_talhoes(request):
    talhao_ids = request.POST.getlist('talhoes_ids')
    novo_nome = request.POST.get('novo_nome')
    tipo_solo = request.POST.get('tipo_solo', 'Misto')
    observacoes = request.POST.get('observacoes', '')

    if len(talhao_ids) < 2:
        messages.error(request, 'Selecione pelo menos 2 talhões para unir.')
        return redirect('talhao_list')

    talhoes = Talhao.objects.filter(id__in=talhao_ids, usuario=request.user)
    
    if talhoes.count() != len(talhao_ids):
        messages.error(request, 'Talhões inválidos ou não pertencem a você.')
        return redirect('talhao_list')

    if Plantio.objects.filter(talhao__in=talhoes, status__in=['ATIVO', 'PREPARO', 'COLHEITA']).exists():
        messages.error(request, 'Não é possível unir talhões que possuem plantios ativos. Finalize-os primeiro.')
        return redirect('talhao_list')

    try:
        with transaction.atomic():
            area_total = sum(t.area_m2 for t in talhoes)
            
            import json
            multipolygon_coords = []
            for t in talhoes:
                if t.coordenadas:
                    try:
                        coord_dict = t.coordenadas if isinstance(t.coordenadas, dict) else json.loads(t.coordenadas)
                        geom = coord_dict.get('geometry') if coord_dict.get('type') == 'Feature' else coord_dict
                        
                        geom_type = geom.get('type')
                        coords = geom.get('coordinates', [])
                        
                        if geom_type == 'Polygon':
                            multipolygon_coords.append(coords)
                        elif geom_type == 'MultiPolygon':
                            multipolygon_coords.extend(coords)
                    except Exception:
                        pass
            
            merged_geojson = None
            if multipolygon_coords:
                merged_geojson = {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": multipolygon_coords
                    },
                    "properties": {}
                }

            novo_talhao = Talhao(
                nome=novo_nome,
                area_m2=area_total,
                tipo_solo=tipo_solo,
                observacoes=observacoes,
                coordenadas=merged_geojson
            )
            novo_talhao.usuario = request.user
            
            novo_talhao.save()
            
            Plantio.objects.filter(talhao__in=talhoes).update(talhao=novo_talhao)
            
            talhoes.delete()
            
            messages.success(request, f'Sucesso: "{novo_nome}" criado com {area_total} m² e todo histórico preservado.')
            
    except Exception as e:
        messages.error(request, f'Falha ao mesclar talhões no banco de dados: {str(e)}')

    return redirect('talhao_list')

@login_required
@require_POST
def dividir_talhao(request, pk):
    talhao = get_object_or_404(Talhao, pk=pk, usuario=request.user)
    
    nomes = request.POST.getlist('fracao_nome[]')
    areas = request.POST.getlist('fracao_area[]')
    
    if not nomes or not areas or len(nomes) != len(areas) or len(nomes) < 2:
        messages.error(request, 'Dados de fracionamento inválidos. Informe pelo menos 2 frações.')
        return redirect('talhao_list')

    try:
        areas_decimal = [Decimal(a) for a in areas]
    except Exception:
        messages.error(request, 'Valores de área inválidos.')
        return redirect('talhao_list')

    if sum(areas_decimal) != talhao.area_m2:
        messages.error(request, 'A soma das áreas das frações deve ser exatamente igual à área original do talhão.')
        return redirect('talhao_list')

    with transaction.atomic():
        for nome, area in zip(nomes, areas_decimal):
            Talhao.objects.create(
                usuario=request.user,
                nome=nome,
                area_m2=area,
                tipo_solo=talhao.tipo_solo,
                coordenadas=talhao.coordenadas
            )
        talhao.delete()
        messages.success(request, 'Talhão dividido com sucesso.')

    return redirect('talhao_list')

@login_required
@require_POST
def dividir_talhao_mapa(request):
    talhao_id = request.POST.get('talhao_id')
    nomes = request.POST.getlist('corte_nomes[]')
    areas = request.POST.getlist('corte_areas[]')
    geojsons = request.POST.getlist('corte_geojsons[]')
    
    if not talhao_id or not nomes or len(nomes) < 2:
        messages.error(request, 'Dados de corte inválidos.')
        return redirect('talhao_list')
        
    talhao = get_object_or_404(Talhao, pk=talhao_id, usuario=request.user)
    
    try:
        with transaction.atomic():
            for nome, area, geojson in zip(nomes, areas, geojsons):
                novo = Talhao.objects.create(
                    usuario=request.user,
                    nome=nome,
                    area_m2=Decimal(area),
                    tipo_solo=talhao.tipo_solo,
                    coordenadas=geojson
                )
            
            primeiro_novo = Talhao.objects.filter(usuario=request.user, nome=nomes[0]).last()
            Plantio.objects.filter(talhao=talhao).update(talhao=primeiro_novo)
            
            talhao.delete()
            messages.success(request, f'Talhão cortado visualmente em {len(nomes)} partes com sucesso!')
            
    except Exception as e:
        messages.error(request, f'Falha ao processar o corte geográfico: {str(e)}')

    return redirect('talhao_list')

@login_required
@require_POST
def registrar_colheita(request, pk):
    plantio = get_object_or_404(Plantio, pk=pk, talhao__usuario=request.user)
    
    data_colheita = request.POST.get('data_colheita')
    quantidade = request.POST.get('quantidade', '')
    destino = request.POST.get('destino_talhao')
    observacoes = request.POST.get('observacoes', '')

    try:
        with transaction.atomic():
            if destino in dict(Plantio.STATUS_CHOICES):
                plantio.status = destino
                plantio.save()

            if data_colheita:
                from datetime import datetime
                Manejo.objects.create(
                    plantio=plantio,
                    data=datetime.strptime(data_colheita, '%Y-%m-%d').date(),
                    tipo_operacao='Colheita',
                    produto_insumo='Produção colhida',
                    dosagem_quantidade=quantidade,
                    observacoes=observacoes
                )

        messages.success(request, f'Colheita registrada com sucesso para o plantio de {plantio.cultura}!')
    except Exception as e:
        messages.error(request, f'Erro ao registrar colheita: {str(e)}')

    return redirect('plantio_list')

class PlantioListView(LoginRequiredMixin, ListView):
    model = Plantio
    template_name = 'core/plantio_list.html'
    context_object_name = 'plantios'
    def get_queryset(self):
        return Plantio.objects.filter(talhao__usuario=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import json
        plantios_data = []
        for p in context['plantios']:
            if p.talhao.coordenadas:
                status_dias = "Pronto para colheita" if p.dias_restantes() <= 0 else f"Faltam {p.dias_restantes()} dias (Dia {p.dias_passados()} de {p.ciclo_dias_estimado})"
                plantios_data.append({
                    'id': p.id,
                    'cultura': p.cultura,
                    'status': p.get_status_display(),
                    'talhao': p.talhao.nome,
                    'variedade': p.variedade or "Não informada",
                    'data_plantio': p.data_plantio.strftime('%d/%m/%Y') if p.data_plantio else "Não definido",
                    'ciclo': p.ciclo_dias_estimado,
                    'status_dias': status_dias,
                    'geojson': p.talhao.coordenadas
                })
        context['plantios_json'] = json.dumps(plantios_data)
        return context

class PlantioDetailView(LoginRequiredMixin, DetailView):
    model = Plantio
    template_name = 'core/plantio_detail.html'
    context_object_name = 'plantio'
    def get_queryset(self):
        return Plantio.objects.filter(talhao__usuario=self.request.user)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

@login_required
def talhao_dashboard(request, pk):
    talhao = get_object_or_404(Talhao, pk=pk, usuario=request.user)
    todos_talhoes = Talhao.objects.filter(usuario=request.user).order_by('nome')

    # Plantio ativo ou em andamento
    plantio_ativo = Plantio.objects.filter(
        talhao=talhao,
        status__in=['ATIVO', 'PREPARO', 'COLHEITA']
    ).order_by('-id').first()

    # Histórico de plantios neste talhão
    plantios_historico = Plantio.objects.filter(talhao=talhao).order_by('-data_plantio', '-id')

    # Histórico de Manejos, Irrigações e Ocorrências no Talhão
    manejos = Manejo.objects.filter(plantio__talhao=talhao).select_related('plantio').order_by('-data', '-id')
    irrigacoes = Irrigacao.objects.filter(plantio__talhao=talhao).select_related('plantio').order_by('-data_hora', '-id')
    ocorrencias = Ocorrencia.objects.filter(plantio__talhao=talhao).select_related('plantio').order_by('-data', '-id')

    # Contagens e estatísticas de aplicações
    total_irrigacoes = irrigacoes.count()
    total_adubacoes = manejos.filter(tipo_operacao__icontains='Adubação').count()
    total_defensivos = manejos.filter(tipo_operacao__icontains='Pulverização').count() + manejos.filter(tipo_operacao__icontains='Defensivo').count()
    total_ocorrencias = ocorrencias.count()
    total_aplicacoes = total_irrigacoes + manejos.count()

    # Linha do tempo unificada de manejos e atividades
    timeline_manejos = []
    for m in manejos:
        badge_class = "bg-primary"
        icon_class = "bi-gear-fill"
        tipo_lower = m.tipo_operacao.lower()
        if "adubação" in tipo_lower:
            badge_class = "bg-success"
            icon_class = "bi-droplet-half"
        elif "pulverização" in tipo_lower or "defensivo" in tipo_lower:
            badge_class = "bg-danger"
            icon_class = "bi-shield-shaded"
        elif "colheita" in tipo_lower:
            badge_class = "bg-warning text-dark"
            icon_class = "bi-basket2-fill"
        elif "poda" in tipo_lower or "capina" in tipo_lower:
            badge_class = "bg-secondary"
            icon_class = "bi-scissors"

        timeline_manejos.append({
            'data': m.data,
            'data_display': m.data.strftime('%d/%m/%Y'),
            'tipo_categoria': 'Manejo',
            'tipo_operacao': m.tipo_operacao,
            'produto_insumo': m.produto_insumo,
            'dosagem': m.dosagem_quantidade,
            'observacoes': m.observacoes,
            'cultura': m.plantio.cultura if m.plantio else "-",
            'badge_class': badge_class,
            'icon_class': icon_class
        })

    for irr in irrigacoes:
        timeline_manejos.append({
            'data': irr.data_hora.date(),
            'data_display': irr.data_hora.strftime('%d/%m/%Y %H:%M'),
            'tipo_categoria': 'Irrigação',
            'tipo_operacao': 'Irrigação',
            'produto_insumo': f"Lâmina/Volume: {irr.lamina_ou_volume or 'Convencional'}",
            'dosagem': f"{irr.duracao_minutos} min",
            'observacoes': irr.observacoes,
            'cultura': irr.plantio.cultura if irr.plantio else "-",
            'badge_class': 'bg-info text-dark',
            'icon_class': 'bi-droplet-fill'
        })

    timeline_manejos.sort(key=lambda x: x['data'], reverse=True)

    # Cálculo da área em hectares (1 ha = 10.000 m²)
    area_ha = round(float(talhao.area_m2) / 10000.0, 2)

    # Status textual e classe de badge do talhão
    if plantio_ativo:
        if plantio_ativo.status == 'ATIVO':
            status_display = 'Ativo'
            status_badge_class = 'bg-success'
        elif plantio_ativo.status == 'PREPARO':
            status_display = 'Preparo'
            status_badge_class = 'bg-warning text-dark'
        elif plantio_ativo.status == 'COLHEITA':
            status_display = 'Em Colheita'
            status_badge_class = 'bg-info text-dark'
        else:
            status_display = plantio_ativo.get_status_display()
            status_badge_class = 'bg-secondary'
    else:
        status_display = 'Sem Plantio'
        status_badge_class = 'bg-secondary'

    # GeoJSON do Talhão para o Leaflet
    import json
    talhao_geojson = None
    if talhao.coordenadas:
        if isinstance(talhao.coordenadas, dict):
            talhao_geojson = json.dumps(talhao.coordenadas)
        else:
            talhao_geojson = str(talhao.coordenadas)

    context = {
        'talhao': talhao,
        'todos_talhoes': todos_talhoes,
        'plantio_ativo': plantio_ativo,
        'status_display': status_display,
        'status_badge_class': status_badge_class,
        'area_ha': area_ha,
        'total_irrigacoes': total_irrigacoes,
        'total_adubacoes': total_adubacoes,
        'total_defensivos': total_defensivos,
        'total_ocorrencias': total_ocorrencias,
        'total_aplicacoes': total_aplicacoes,
        'timeline_manejos': timeline_manejos,
        'ocorrencias': ocorrencias,
        'plantios_historico': plantios_historico,
        'talhao_geojson': talhao_geojson,
    }
    return render(request, 'core/talhao_dashboard.html', context)
