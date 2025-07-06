from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse('adminlogin')

        allowed_paths = [
            login_url,
            '/static/',
        ]

        if not request.session.get('is_admin'):
            if not any(request.path.startswith(path) for path in allowed_paths):
                return redirect('adminlogin')

        return self.get_response(request)
