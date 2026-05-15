from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, Movimentacao, Instituicao, Lote
from .forms import CadastroUsuarioForm, CadastroUsuarioForm, MaterialForm, MovimentacaoForm, InstituicaoForm
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import IntegrityError

# Tela apresentação do sistema
def home(request):
    if request.user.is_authenticated:
        return redirect('lista_materiais')
    
    return render(request, 'home.html')

# Tela de estoque
@login_required
def lista_materiais(request):
    instituicao= Instituicao.objects.filter(usuario=request.user).first()
    
    if not instituicao:
        return redirect('instituicao_config')
    
    materiais = Material.objects.filter(instituicao=instituicao, ativo = True)
    
    materiais_status = []
    hoje = date.today()

    for material in materiais:
        lotes = Lote.objects.filter(material=material, quantidade__gt=0).order_by('validade')
        alerta_vencimento = hoje + timedelta(days=30)
        
        estoque_atual = sum(l.quantidade for l in lotes)

        vencidos = any(lote.validade and lote.validade < hoje for lote in lotes)
        proximos_vencimento = any(lote.validade and hoje < lote.validade <= alerta_vencimento for lote in lotes)
        
        materiais_status.append({
            'material': material,
            'estoque': estoque_atual,
            'vencido': vencidos,
            'tem_movimentacoes': Movimentacao.objects.filter(material=material).exists(),
            'proximo_vencimento': proximos_vencimento,
            'lotes': Lote.objects.filter(material=material, quantidade__gt=0).order_by('validade')
        })
        
    return render(request, 'materiais/lista_materiais.html', {'materiais_status': materiais_status, 'hoje': hoje})

# Tela de detalhes de lotes dos materiais 
@login_required
def detalhes_lotes(request, id):
    material = get_object_or_404(Material, id=id, instituicao__usuario=request.user)
    lotes = Lote.objects.filter(material=material, quantidade__gt=0).order_by('validade')
    return render(request, 'materiais/detalhes_lotes.html', {'material': material, 'lotes': lotes, 'hoje': date.today()})

# Tela de cadastro material 
@login_required
def cadastrar_material(request):
    instituicao= Instituicao.objects.filter(usuario=request.user).first()
       
    if not instituicao:
        return redirect('instituicao_config')
    
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            try:
                material = form.save(commit=False)
                material.instituicao = instituicao
                material.save()
                return redirect('lista_materiais')
            except IntegrityError:
                form.add_error("nome", 'Este material já está cadastrado no seu estoque.')
    else:
        form = MaterialForm()

    contexto = {'form': form}
    return render(request, 'materiais/cadastro_material.html', contexto)

# Tela de edição
@login_required
def editar_material(request, id):
    material = get_object_or_404(Material, id=id, instituicao__usuario=request.user)

    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('lista_materiais')
    else:
        form = MaterialForm(instance=material)

    contexto = {'form': form}
    return render(request, 'materiais/cadastro_material.html', contexto)

# Tela de exclusão
@login_required
def excluir_material(request, id):
    material = get_object_or_404(Material, id=id, instituicao__usuario=request.user)

    if request.method == 'POST':
        if Movimentacao.objects.filter(material=material, ativo=True).exists():
            messages.error(request, 'Não é possível exluir um material que possui movimentações registradas.')
            return redirect('lista_materiais')
        
        material.delete()
        messages.success(request, 'Material excluído com sucesso!')
        return redirect('lista_materiais')

    contexto = {'material': material}
    return render(request, 'materiais/confirmar_exclusao.html', contexto)

# Tela de listagem de movimentações (consulta)
@login_required
def lista_movimentacoes(request):
    material_id = request.GET.get('material_id')
    
    movimentacoes = Movimentacao.objects.filter(material__instituicao__usuario=request.user)
    if material_id:
        movimentacoes = movimentacoes.filter(material_id=material_id)
    
    movimentacoes = movimentacoes.order_by('-data')
    
    return render(request, 'materiais/lista_movimentacoes.html', {'movimentacoes': movimentacoes})

# Tela cadastro de movimentações 
@login_required
def cadastro_movimentacoes(request, id):
    material = get_object_or_404(Material, id=id, instituicao__usuario=request.user)

    if request.method == 'POST':
        form = MovimentacaoForm(request.POST, material = material)
        
        quantidade = request.POST.get('quantidade')
        if quantidade and int(quantidade) <= 0:
            form.add_error('quantidade', 'A quantidade deve ser maior que zero.')
            
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.material = material
            
            try:
                from django.db import transaction
                with transaction.atomic():
                    if movimentacao.tipo == 'E':
                        Lote.objects.create(material=material, quantidade=movimentacao.quantidade, validade=form.cleaned_data.get('validade'))
                        movimentacao.save()

                    elif movimentacao.tipo == 'S':
                        lotes = Lote.objects.filter(material=material, quantidade__gt=0).order_by('data_entrada')
                        quantidade_saida = movimentacao.quantidade
                        
                        if material.estoque_atual < quantidade_saida:
                            raise ValidationError('Quantidade de saída maior que o estoque atual.')
                        
                        for lote in lotes:
                            if quantidade_saida <= 0: 
                                break
                            if lote.quantidade <= quantidade_saida:
                                quantidade_saida -= lote.quantidade
                                lote.delete()
                            else:
                                lote.quantidade -= quantidade_saida
                                lote.save()
                                quantidade_saida = 0
                        
                        movimentacao.save()
                        
                    if movimentacao.tipo == 'E':
                        messages.success(request, f"O item {material.nome} foi adicionado ao estoque.") 
                    else:
                        messages.success(request, 'Movimentação de saída registrada com sucesso')
                    
                    return redirect('lista_materiais')  
            
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = MovimentacaoForm(material = material)
        
    return render(request, 'materiais/form_movimentacao.html', {'form': form, 'material': material})
                
# Tela de visualização e geração de relatório 
@login_required
def relatorio_estoque(request):
    instituicao = Instituicao.objects.filter(usuario=request.user).first()
    materiais = Material.objects.filter(instituicao=instituicao, ativo = True)

    dados = []
    for material in materiais:
        dados.append({
            'nome' : material.nome,
            'categoria' : material.categoria,
            'estoque_atual' : material.estoque_atual
        })
    
    return render(request, 'materiais/relatorio_estoque.html', {'dados': dados}) 

# Cadastro de instituições (tela institucional)
@login_required
def instituicao_config(request):
    instituicao = Instituicao.objects.filter(usuario=request.user).first()

    if request.method == 'POST':
        form = InstituicaoForm(request.POST, instance=instituicao)
        if form.is_valid():
            try:
                obkj = form.save(commit=False)
                obkj.usuario = request.user
                obkj.full_clean()
                obkj.save() 
                
                messages.success(request, 'Informaçõs salvas com sucesso!')
                return redirect('lista_materiais')
            except ValidationError as e:
                form.add_error(None, e.message_dict.get('__all__', e.messages))
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = InstituicaoForm(instance=instituicao) 

    return render(request, 'materiais/instituicao.html', {'form': form})

# Tela de cadastro de usuários
def cadastro_usuario(request):
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            return redirect('instituicao_config')
    else:
        form = CadastroUsuarioForm()

    return render(request, 'cadastro_usuario.html', {'form': form})











