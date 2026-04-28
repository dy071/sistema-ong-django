from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, Movimentacao
from .forms import MaterialForm, MovimentacaoForm
from django.contrib import messages
from django.core.exceptions import ValidationError

# Tela de estoque
def lista_materiais(request):
    materiais_no_banco = Material.objects.all()
    contexto = {'materiais': materiais_no_banco}
    return render(request, 'materiais/lista_materiais.html', contexto)

# Tela de cadastro
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
def excluir_material(request, id):
    material = get_object_or_404(Material, id=id)

    if request.method == 'POST':
        if material.movimentacoes.exists():
            messages.error(request, 'Não é possível exluir um material que possui movimentações registradas.')
            return redirect('lista_materiais')
        
        material.delete() # O comando que apaga do banco de dados
        messages.success(request, 'Material excluído com sucesso!')
        return redirect('lista_materiais')

    contexto = {'material': material}
    return render(request, 'materiais/confirmar_exclusao.html', contexto)

# Tela de listagem de movimentações (consulta)
def lista_movimentacoes(request):
    movimentacoes = Movimentacao.objects.all().order_by('-data')
    return render(request, 'materiais/lista_movimentacoes.html', {'movimentacoes': movimentacoes})

# Tela cadastro de movimentações 
def cadastro_movimentacoes(request, id):
    material = get_object_or_404(Material, id=id)

    if request.method == 'POST':
        form = MovimentacaoForm(request.POST, material = material)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.material = material

            try:
                movimentacao.full_clean() 
                movimentacao.save()
                messages.success(request, 'Movimentação registrada com sucesso')
                return redirect('lista_materiais')
            except ValidationError as e:
                form.add_error(None, e.message_dict.get('__all__', e.messages))
    else:
        form = MovimentacaoForm(material=material)

    return render(request, 'materiais/form_movimentacao.html', {'form': form, 'material': material})
