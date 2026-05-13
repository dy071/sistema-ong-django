from datetime import date, timedelta
from .models import Instituicao, Lote

def notificacoes(request):
    if not request.user.is_authenticated:
        return {}
    
    instituicao = Instituicao.objects.filter(usuario=request.user).first()
    if not instituicao:
        return {
            'notificacoes': {
                'total': 0,
                'vencidos': [],
                'proximos': []
            }
        }
    
    hoje = date.today()

    vencidos_list = Lote.objects.filter(material__instituicao__usuario=request.user, validade__lt=hoje)
    proximos_list = Lote.objects.filter(material__instituicao__usuario=request.user, validade__gte=hoje, validade__lte=hoje + timedelta(days=30))

    return {
        'notificacoes': {
            'total': vencidos_list.count() + proximos_list.count(),
            'vencidos': vencidos_list,
            'proximos': proximos_list,
            'quantidade_vencidos': vencidos_list.count(),
            'quantidade_proximos': proximos_list.count(),
        }
    }
