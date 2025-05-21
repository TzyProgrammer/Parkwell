from django.urls import path
from .views import register_view, login_view, logout_view, home_view, reservation_view, mqtt_data_view, status_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', home_view, name='home'),
    path('home/', home_view, name='home'),
    path('reservation/', reservation_view, name='reservation'),
    path('mqtt-data/', mqtt_data_view, name='mqtt-data'),
    path('status/', status_view, name='status')
]
