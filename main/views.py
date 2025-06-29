from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import CustomUser, Spot, Reservation, Car
from django.contrib import messages
import logging
from datetime import datetime, time, date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date

logger = logging.getLogger(__name__)

# Create your views here.
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        phone_number = request.POST['phone_number']

        errors = {}

        if CustomUser.objects.filter(username=username).exists():
            errors['username'] = "* Username is already taken."

        if CustomUser.objects.filter(email=email).exists():
            errors['email'] = "* Email is already registered."

        if password != confirm_password:
            errors['password'] = "* Passwords do not match."

        if errors:
            return render(request, 'register.html', {
                'errors': errors,
                'input': request.POST
            })
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number
        )
        login(request, user)
        return redirect('login')
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            logger.debug(f"User {user.username} logged in successfully")
            return redirect('home')
        else:
            return render(request, 'login.html', {
                'error': "* Invalid username or password.",
                'input': request.POST
            })
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def home_view(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def reservation_view(request):
    today = date.today()
    two_weeks = today + timedelta(days=14)
    
    if request.method == 'POST':
        print("POST request received")
        date_str = request.POST.get('date')          # from your datepicker
        start_hour = request.POST.get('start_time')  # from time select
        end_hour = request.POST.get('end_time')
        spot_number = request.POST.get('slot')
        
        print("Raw POST data:", request.POST)
        
        if not (date_str and start_hour and end_hour and spot_number):
            # Handle missing form data here (maybe send an error)
            return render(request, 'reservation.html', {'error': 'Please fill all fields'})

        # Convert date to "YYYY-MM-DD"
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")

        # Combine date and time
        start_datetime = datetime.strptime(f"{formatted_date} {start_hour}:00", "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(f"{formatted_date} {end_hour}:00", "%Y-%m-%d %H:%M:%S")
        print(start_datetime)
        print(end_datetime)

        # Get Spot object
        try:
            spot = Spot.objects.get(spot_number=spot_number)
        except Spot.DoesNotExist:
            return render(request, 'reservation.html', {'error': 'Invalid parking slot selected'})
        
        # Create and save reservation
        reservation = Reservation.objects.create(
            user=request.user,
            spot=spot,
            start_time=start_datetime,
            end_time=end_datetime,
        )

        # Redirect or return success
        return redirect('reservationdetails', reservation_id=reservation.id)  # Replace with your success URL or render success message

    # GET request fallback
    return render(request, 'reservation.html', {
        'today': today.strftime('%Y-%m-%d'),
        'two_weeks': two_weeks.strftime('%Y-%m-%d'),
    })

latest_data = {"distance": "Belum ada data"}

def status_view(request):
    spots = Spot.objects.all()
    return render(request, 'status.html', {"spots": spots})

def reservation_details_view(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id)
    except Reservation.DoesNotExist:
        return render(request, 'reservation_details.html', {'error': 'Reservation not found'})
    
    if request.method == 'POST':
        brand = request.POST.get('dropdown1')
        model = request.POST.get('dropdown2')
        color = request.POST.get('color')
        plate1 = request.POST.get('plate1')
        plate2 = request.POST.get('plate2')
        plate3 = request.POST.get('plate3')
        uploaded_image = request.FILES.get('imageUpload')
        
        license_plate = f"{plate1} {plate2} {plate3.strip().upper()}"

        print("reservation details data: ", request.POST, request.FILES)
        
        Car.objects.create(
            user=request.user,
            brand=brand,
            model=model,
            color=color,
            license_plate=license_plate,
            image=uploaded_image,
        )
        return redirect('account')

    return render(request, 'reservation_details.html', {'reservation': reservation})

def account_view(request):
    return render(request, 'account.html')

def update_account_view(request):
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_number = request.POST.get('phone_number')

        errors = {}

        if CustomUser.objects.filter(username=username).exclude(id=user.id).exists():
            errors['username'] = "* Username is already taken."

        if password and password != confirm_password:
            errors['password'] = "* Passwords do not match."

        if errors:
            return render(request, 'account.html', {
                'errors': errors,
                'input': request.POST
            })

        user.username = username
        user.phone_number = phone_number

        if password:
            user.set_password(password)
            # Perlu login ulang jika password diganti
            user.save()
            login(request, user)
        else:
            user.save()

        messages.success(request, "Akun berhasil diperbarui.")
        return redirect('account')  # Ganti sesuai halaman utama akun kamu

    return redirect('account')

def delete_reservation(request, reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    reservation.delete()
    return redirect('reservation')

def history_view(request):
    return render(request, 'history.html')

def guide_view(request):
    return render(request, 'guide.html')


def spots_dynamic_status_json(request):
    
    selected_date_str = request.GET.get('date')
    if not selected_date_str:
        return JsonResponse({'error': 'No date provided'}, status=400)
    selected_date = parse_date(selected_date_str)
    if not selected_date:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    spots = []
    now = timezone.now().replace(second=0, microsecond=0)

    for spot in Spot.objects.all():
        # Cek reservasi hari ini
        reserved_on_day = Reservation.objects.filter(
            spot=spot,
            start_time__date=selected_date
        ).exists()

        # Sensor status dari field Spot.status
        sensor_occupied = spot.status == "occupied"

        if sensor_occupied:
            status = "occupied"
        elif reserved_on_day:
            status = "reserved"
        else:
            status = "available"

        spots.append({"spot_number": spot.spot_number, "status": status})

    return JsonResponse(spots, safe=False)