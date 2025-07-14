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
from django.utils.timezone import localdate, make_aware, localtime

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

@login_required(login_url='login')
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
        
        car = Car.objects.create(
            user=request.user,
            brand=brand,
            model=model,
            color=color,
            license_plate=license_plate,
            image=uploaded_image,
        )
        
        reservation.car = car
        reservation.save()
        
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
    
    next_page = request.GET.get('next', 'history')
    return redirect(next_page)

def history_view(request):
    now = timezone.now()
    reservations = Reservation.objects.filter(user=request.user, end_time__gte=now).order_by('-start_time').select_related('car')
    return render(request, 'history.html', {
        'reservations': reservations})

def guide_view(request):
    return render(request, 'guide.html')

# ADMIN SECTION
def adminlogin_view(request):
    return render(request, 'adminlogin.html')

def adminhome_view(request):
    return render(request, 'adminhome.html')

def adminreservation_view(request):
    return render(request, 'adminreservation.html')

def adminmonitoring_view(request):
    return render(request, 'adminmonitoring.html')
  
def spots_dynamic_status_json(request):
    selected_date_str = request.GET.get('date')
    if not selected_date_str:
        return JsonResponse({'error': 'No date provided'}, status=400)

    selected_date = parse_date(selected_date_str)
    if not selected_date:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    today = localdate()  # Hari ini (bukan timezone.now().date())

    spots = []
    for spot in Spot.objects.all():
        # Cek apakah ada reservasi pada tanggal yang diminta
        reserved_on_date = Reservation.objects.filter(
            spot=spot,
            start_time__date=selected_date
        ).exists()

        # Jika tanggal yang dipilih adalah hari ini, sensor aktif
        if selected_date == today:
            if spot.status == "occupied":
                status = "occupied"
            elif reserved_on_date:
                status = "reserved"
            else:
                status = "available"
        else:
            # Untuk tanggal lain, hanya berdasarkan reservasi
            status = "reserved" if reserved_on_date else "available"

        spots.append({
            "spot_number": spot.spot_number,
            "status": status
        })

    return JsonResponse(spots, safe=False)
"""
def reserved_hours_view(request):
    spot_number = request.GET.get('spot')
    date_str = request.GEt.get('date')

    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    reservations = Reservation.objects.filter(
        spot__spot_number=spot_number,
        start_time__date=date_obj
    )
    
    reserved_hours = []
    for r in reservations:
        start_hour = r.start_time.hour
        end_hour = r.end_time.hour
        reserved_hours.extend(list(range(start_hour, end_hour)))

    return JsonResponse({'reserved_hours': sorted(set(reserved_hours))})
"""
def get_reserved_times(start, end):
    blocked = []
    current = start
    while current <= end:
        blocked.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
    return blocked

def reserved_intervals_view(request):
    from django.utils.timezone import localtime

    date_str = request.GET.get('date')
    spot_id = request.GET.get('spot')

    if not date_str or not spot_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    from .models import Spot  # adjust if needed
    try:
        spot = Spot.objects.get(spot_number=spot_id)
    except Spot.DoesNotExist:
        return JsonResponse({'error': 'Spot not found'}, status=404)

    # Use naive date for filtering
    target_date = parse_date(date_str)

    reservations = Reservation.objects.filter(
        spot=spot,
        start_time__date=target_date
    )

    all_blocked = []
    for r in reservations:
        start = localtime(r.start_time)  # Convert to local time
        end = localtime(r.end_time)
        blocked = get_reserved_times(start, end)
        all_blocked.extend(blocked)

    return JsonResponse({'reserved_times': all_blocked})

def extend_reservation(request, reservation_id):
    if request.method == 'POST':
        reservation = Reservation.objects.get(id=reservation_id)
        new_end_time = request.POST.get('new_end_time')

        reservation.end_time = new_end_time
        reservation.save()

        return redirect('history')