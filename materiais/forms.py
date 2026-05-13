from django import forms
from .models import Material, Movimentacao, Instituicao
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from datetime import date
import re

# Formulário para cadastro de usuários
class CadastroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirme sua senha', widget=forms.PasswordInput(attrs={'class': 'form-control'})) 

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Usuário',
            'email': 'E-mail',
        }
        help_texts = {
            'username': 'O nome de usuário deve conter apenas letras, números e caracteres especiais.',
            'email': 'Digite um endereço de e-mail válido.',
        }   

class InstituicaoForm(forms.ModelForm):
    class Meta:
        model = Instituicao
        fields = ['nome', 'documento', 'endereco', 'telefone', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'documento': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', nome):
            raise forms.ValidationError('O nome da instituição deve conter apenas letras e espaços.')
        if len(nome) < 3:
            raise forms.ValidationError('O nome da instituição deve conter pelo menos 3 caracteres.')
        return nome
        
    def clean_documento(self):
        documento = self.cleaned_data.get('documento')
        
        if not documento:
            raise forms.ValidationError('O CPF/CNPJ é obrigatório.')
        
        numeros = re.sub(r'\D', '', documento)
        
        if len(numeros) == 11:
            padrao_cpf = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
            if not re.match(padrao_cpf, documento):
                raise forms.ValidationError('O CPF deve estar no formato XXX.XXX.XXX-XX.')
            return documento
        elif len(numeros) == 14:
            padrao_cnpj = r'^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$'
            if not re.match(padrao_cnpj, documento):
                raise forms.ValidationError('O CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX.')
            return documento
        
        raise forms.ValidationError('O CPF/CNPJ deve conter 11 ou 14 caracteres.')
    
    def clean_endereco(self):
        endereco = self.cleaned_data.get('endereco')
        if len(endereco) < 5:
            raise forms.ValidationError('O endereço deve conter pelo menos 5 caracteres.')
        return endereco
        
    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if not re.match(r'^\(?\d{2}\)?[\s-]?\d{4,5}-?\d{4}$', telefone):
            raise forms.ValidationError('O telefone deve estar no formato (XX) XXXX-XXXX ou (XX) XXXXX-XXXX.')
        if telefone:
            telefone_numeros = re.sub(r'\D', '', telefone)
            if len(telefone_numeros) < 10 or len(telefone_numeros) > 11:
                raise forms.ValidationError('Telefone inválido.')
        return telefone
    
    email = forms.EmailField(error_messages={'invalid': 'Digite um endereço de e-mail válido.'})

# Formulário para cadastro e edição de materiais
class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['nome', 'categoria', 'estado', 'observacoes']
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MovimentacaoForm(forms.ModelForm):
    validade = forms.DateField(
        required=False, 
        input_formats= ['%d/%m/%Y'],
        label='Validade', 
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control','placeholder': 'dd/mm/aaaa'}),
        help_text='Obrigatório para materiais da categoria ALIMENTOS.')
    def __init__(self, *args, **kwargs):
        self.material = kwargs.pop('material', None)
        super().__init__(*args, **kwargs)
        
    class Meta:
        model = Movimentacao
        fields = ['tipo', 'quantidade', 'validade']

    # Campo validade requerido apenas para materiais de alimentação
    def clean(self):
        cleaned_data = super().clean()
        validade = cleaned_data.get('validade')
        tipo = self.cleaned_data.get('tipo')

        if (self.material and self.material.categoria == 'ALIMENTOS' and not validade and tipo == 'E'):
            raise forms.ValidationError("Materiais de alimentação devem ter uma data de validade.")
        if validade and validade < date.today():
            raise forms.ValidationError("A data de validade não pode ser menor que a data atual.")
        
        return self.cleaned_data
