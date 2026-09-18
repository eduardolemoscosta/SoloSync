from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Propriedade, Talhao, Plantio, Manejo, Irrigacao, Ocorrencia, PerfilUsuario
from datetime import date


class PropriedadeHierarchyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='fazendeiro_joao', password='password123')
        self.propriedade1 = Propriedade.objects.create(
            usuario=self.user,
            nome='Fazenda Santa Luzia',
            cidade='Petrolina',
            estado='PE',
            latitude_sede=-9.3891,
            longitude_sede=-40.5027,
            area_total_ha=150.00
        )
        self.propriedade2 = Propriedade.objects.create(
            usuario=self.user,
            nome='Sítio Boa Vista',
            cidade='Juazeiro',
            estado='BA',
            latitude_sede=-9.4167,
            longitude_sede=-40.5000,
            area_total_ha=45.50
        )
        self.talhao1 = Talhao.objects.create(
            propriedade=self.propriedade1,
            nome='Talhão 01 - Manga',
            area_m2=20000.0,
            tipo_solo='Arenoso',
            coordenadas_json={
                "type": "Polygon",
                "coordinates": [[[-40.50, -9.38], [-40.50, -9.39], [-40.51, -9.39], [-40.51, -9.38], [-40.50, -9.38]]]
            }
        )
        self.talhao2 = Talhao.objects.create(
            propriedade=self.propriedade1,
            nome='Talhão 02 - Uva',
            area_m2=30000.0,
            tipo_solo='Argiloso',
            coordenadas_json={
                "type": "Polygon",
                "coordinates": [[[-40.51, -9.38], [-40.51, -9.39], [-40.52, -9.39], [-40.52, -9.38], [-40.51, -9.38]]]
            }
        )

    def test_propriedade_str_and_relation(self):
        self.assertEqual(str(self.propriedade1), 'Fazenda Santa Luzia (fazendeiro_joao)')
        self.assertEqual(self.propriedade1.talhoes.count(), 2)
        self.assertEqual(self.propriedade2.talhoes.count(), 0)

    def test_talhao_str_and_properties(self):
        self.assertEqual(str(self.talhao1), 'Talhão 01 - Manga - Fazenda Santa Luzia')
        self.assertEqual(self.talhao1.usuario, self.user)
        self.assertIsNotNone(self.talhao1.coordenadas)

    def test_propriedade_crud_views(self):
        self.client.login(username='fazendeiro_joao', password='password123')
        res = self.client.get(reverse('propriedade_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Fazenda Santa Luzia')
        self.assertContains(res, 'Sítio Boa Vista')

        res = self.client.post(reverse('propriedade_create'), {
            'nome': 'Chácara Recanto Verde',
            'cidade': 'Casa Nova',
            'estado': 'BA',
            'latitude_sede': -9.16,
            'longitude_sede': -40.97,
            'area_total_ha': 12.0
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Propriedade.objects.filter(nome='Chácara Recanto Verde', usuario=self.user).exists())

        chacara = Propriedade.objects.get(nome='Chácara Recanto Verde')
        res = self.client.post(reverse('propriedade_update', kwargs={'pk': chacara.pk}), {
            'nome': 'Chácara Recanto Verde Atualizada',
            'cidade': 'Casa Nova',
            'estado': 'BA',
            'latitude_sede': -9.16,
            'longitude_sede': -40.97,
            'area_total_ha': 15.0
        })
        self.assertEqual(res.status_code, 302)
        chacara.refresh_from_db()
        self.assertEqual(chacara.nome, 'Chácara Recanto Verde Atualizada')
        self.assertEqual(chacara.area_total_ha, 15.0)

        res = self.client.post(reverse('propriedade_delete', kwargs={'pk': chacara.pk}))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Propriedade.objects.filter(pk=chacara.pk).exists())

    def test_talhao_create_in_propriedade(self):
        self.client.login(username='fazendeiro_joao', password='password123')
        res = self.client.post(reverse('talhao_create'), {
            'propriedade': self.propriedade2.id,
            'nome': 'Talhão B1',
            'area_m2': 15000.0,
            'tipo_solo': 'Misto',
            'coordenadas_json': '{"type": "Polygon", "coordinates": []}'
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Talhao.objects.filter(nome='Talhão B1', propriedade=self.propriedade2).exists())

    def test_unir_talhoes_mesma_propriedade(self):
        self.client.login(username='fazendeiro_joao', password='password123')
        res = self.client.post(reverse('talhoes_unir'), {
            'talhoes_ids': [self.talhao1.id, self.talhao2.id],
            'novo_nome': 'Talhão Unificado 01+02',
            'tipo_solo': 'Misto'
        })
        self.assertEqual(res.status_code, 302)
        unificado = Talhao.objects.filter(nome='Talhão Unificado 01+02').first()
        self.assertIsNotNone(unificado)
        self.assertEqual(unificado.propriedade, self.propriedade1)
        self.assertEqual(unificado.area_m2, 50000.0)


class TalhaoDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='produtor1', password='password123')
        self.propriedade = Propriedade.objects.create(
            usuario=self.user,
            nome='Fazenda Modelo',
            latitude_sede=-5.8958,
            longitude_sede=-35.7633,
            area_total_ha=50.0
        )
        self.talhao = Talhao.objects.create(
            propriedade=self.propriedade,
            nome='Talhão Sul - Milho',
            area_m2=25000.0,
            tipo_solo='Argiloso',
            coordenadas_json={
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
        self.assertContains(response, 'Fazenda Modelo')

    def test_signup_redirects_to_propriedade_create(self):
        response = self.client.post(reverse('signup'), {
            'username': 'usuario_onboarding',
            'password1': 'Teste123SenhaForte!#',
            'password2': 'Teste123SenhaForte!#',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('propriedade_create'))
        novo_user = User.objects.filter(username='usuario_onboarding').first()
        self.assertIsNotNone(novo_user)

