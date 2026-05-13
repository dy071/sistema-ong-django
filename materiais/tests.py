from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Instituicao, Material, Movimentacao, Lote


class SGEDTestCase(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username='usuario1',
            password='123456'
        )

        self.user2 = User.objects.create_user(
            username='usuario2',
            password='123456'
        )

        self.instituicao = Instituicao.objects.create(
            usuario=self.user,
            nome='ONG Teste',
            documento='123.456.789-00',
            endereco='Rua Teste',
            telefone='11999999999',
            email='teste@email.com'
        )

        self.instituicao2 = Instituicao.objects.create(
            usuario=self.user2,
            nome='ONG Teste 2',
            documento='987.654.321-00',
            endereco='Rua Teste 2',
            telefone='11888888888',
            email='teste2@email.com'
        )

        self.material = Material.objects.create(
            instituicao=self.instituicao,
            nome='Arroz',
            categoria='ALIMENTOS',
            estado='NOVO'
        )

    def test_criacao_material(self):

        self.assertEqual(self.material.nome, 'Arroz')
        self.assertTrue(self.material.ativo)

    def test_material_vinculado_usuario(self):

        self.assertEqual(
            self.material.instituicao.usuario,
            self.user
        )

    def test_criacao_lote(self):

        lote = Lote.objects.create(
            material=self.material,
            quantidade=20,
            validade=date.today() + timedelta(days=30)
        )

        self.assertEqual(lote.quantidade, 20)

    def test_estoque_atual(self):

        Lote.objects.create(
            material=self.material,
            quantidade=10,
            validade=date.today() + timedelta(days=30)
        )

        Lote.objects.create(
            material=self.material,
            quantidade=5,
            validade=date.today() + timedelta(days=60)
        )

        self.assertEqual(self.material.estoque_atual, 15)

    def test_movimentacao_entrada(self):

        movimentacao = Movimentacao.objects.create(
            material=self.material,
            tipo='E',
            quantidade=10
        )

        self.assertEqual(movimentacao.quantidade, 10)

    def test_quantidade_negativa(self):

        movimentacao = Movimentacao(
            material=self.material,
            tipo='E',
            quantidade=-5
        )

        with self.assertRaises(ValidationError):
            movimentacao.full_clean()

    def test_quantidade_zero(self):

        movimentacao = Movimentacao(
            material=self.material,
            tipo='E',
            quantidade=0
        )

        with self.assertRaises(ValidationError):
            movimentacao.full_clean()

    def test_lote_vencido(self):

        lote = Lote.objects.create(
            material=self.material,
            quantidade=10,
            validade=date.today() - timedelta(days=1)
        )

        self.assertTrue(lote.validade < date.today())

    def test_lote_proximo_vencimento(self):

        lote = Lote.objects.create(
            material=self.material,
            quantidade=10,
            validade=date.today() + timedelta(days=10)
        )

        self.assertTrue(
            lote.validade <= date.today() + timedelta(days=30)
        )

    def test_separacao_usuarios(self):

        material2 = Material.objects.create(
            instituicao=self.instituicao2,
            nome='Feijão',
            categoria='ALIMENTOS',
            estado='NOVO'
        )

        materiais_user1 = Material.objects.filter(
            instituicao__usuario=self.user
        )

        self.assertNotIn(material2, materiais_user1)

    def test_exclusao_logica(self):

        self.material.ativo = False
        self.material.save()

        materiais_ativos = Material.objects.filter(ativo=True)

        self.assertNotIn(self.material, materiais_ativos)

    def test_login_usuario(self):

        login = self.client.login(
            username='usuario1',
            password='123456'
        )

        self.assertTrue(login)

    def test_acesso_estoque_logado(self):

        self.client.login(
            username='usuario1',
            password='123456'
        )

        response = self.client.get('/materiais/')

        self.assertEqual(response.status_code, 200)

    def test_redirecionamento_sem_login(self):

        response = self.client.get('/materiais/')

        self.assertEqual(response.status_code, 302)