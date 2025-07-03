from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', home_view, name='home'),
    path('home/', home_view, name='home'),
    path('reservation/', reservation_view, name='reservation'),
    path('reservation/<int:reservation_id>/', reservation_details_view, name='reservationdetails'),
    path('account/', account_view, name='account'),
    path('update-account/', update_account_view, name='update_account'),
    path('reservation/<int:reservation_id>/delete/', delete_reservation, name='delete_reservation'),
    path('history/', history_view, name='history'),
    path('guide/', guide_view, name='guide' ),
    path('status/', status_view, name='status'),
  
    path('api/spots-dynamic-status/', spots_dynamic_status_json, name='spots_dynamic_status_json'),
    path('api/reserved-intervals/', reserved_intervals_view, name='reserved_intervals'),
    # admin
    path('adminlogin/', adminlogin_view, name='adminlogin'),
    path('adminhome/', adminhome_view, name='adminhome'),
    path('adminreservation/', adminreservation_view, name='adminreservation'),
    path('adminmonitoring/', adminmonitoring_view, name='adminmonitoring'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)