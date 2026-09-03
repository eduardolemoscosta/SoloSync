from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction, models
from decimal import Decimal
import json
from .models import Propriedade, Talhao, Plantio, Manejo, Irrigacao, Ocorrencia, PerfilUsuario
from .forms import PropriedadeForm, TalhaoForm, PlantioForm, ManejoForm, IrrigacaoForm, OcorrenciaForm, PerfilUsuarioForm
from django.contrib.auth import login


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            PerfilUsuario.objects.get_or_create(usuario=user)
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Cadastre sua primeira propriedade/fazenda.')
            return redirect('propriedade_create')
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


# ==========================================
# CRUD de Propriedades / Terras (Fazendas)
# ==========================================

class PropriedadeListView(LoginRequiredMixin, ListView):
    model = Propriedade
    template_name = 'core/propriedade_list.html'
    context_object_name = 'propriedades'

    def get_queryset(self):
        return Propriedade.objects.filter(usuario=self.request.user).annotate(
            total_talhoes=models.Count('talhoes', filter=models.Q(talhoes__ativo=True))
        ).order_by('-criado_em')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        propriedades_data = []
        for p in context['propriedades']:
            propriedades_data.append({
                'id': p.id,
                'nome': p.nome,
                'cidade': p.cidade or '',
                'estado': p.estado or '',
                'lat': p.latitude_sede,
                'lng': p.longitude_sede,
                'area_ha': str(p.area_total_ha) if p.area_total_ha else '0',
                'talhoes_count': p.total_talhoes
            })
        context['propriedades_json'] = json.dumps(propriedades_data)
        return context


class PropriedadeCreateView(LoginRequiredMixin, CreateView):
    model = Propriedade
    form_class = PropriedadeForm
    template_name = 'core/propriedade_form.html'
    success_url = reverse_lazy('propriedade_list')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, f'Propriedade "{form.instance.nome}" cadastrada com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cadastrar Nova Propriedade / Terra'
        return context


class PropriedadeUpdateView(LoginRequiredMixin, UpdateView):
    model = Propriedade
    form_class = PropriedadeForm
    template_name = 'core/propriedade_form.html'
    success_url = reverse_lazy('propriedade_list')

    def get_queryset(self):
        return Propriedade.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Propriedade "{form.instance.nome}" atualizada com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Propriedade: {self.object.nome}'
        return context


class PropriedadeDeleteView(LoginRequiredMixin, DeleteView):
    model = Propriedade
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('propriedade_list')

    def get_queryset(self):
        return Propriedade.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Propriedade excluída com sucesso.')
        return super().form_valid(form)


# ==========================================
# Dashboard & Talhões
# ==========================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        plantios = Plantio.objects.filter(talhao__propriedade__usuario=user)
        context['total_propriedades'] = Propriedade.objects.filter(usuario=user).count()
        context['plantios_ativos'] = plantios.filter(status='ATIVO').count()
        context['areas_preparo'] = plantios.filter(status='PREPARO').count()
        context['total_talhoes'] = Talhao.objects.filter(propriedade__usuario=user, ativo=True).count()
        context['plantios_andamento'] = plantios.exclude(status='FINALIZADO').order_by('-data_plantio')
        return context


class TalhaoListView(LoginRequiredMixin, ListView):
    model = Talhao
    template_name = 'core/talhao_list.html'
    context_object_name = 'talhoes'

    def get_queryset(self):
        # Rotina para alocar talhões órfãos
        orfaos = Talhao.objects.filter(propriedade__isnull=True)
        if orfaos.exists():
            prop_padrao, _ = Propriedade.objects.get_or_create(
                usuario=self.request.user,
                nome="Propriedade Padrão (Recuperada)",
                defaults={
                    'latitude_sede': -5.8958,
                    'longitude_sede': -35.7633,
                    'area_total_ha': 0
                }
            )
            orfaos.update(propriedade=prop_padrao)

        qs = Talhao.objects.filter(propriedade__usuario=self.request.user, ativo=True).select_related('propriedade')
        propriedade_id = self.request.GET.get('propriedade')
        if propriedade_id:
            qs = qs.filter(propriedade_id=propriedade_id)
        return qs.order_by('propriedade__nome', 'nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        talhoes_data = []
        for t in context['talhoes']:
            if t.coordenadas_json:
                talhoes_data.append({
                    'id': t.id,
                    'nome': t.nome,
                    'propriedade_nome': t.propriedade.nome,
                    'area': str(t.area_m2),
                    'geojson': t.coordenadas_json
                })
        context['talhoes_json'] = json.dumps(talhoes_data)
        context['propriedades'] = Propriedade.objects.filter(usuario=self.request.user).order_by('nome')
        context['selected_propriedade'] = self.request.GET.get('propriedade', '')

        # Se houver propriedade selecionada, obter suas coordenadas centrais
        prop_selecionada = None
        if context['selected_propriedade']:
            prop_selecionada = context['propriedades'].filter(id=context['selected_propriedade']).first()
        elif context['propriedades'].exists():
            prop_selecionada = context['propriedades'].first()

        context['centro_mapa_lat'] = prop_selecionada.latitude_sede if prop_selecionada else -5.8958
        context['centro_mapa_lng'] = prop_selecionada.longitude_sede if prop_selecionada else -35.7633
        return context


class TalhaoCreateView(LoginRequiredMixin, CreateView):
    model = Talhao
    form_class = TalhaoForm
    template_name = 'core/talhao_form.html'
    success_url = reverse_lazy('talhao_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        propriedade_id = self.request.GET.get('propriedade')
        if propriedade_id:
            initial['propriedade'] = propriedade_id
        return initial

    def form_valid(self, form):
        # Captura o ID da propriedade que está selecionada na tela
        prop_id = self.request.POST.get('propriedade')
        if prop_id:
            form.instance.propriedade_id = prop_id

        if not form.instance.propriedade:
            messages.error(self.request, 'Selecione uma propriedade.')
            return self.form_invalid(form)

        # Valida que a propriedade pertence ao usuário
        if form.instance.propriedade.usuario != self.request.user:
            messages.error(self.request, 'Propriedade inválida.')
            return self.form_invalid(form)
        messages.success(self.request, f'Talhão "{form.instance.nome}" criado com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Novo Talhão'
        
        user_props = Propriedade.objects.filter(usuario=self.request.user)
        propriedades_map = {}
        propriedades_geojson = {}
        for p in user_props:
            propriedades_map[str(p.id)] = {
                'lat': p.latitude_sede,
                'lng': p.longitude_sede,
                'nome': p.nome
            }
            if p.contorno_geojson:
                propriedades_geojson[str(p.id)] = p.contorno_geojson
                
        context['propriedades_map_json'] = json.dumps(propriedades_map)
        context['propriedades_json'] = json.dumps(propriedades_geojson)

        existentes = Talhao.objects.filter(propriedade__usuario=self.request.user, ativo=True).exclude(coordenadas_json__isnull=True)
        data = [{'nome': t.nome, 'propriedade_id': t.propriedade_id, 'geojson': t.coordenadas_json} for t in existentes]
        context['talhoes_existentes_json'] = json.dumps(data)

        primeira_prop = user_props.first()
        context['default_lat'] = primeira_prop.latitude_sede if primeira_prop else -5.8958
        context['default_lng'] = primeira_prop.longitude_sede if primeira_prop else -35.7633
        return context


class TalhaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Talhao
    form_class = TalhaoForm
    template_name = 'core/talhao_form.html'
    success_url = reverse_lazy('talhao_list')

    def get_queryset(self):
        return Talhao.objects.filter(propriedade__usuario=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if form.instance.propriedade.usuario != self.request.user:
            messages.error(self.request, 'Propriedade inválida.')
            return self.form_invalid(form)
        messages.success(self.request, f'Talhão "{form.instance.nome}" atualizado com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Talhão: {self.object.nome}'
        
        user_props = Propriedade.objects.filter(usuario=self.request.user)
        propriedades_map = {}
        propriedades_geojson = {}
        for p in user_props:
            propriedades_map[str(p.id)] = {
                'lat': p.latitude_sede,
                'lng': p.longitude_sede,
                'nome': p.nome
            }
            if p.contorno_geojson:
                propriedades_geojson[str(p.id)] = p.contorno_geojson
                
        context['propriedades_map_json'] = json.dumps(propriedades_map)
        context['propriedades_json'] = json.dumps(propriedades_geojson)

        existentes = Talhao.objects.filter(propriedade__usuario=self.request.user, ativo=True).exclude(pk=self.object.pk).exclude(coordenadas_json__isnull=True)
        data = [{'nome': t.nome, 'propriedade_id': t.propriedade_id, 'geojson': t.coordenadas_json} for t in existentes]
        context['talhoes_existentes_json'] = json.dumps(data)

        context['default_lat'] = self.object.propriedade.latitude_sede
        context['default_lng'] = self.object.propriedade.longitude_sede
        return context


class TalhaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Talhao
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('talhao_list')

    def get_queryset(self):
        return Talhao.objects.filter(propriedade__usuario=self.request.user)


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

    talhoes = Talhao.objects.filter(id__in=talhao_ids, propriedade__usuario=request.user)
    
    if talhoes.count() != len(talhao_ids):
        messages.error(request, 'Talhões inválidos ou não pertencem a você.')
        return redirect('talhao_list')

    # Valida se pertencem à mesma propriedade
    propriedades_ids = set(t.propriedade_id for t in talhoes)
    if len(propriedades_ids) > 1:
        messages.error(request, 'Só é possível unir talhões que pertencem à mesma propriedade.')
        return redirect('talhao_list')

    propriedade_origem = talhoes.first().propriedade

    if Plantio.objects.filter(talhao__in=talhoes, status__in=['ATIVO', 'PREPARO', 'COLHEITA']).exists():
        messages.error(request, 'Não é possível unir talhões que possuem plantios ativos. Finalize-os primeiro.')
        return redirect('talhao_list')

    try:
        with transaction.atomic():
            area_total = sum(t.area_m2 for t in talhoes)
            
            multipolygon_coords = []
            for t in talhoes:
                if t.coordenadas_json:
                    try:
                        coord_dict = t.coordenadas_json if isinstance(t.coordenadas_json, dict) else json.loads(t.coordenadas_json)
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
                propriedade=propriedade_origem,
                nome=novo_nome,
                area_m2=area_total,
                tipo_solo=tipo_solo,
                observacoes=observacoes,
                coordenadas_json=merged_geojson
            )
            novo_talhao.save()
            
            Plantio.objects.filter(talhao__in=talhoes).update(talhao=novo_talhao)
            
            talhoes.delete()
            
            messages.success(request, f'Sucesso: "{novo_nome}" criado com {area_total} m² na propriedade {propriedade_origem.nome}.')
            
    except Exception as e:
        messages.error(request, f'Falha ao mesclar talhões no banco de dados: {str(e)}')

    return redirect('talhao_list')


@login_required
@require_POST
def dividir_talhao(request, pk):
    talhao = get_object_or_404(Talhao, pk=pk, propriedade__usuario=request.user)
    
    nomes = request.POST.getlist('fracao_nome[]')
    areas = request.POST.getlist('fracao_area[]')
    
    if not nomes or not areas or len(nomes) != len(areas) or len(nomes) < 2:
        messages.error(request, 'Dados de fracionamento inválidos. Informe pelo menos 2 frações.')
        return redirect('talhao_list')

    try:
        areas_float = [float(a) for a in areas]
    except Exception:
        messages.error(request, 'Valores de área inválidos.')
        return redirect('talhao_list')

    if abs(sum(areas_float) - talhao.area_m2) > 0.05:
        messages.error(request, 'A soma das áreas das frações deve ser igual à área original do talhão.')
        return redirect('talhao_list')

    with transaction.atomic():
        for nome, area in zip(nomes, areas_float):
            Talhao.objects.create(
                propriedade=talhao.propriedade,
                nome=nome,
                area_m2=area,
                tipo_solo=talhao.tipo_solo,
                coordenadas_json=talhao.coordenadas_json
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
        
    talhao = get_object_or_404(Talhao, pk=talhao_id, propriedade__usuario=request.user)
    
    try:
        with transaction.atomic():
            for nome, area, geojson in zip(nomes, areas, geojsons):
                Talhao.objects.create(
                    propriedade=talhao.propriedade,
                    nome=nome,
                    area_m2=float(area),
                    tipo_solo=talhao.tipo_solo,
                    coordenadas_json=geojson
                )
            
            primeiro_novo = Talhao.objects.filter(propriedade=talhao.propriedade, nome=nomes[0]).last()
            Plantio.objects.filter(talhao=talhao).update(talhao=primeiro_novo)
            
            talhao.delete()
            messages.success(request, f'Talhão cortado visualmente em {len(nomes)} partes com sucesso!')
            
    except Exception as e:
        messages.error(request, f'Falha ao processar o corte geográfico: {str(e)}')

    return redirect('talhao_list')


@login_required
@require_POST
def registrar_colheita(request, pk):
    plantio = get_object_or_404(Plantio, pk=pk, talhao__propriedade__usuario=request.user)
    
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


# ==========================================
# Plantios, Manejos, Irrigações e Ocorrências
# ==========================================

class PlantioListView(LoginRequiredMixin, ListView):
    model = Plantio
    template_name = 'core/plantio_list.html'
    context_object_name = 'plantios'

    def get_queryset(self):
        return Plantio.objects.filter(talhao__propriedade__usuario=self.request.user).select_related('talhao', 'talhao__propriedade')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plantios_data = []
        for p in context['plantios']:
            if p.talhao.coordenadas_json:
                status_dias = "Pronto para colheita" if p.dias_restantes() <= 0 else f"Faltam {p.dias_restantes()} dias (Dia {p.dias_passados()} de {p.ciclo_dias_estimado})"
                plantios_data.append({
                    'id': p.id,
                    'cultura': p.cultura,
                    'status': p.get_status_display(),
                    'talhao': f"{p.talhao.nome} ({p.talhao.propriedade.nome})",
                    'variedade': p.variedade or "Não informada",
                    'data_plantio': p.data_plantio.strftime('%d/%m/%Y') if p.data_plantio else "Não definido",
                    'ciclo': p.ciclo_dias_estimado,
                    'status_dias': status_dias,
                    'geojson': p.talhao.coordenadas_json
                })
        context['plantios_json'] = json.dumps(plantios_data)
        
        primeira_prop = Propriedade.objects.filter(usuario=self.request.user).first()
        context['default_lat'] = primeira_prop.latitude_sede if primeira_prop else -5.8958
        context['default_lng'] = primeira_prop.longitude_sede if primeira_prop else -35.7633
        return context


class PlantioDetailView(LoginRequiredMixin, DetailView):
    model = Plantio
    template_name = 'core/plantio_detail.html'
    context_object_name = 'plantio'

    def get_queryset(self):
        return Plantio.objects.filter(talhao__propriedade__usuario=self.request.user)

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
        return Plantio.objects.filter(talhao__propriedade__usuario=self.request.user)

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
        return Plantio.objects.filter(talhao__propriedade__usuario=self.request.user)


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
    talhao = get_object_or_404(Talhao, pk=pk, propriedade__usuario=request.user)
    todos_talhoes = Talhao.objects.filter(propriedade=talhao.propriedade, ativo=True).order_by('nome')

    plantio_ativo = Plantio.objects.filter(
        talhao=talhao,
        status__in=['ATIVO', 'PREPARO', 'COLHEITA']
    ).order_by('-id').first()

    plantios_historico = Plantio.objects.filter(talhao=talhao).order_by('-data_plantio', '-id')

    manejos = Manejo.objects.filter(plantio__talhao=talhao).select_related('plantio').order_by('-data', '-id')
    irrigacoes = Irrigacao.objects.filter(plantio__talhao=talhao).select_related('plantio').order_by('-data_hora', '-id')
    ocorrencias = Ocorrencia.objects.filter(plantio__talhao=talhao).select_related('plantio').order_by('-data', '-id')

    total_irrigacoes = irrigacoes.count()
    total_adubacoes = manejos.filter(tipo_operacao__icontains='Adubação').count()
    total_defensivos = manejos.filter(tipo_operacao__icontains='Pulverização').count() + manejos.filter(tipo_operacao__icontains='Defensivo').count()
    total_ocorrencias = ocorrencias.count()
    total_aplicacoes = total_irrigacoes + manejos.count()

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

    area_ha = round(float(talhao.area_m2) / 10000.0, 2)

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

    talhao_geojson = None
    if talhao.coordenadas_json:
        if isinstance(talhao.coordenadas_json, dict):
            talhao_geojson = json.dumps(talhao.coordenadas_json)
        else:
            talhao_geojson = str(talhao.coordenadas_json)

    context = {
        'talhao': talhao,
        'propriedade': talhao.propriedade,
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
        'default_lat': talhao.propriedade.latitude_sede,
        'default_lng': talhao.propriedade.longitude_sede,
    }
    return render(request, 'core/talhao_dashboard.html', context)

