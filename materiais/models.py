from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils import timezone

# Modelo para materiais
class Material(models.Model):
    # Definindo opções fixas 
    CATEGORIAS_CHOICES = [
        ('ALIMENTOS', 'Alimentos não perecíveis'),
        ('VESTUARIO', 'Roupas e Calçados'),
        ('HIGIENE', 'Produtos de Higiene Pessoal'),
        ('EQUIPAMENTOS', 'Equipamentos (Cadeiras de rodas, muletas, etc)'),
        ('OUTROS', 'Outros'),
    ]

    ESTADO_CHOICES = [
        ('NOVO', 'Novo'),
        ('BOM', 'Usado (Em bom estado)'),
        ('REPARO', 'Usado (Precisa de pequenos reparos)'),
    ]

    # Colunas da tabela
    nome = models.CharField(max_length=150, verbose_name="Nome do Material")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_CHOICES, verbose_name="Categoria")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, verbose_name="Estado de Conservação")
    
    # Textos longos para detalhes e histórico
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações Adicionais")
    
    # Preenche a data e hora automaticamente no momento do cadastro
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")

    # Como o material vai se "apresentar" quando listado
    def __str__(self):
        return self.nome
    
    # Atualização automática da quantidade no estoque 
    def estoque_atual(self):
        entradas = self.movimentacoes.filter(tipo='E', ativo=True).aggregate(total=models.Sum('quantidade'))['total'] or 0
        saidas = self.movimentacoes.filter(tipo='S', ativo=True).aggregate(total=models.Sum('quantidade'))['total'] or 0
        return entradas - saidas

# Modelo para movimentações
class Movimentacao(models.Model):
    TIPO_MOVIMENTACAO = [
        ('E', 'Entrada'),
        ('S', 'Saída'),
    ]

    material = models.ForeignKey('Material', on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=1, choices=TIPO_MOVIMENTACAO)
    quantidade = models.PositiveBigIntegerField()
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.material} - {self.get_tipo_display()} - {self.quantidade}"
    
    # Regra para impedir a quantidade de saída maior que a quantidade contida no Estoque  
    def clean(self):
        if not self.material_id:
            return
        
        # Regra para que a movimentação cancelada não seja alterada garantindo o histórico no sistema
        if self.pk:
            movimentacao_antiga = Movimentacao.objects.filter(pk=self.pk).first()
            if movimentacao_antiga and not movimentacao_antiga.ativo:
                raise ValidationError('Movimentações canceladas não podem ser editadas.')
            
        # Garante que o campo de quantidade seja maior que 0     
        if self.quantidade <= 0:
            raise ValidationError('A quantidade deve ser maior que zero.')
        
        # Atualização dinâmica do estoque 
        if self.tipo == 'S':
            estoque_atual = self.material.estoque_atual()
            if self.pk:
                movimentacao_antiga = Movimentacao.objects.filter(pk=self.pk).first()
                if movimentacao_antiga.tipo == 'S':
                    estoque_atual += movimentacao_antiga.quantidade
                else:
                    estoque_atual -= movimentacao_antiga.quantidade

            # Validação para que a quantidade de saída não seja maior que a quantidade do estoque 
            if self.quantidade > estoque_atual:
                raise ValidationError('Quantidade de saída maior que o estoque disponível.') 

    # Metódo para que a função clean() seja chamada automaticamente
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # Metódo para cancelamento de movimentações 
    def cancelar(self):
        if not self.ativo:
            raise ValidationError('Esta movimentação já está cancelada.')
        
        if self.tipo == 'E':
            estoque_atual = self.material.estoque_atual()
            if estoque_atual - self.quantidade < 0:
                raise ValidationError('Não é possível cancelar esta entrada, pois existem saídas dependentes.')
        
        self.ativo = False
        self.data_cancelamento = timezone.now()
        self.save()
