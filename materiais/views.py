from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, Movimentacao, Instituicao, Lote
from .forms import CadastroUsuarioForm, CadastroUsuarioForm, MaterialForm, MovimentacaoForm, InstituicaoForm
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

# Tela apresentação do sistema
def home(request):
    if request.user.is_authenticated:
        return redirect('lista_materiais')
    
    return render(request, 'home.html')

# Tela de estoque
@login_required
def lista_materiais(request):
    if not Instituicao.objects.exists():
        return redirect('instituicao_config')

    materiais = Material.objects.filter(ativo=True)
    materiais_status = []

    for material in materiais:
        lotes = Lote.objects.filter(material=material)

        estoque_atual = sum(l.quantidade for l in lotes)

        vencidos = any(lote.validade and lote.validade <= date.today() for lote in lotes)
        proximos_vencimento = any(lote.validade and lote.validade <= date.today() + timedelta(days=30) for lote in lotes) 

        materiais_status.append({
            'material': material,
            'estoque': estoque_atual,
            'vencido': vencidos,
            'proximo_vencimento': proximos_vencimento
        })
    
    return render(request, 'materiais/lista_materiais.html', {'materiais_status': materiais_status})

# Tela de cadastro
@login_required
def cadastrar_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_materiais')
    else:
        form = MaterialForm()

    contexto = {'form': form}
    return render(request, 'materiais/cadastro_material.html', contexto)

# Tela de edição
@login_required
def editar_material(request, id):
    material = get_object_or_404(Material, id=id)

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
    material = get_object_or_404(Material, id=id)

    if request.method == 'POST':
        if material.movimentacoes.exists():
            messages.error(request, 'Não é possível exluir um material que possui movimentações registradas.')
            return redirect('lista_materiais')
        
        material.ativo = False
        material.save()
        messages.success(request, 'Material excluído com sucesso!')
        return redirect('lista_materiais')

    contexto = {'material': material}
    return render(request, 'materiais/confirmar_exclusao.html', contexto)

# Tela de listagem de movimentações (consulta)
@login_required
def lista_movimentacoes(request):
    material_id = request.GET.get('material')

    if material_id:
        movimentacoes = Movimentacao.objects.filter(material_id=material_id).order_by('-data')
    else:
        movimentacoes = Movimentacao.objects.all().order_by('-data')
    
    return render(request, 'materiais/lista_movimentacoes.html', {'movimentacoes': movimentacoes})

# Tela cadastro de movimentações 
@login_required
def cadastro_movimentacoes(request, id):
    material = get_object_or_404(Material, id=id)

    if request.method == 'POST':
        form = MovimentacaoForm(request.POST, material = material)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.material = material

            try:
                if movimentacao.tipo == 'E':
                    Lote.objects.create(material=material, quantidade=movimentacao.quantidade, validade=form.cleaned_data.get('validade'))
                    messages.warning(request, f"O item {material.nome} foi adicionado ao estoque.")

                elif movimentacao.tipo == 'S':
                    if any(l.validade and l.validade < date.today() for l in Lote.objects.filter(material=material)):
                        messages.warning(request, f"Itens vencidos no estoque: {material.nome}. Priorize a saída desses itens para evitar desperdícios.")

                    lotes = Lote.objects.filter(material=material, quantidade__gt=0).order_by('data_entrada')
                    quantidade_saida = movimentacao.quantidade

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

                    if quantidade_saida > 0:
                        raise ValidationError('Não há lotes suficientes para atender a quantidade de saída solicitada.')

                lotes_restantes = Lote.objects.filter(material=material)
                for lote in lotes_restantes:
                    if any(l.validade and l.validade < date.today() for l in lotes_restantes):
                        messages.warning(request, f"Itens vencidos no estoque: {material.nome}. Priorize a saída desses itens para evitar desperdícios.")

                movimentacao.save()

                messages.success(request, 'Movimentação registrada com sucesso')
                return redirect('lista_materiais')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = MovimentacaoForm(material=material)

    return render(request, 'materiais/form_movimentacao.html', {'form': form, 'material': material})

# Tela de visualização e geração de relatório 
@login_required
def relatorio_estoque(request):
    materiais = Material.objects.all()

    dados = []
    for material in materiais:
        dados.append({
            'nome' : material.nome,
            'categoria' : material.categoria,
            'estoque_atual' : material.estoque_atual()
        })
    
    return render(request, 'materiais/relatorio_estoque.html', {'dados': dados}) 

# Cadastro de instituições (tela institucional)
@login_required
def instituicao_config(request):
    instiuicao = Instituicao.objects.first() 

    if request.method == 'POST':
        form = InstituicaoForm(request.POST, instance=instiuicao)
        if form.is_valid():
            try:
                obkj = form.save(commit=False)
                obkj.full_clean()
                obkj.save() 
                
                messages.success(request, 'Informaçõs salvas com sucesso!')
                return redirect('lista_materiais')
            except ValidationError as e:
                form.add_error(None, e.message_dict.get('__all__', e.messages))
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = InstituicaoForm(instance=instiuicao) 

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
