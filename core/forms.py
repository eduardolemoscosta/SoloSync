from django import forms
from .models import Propriedade, Talhao, Plantio, Manejo, Irrigacao, Ocorrencia, PerfilUsuario

class PropriedadeForm(forms.ModelForm):
    class Meta:
        model = Propriedade
        fields = ['nome', 'cidade', 'estado', 'latitude_sede', 'longitude_sede', 'area_total_ha']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Fazenda Santa Luzia'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Petrolina'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: PE', 'maxlength': '2'}),
            'latitude_sede': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'id': 'id_latitude_sede'}),
            'longitude_sede': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'id': 'id_longitude_sede'}),
            'area_total_ha': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex: 120.50'}),
        }


class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['nome_propriedade', 'latitude_propriedade', 'longitude_propriedade']
        widgets = {
            'nome_propriedade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Fazenda Boa Esperança'}),
            'latitude_propriedade': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'id': 'id_latitude'}),
            'longitude_propriedade': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'id': 'id_longitude'}),
        }


class TalhaoForm(forms.ModelForm):
    class Meta:
        model = Talhao
        fields = ['propriedade', 'nome', 'area_m2', 'tipo_solo', 'coordenadas_json', 'observacoes']
        widgets = {
            'propriedade': forms.Select(attrs={'class': 'form-select', 'id': 'id_propriedade'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Talhão 01, T1'}),
            'area_m2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'tipo_solo': forms.Select(attrs={'class': 'form-select'}),
            'coordenadas_json': forms.HiddenInput(attrs={'id': 'id_coordenadas_json'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TalhaoForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['propriedade'].queryset = Propriedade.objects.filter(usuario=user)
            if not self.instance.pk and self.fields['propriedade'].queryset.exists():
                self.fields['propriedade'].initial = self.fields['propriedade'].queryset.first()


class PlantioForm(forms.ModelForm):
    class Meta:
        model = Plantio
        fields = ['talhao', 'cultura', 'variedade', 'data_plantio', 'ciclo_dias_estimado', 'status']
        widgets = {
            'talhao': forms.Select(attrs={'class': 'form-select'}),
            'cultura': forms.TextInput(attrs={'class': 'form-control'}),
            'variedade': forms.TextInput(attrs={'class': 'form-control'}),
            'data_plantio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ciclo_dias_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PlantioForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['talhao'].queryset = Talhao.objects.filter(propriedade__usuario=user, ativo=True)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        cultura = cleaned_data.get('cultura')
        data_plantio = cleaned_data.get('data_plantio')
        ciclo = cleaned_data.get('ciclo_dias_estimado')

        if status == 'PREPARO':
            cleaned_data['cultura'] = cultura or "Preparo de Solo"
            cleaned_data['variedade'] = ""
            cleaned_data['data_plantio'] = None
            cleaned_data['ciclo_dias_estimado'] = 0
        else:
            if not cultura or cultura == "Preparo de Solo":
                self.add_error('cultura', 'Cultura é obrigatória quando o status não for Preparo.')
            if not data_plantio:
                self.add_error('data_plantio', 'Data de Plantio é obrigatória.')
            if ciclo is None or ciclo <= 0:
                self.add_error('ciclo_dias_estimado', 'Ciclo estimado é obrigatório.')

        return cleaned_data


class ManejoForm(forms.ModelForm):
    class Meta:
        model = Manejo
        fields = ['plantio', 'data', 'tipo_operacao', 'produto_insumo', 'dosagem_quantidade', 'observacoes']
        widgets = {
            'plantio': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'produto_insumo': forms.TextInput(attrs={'class': 'form-control'}),
            'dosagem_quantidade': forms.TextInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ManejoForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['plantio'].queryset = Plantio.objects.filter(talhao__propriedade__usuario=user)


class IrrigacaoForm(forms.ModelForm):
    class Meta:
        model = Irrigacao
        fields = ['plantio', 'data_hora', 'duracao_minutos', 'lamina_ou_volume', 'observacoes']
        widgets = {
            'plantio': forms.Select(attrs={'class': 'form-select'}),
            'data_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duracao_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'lamina_ou_volume': forms.TextInput(attrs={'class': 'form-control'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(IrrigacaoForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['plantio'].queryset = Plantio.objects.filter(talhao__propriedade__usuario=user)


class OcorrenciaForm(forms.ModelForm):
    class Meta:
        model = Ocorrencia
        fields = ['plantio', 'data', 'tipo', 'descricao', 'acao_tomada']
        widgets = {
            'plantio': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'acao_tomada': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(OcorrenciaForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['plantio'].queryset = Plantio.objects.filter(talhao__propriedade__usuario=user)
