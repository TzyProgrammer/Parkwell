from django.urls import path
from .views import register_view, login_view, logout_view, home_view, reservation_view, reservation_details_view, account_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', home_view, name='home'),
    path('home/', home_view, name='home'),
    path('reservation/', reservation_view, name='reservation'),
    path('reservation/<int:reservation_id>/', reservation_details_view, name='reservationdetails'),
    path('account/', account_view, name='account'),
]
