from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nome_propriedade = models.CharField('Nome da Propriedade', max_length=150, blank=True, null=True)
    latitude_propriedade = models.FloatField('Latitude', default=-5.8958)
    longitude_propriedade = models.FloatField('Longitude', default=-35.7633)
    propriedade_configurada = models.BooleanField('Propriedade Configurada', default=False)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.get_or_create(usuario=instance)
    else:
        if not hasattr(instance, 'perfil'):
            PerfilUsuario.objects.get_or_create(usuario=instance)


class Propriedade(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='propriedades')
    nome = models.CharField(max_length=150)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    latitude_sede = models.FloatField(help_text="Coordenada para centralizar o mapa da terra")
    longitude_sede = models.FloatField(help_text="Coordenada para centralizar o mapa da terra")
    area_total_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contorno_geojson = models.JSONField(blank=True, null=True, help_text="Coordenadas do perímetro da propriedade")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.usuario.username})"


class Talhao(models.Model):
    TIPO_SOLO_CHOICES = [
        ('Arenoso', 'Arenoso'),
        ('Argiloso', 'Argiloso'),
        ('Misto', 'Misto'),
        ('Siltoso', 'Siltoso'),
        ('Outro', 'Outro'),
    ]

    SISTEMA_IRRIGACAO_CHOICES = [
        ('GOTEJAMENTO', 'Gotejamento'),
        ('ASPERSAO', 'Aspersão'),
        ('MICROASPERSAO', 'Microaspersão'),
        ('PIVO', 'Pivô Central'),
        ('SEQUEIRO', 'Sequeiro / Sem Irrigação'),
    ]

    propriedade = models.ForeignKey(Propriedade, on_delete=models.CASCADE, related_name='talhoes', null=True, blank=True)
    nome = models.CharField(max_length=100)
    area_m2 = models.FloatField()
    tipo_solo = models.CharField(max_length=100, choices=TIPO_SOLO_CHOICES, default='Misto', blank=True, null=True)
    sistema_irrigacao = models.CharField(max_length=20, choices=SISTEMA_IRRIGACAO_CHOICES, default='SEQUEIRO')
    coordenadas_json = models.JSONField(help_text="Polígono do talhão no mapa [[lat, lng], ...]", null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def coordenadas(self):
        return self.coordenadas_json

    @coordenadas.setter
    def coordenadas(self, value):
        self.coordenadas_json = value

    @property
    def usuario(self):
        return self.propriedade.usuario

    def __str__(self):
        return f"{self.nome} - {self.propriedade.nome}"

class Plantio(models.Model):
    STATUS_CHOICES = [
        ('PREPARO', 'Preparo do talhão'),
        ('ATIVO', 'Ativo / Em desenvolvimento'),
        ('COLHEITA', 'Em Colheita'),
        ('FINALIZADO', 'Finalizado'),
    ]

    talhao = models.ForeignKey(Talhao, on_delete=models.CASCADE, related_name='plantios')
    cultura = models.CharField(max_length=100, blank=True, null=True, default="Preparo de Solo")
    variedade = models.CharField(max_length=100, blank=True, null=True)
    data_plantio = models.DateField(blank=True, null=True)
    ciclo_dias_estimado = models.PositiveIntegerField('Ciclo (dias)', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PREPARO')

    def data_prevista_colheita(self):
        if self.data_plantio and self.ciclo_dias_estimado:
            return self.data_plantio + timedelta(days=self.ciclo_dias_estimado)
        return None

    def dias_decorridos(self):
        if self.data_plantio:
            delta = date.today() - self.data_plantio
            return max(0, delta.days)
        return 0

    def dias_passados(self):
        return self.dias_decorridos()

    def dias_restantes(self):
        if not self.data_plantio or not self.ciclo_dias_estimado:
            return 0
        restantes = self.ciclo_dias_estimado - self.dias_passados()
        return max(0, restantes)

    def progresso_ciclo_porcentagem(self):
        if not self.data_plantio or not self.ciclo_dias_estimado:
            return 0
        decorridos = self.dias_decorridos()
        if decorridos >= self.ciclo_dias_estimado:
            return 100
        return int((decorridos / self.ciclo_dias_estimado) * 100)

    def porcentagem_progresso(self):
        return self.progresso_ciclo_porcentagem()

    def __str__(self):
        return f"{self.cultura} - {self.talhao.nome} ({self.get_status_display()})"

class Manejo(models.Model):
    TIPO_OPERACAO_CHOICES = [
        ('Adubação de Fundação', 'Adubação de Fundação'),
        ('Adubação de Cobertura', 'Adubação de Cobertura'),
        ('Pulverização/Defensivo', 'Pulverização/Defensivo'),
        ('Poda/Desbrota', 'Poda/Desbrota'),
        ('Capina/Roçada', 'Capina/Roçada'),
        ('Tratos Culturais', 'Tratos Culturais'),
        ('Colheita', 'Colheita'),
    ]

    plantio = models.ForeignKey(Plantio, on_delete=models.CASCADE, related_name='manejos')
    data = models.DateField(default=timezone.now)
    tipo_operacao = models.CharField(max_length=100, choices=TIPO_OPERACAO_CHOICES)
    produto_insumo = models.CharField(max_length=150)
    dosagem_quantidade = models.CharField(max_length=100)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_operacao} em {self.plantio.cultura} ({self.data.strftime('%d/%m/%Y')})"

class Irrigacao(models.Model):
    plantio = models.ForeignKey(Plantio, on_delete=models.CASCADE, related_name='irrigacoes')
    data_hora = models.DateTimeField(default=timezone.now)
    duracao_minutos = models.PositiveIntegerField()
    lamina_ou_volume = models.CharField(max_length=50, blank=True, null=True)
    observacoes = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Irrigação: {self.duracao_minutos} min - {self.plantio.cultura}"

class Ocorrencia(models.Model):
    TIPO_OCORRENCIA_CHOICES = [
        ('Praga', 'Praga'),
        ('Doença', 'Doença'),
        ('Deficiência Nutricional', 'Deficiência Nutricional'),
        ('Dano Climático', 'Dano Climático'),
        ('Outro', 'Outro'),
    ]

    plantio = models.ForeignKey(Plantio, on_delete=models.CASCADE, related_name='ocorrencias')
    data = models.DateField(default=timezone.now)
    tipo = models.CharField(max_length=100, choices=TIPO_OCORRENCIA_CHOICES)
    descricao = models.TextField()
    acao_tomada = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.plantio.cultura}"

class RegistroIrrigacao(models.Model):
    plantio = models.ForeignKey(Plantio, on_delete=models.CASCADE, related_name='registros_irrigacao')
    data_irrigacao = models.DateField(default=timezone.now)
    hora_irrigacao = models.TimeField(default=timezone.now)
    duracao_horas = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Tempo de rega em horas")
    volume_mm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Volume estimado em mm (L/m²)")
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Registro de Irrigação: {self.data_irrigacao} - {self.plantio.cultura}"
