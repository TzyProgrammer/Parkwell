from django.shortcuts import render

def register_view(request):
    return render(request, 'main/register.html')
