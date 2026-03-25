from django.shortcuts import render


def index(request):
    pass


def mapa(request):
    return render(request, 'core/mapa.html')


def order_panel(request):
    return render(request, 'core/order_panel.html')
