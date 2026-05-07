from datetime import date, timedelta
from .models import Lote

def notificacoes(request):
    hoje = date.today()

    vencidos_list = Lote.objects.filter(validade__lt=hoje)
    proximos_list = Lote.objects.filter(validade__gte=hoje, validade__lte=hoje + timedelta(days=30))

    return {
        'notificacoes': {
            'total': vencidos_list.count() + proximos_list.count(),
            'vencidos': vencidos_list,
            'proximos': proximos_list,
            'quantidade_vencidos': vencidos_list.count(),
            'quantidade_proximos': proximos_list.count(),
        }
    }
