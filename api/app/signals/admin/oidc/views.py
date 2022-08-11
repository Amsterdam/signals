from django.shortcuts import render

def login_failure(request):
    return render(request, 'admin/oidc/login_failure.html')
