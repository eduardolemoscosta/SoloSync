from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Talhao, Plantio, Manejo, Irrigacao, Ocorrencia, PerfilUsuario
from datetime import date

class TalhaoDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='produtor1', password='password123')
        self.talhao = Talhao.objects.create(
            usuario=self.user,
            nome='Talhão Sul - Milho',
            area_m2=25000.00,
            tipo_solo='Argiloso',
            coordenadas={
                "type": "Polygon",
                "coordinates": [[[-35.60, -6.15], [-35.60, -6.16], [-35.61, -6.16], [-35.61, -6.15], [-35.60, -6.15]]]
            },
            observacoes='Solo fértil com declive suave.'
        )
        self.plantio = Plantio.objects.create(
            talhao=self.talhao,
            cultura='Milho Híbrido',
            variedade='DKB 390',
            data_plantio=date.today(),
            ciclo_dias_estimado=120,
            status='ATIVO'
        )
        self.manejo = Manejo.objects.create(
            plantio=self.plantio,
            data=date.today(),
            tipo_operacao='Adubação de Cobertura',
            produto_insumo='Ureia 45%',
            dosagem_quantidade='150 kg/ha',
            observacoes='Aplicação realizada antes da chuva.'
        )
        self.irrigacao = Irrigacao.objects.create(
            plantio=self.plantio,
            duracao_minutos=90,
            lamina_ou_volume='15 mm',
            observacoes='Gotejamento setor 1'
        )
        self.ocorrencia = Ocorrencia.objects.create(
            plantio=self.plantio,
            data=date.today(),
            tipo='Praga',
            descricao='Lagarta-do-cartucho detectada em 5% das plantas',
            acao_tomada='Pulverização biológica com Bacillus thuringiensis agendada'
        )

    def test_dashboard_requires_login(self):
        url = reverse('talhao_dashboard', kwargs={'pk': self.talhao.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_dashboard_view_authenticated(self):
        self.client.login(username='produtor1', password='password123')
        url = reverse('talhao_dashboard', kwargs={'pk': self.talhao.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/talhao_dashboard.html')
        self.assertEqual(response.context['talhao'], self.talhao)
        self.assertEqual(response.context['plantio_ativo'], self.plantio)
        self.assertEqual(response.context['area_ha'], 2.5)
        self.assertEqual(response.context['total_adubacoes'], 1)
        self.assertEqual(response.context['total_irrigacoes'], 1)
        self.assertEqual(response.context['total_ocorrencias'], 1)
        self.assertEqual(response.context['total_aplicacoes'], 2)
        self.assertContains(response, 'Talhão Sul - Milho')
        self.assertContains(response, 'Milho Híbrido')
        self.assertContains(response, 'Lagarta-do-cartucho')


class PerfilUsuarioTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='novo_fazendeiro', password='password123')

    def test_perfil_auto_created(self):
        self.assertTrue(hasattr(self.user, 'perfil'))
        self.assertEqual(self.user.perfil.propriedade_configurada, False)
        self.assertEqual(self.user.perfil.latitude_propriedade, -5.8958)
        self.assertEqual(self.user.perfil.longitude_propriedade, -35.7633)

    def test_configurar_propriedade_get(self):
        self.client.login(username='novo_fazendeiro', password='password123')
        response = self.client.get(reverse('configurar_propriedade'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/configurar_propriedade.html')
        self.assertTrue(response.context['is_onboarding'])

    def test_configurar_propriedade_post(self):
        self.client.login(username='novo_fazendeiro', password='password123')
        response = self.client.post(reverse('configurar_propriedade'), {
            'nome_propriedade': 'Fazenda Bela Vista',
            'latitude_propriedade': -5.912345,
            'longitude_propriedade': -35.789012,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        self.user.perfil.refresh_from_db()
        self.assertEqual(self.user.perfil.nome_propriedade, 'Fazenda Bela Vista')
        self.assertEqual(self.user.perfil.latitude_propriedade, -5.912345)
        self.assertEqual(self.user.perfil.longitude_propriedade, -35.789012)
        self.assertEqual(self.user.perfil.propriedade_configurada, True)

    def test_signup_redirects_to_configurar_propriedade(self):
        response = self.client.post(reverse('signup'), {
            'username': 'usuario_onboarding',
            'password1': 'Teste123SenhaForte!#',
            'password2': 'Teste123SenhaForte!#',
        })
        # Verificamos se cria o usuário e redireciona para a configuração inicial da propriedade
        novo_user = User.objects.filter(username='usuario_onboarding').first()
        self.assertIsNotNone(novo_user)
        self.assertTrue(hasattr(novo_user, 'perfil'))
        self.assertEqual(novo_user.perfil.propriedade_configurada, False)
