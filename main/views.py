from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import CustomUser, Spot, Reservation, Car
from django.contrib import messages
import logging
from datetime import datetime, time, date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import localdate, make_aware, localtime
from django.views.decorators.http import require_POST
import json

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
        print("Raw POST data:", request.POST)

        # Ambil data dari form
        date_str = request.POST.get('date')
        start_hour = request.POST.get('start_time')
        end_hour = request.POST.get('end_time')
        spot_number = request.POST.get('slot')  # name="slot" di HTML

        # Validasi form kosong
        if not all([date_str, start_hour, end_hour, spot_number]):
            return render(request, 'reservation.html', {
                'error': 'Please fill all fields',
                'today': today.strftime('%Y-%m-%d'),
                'two_weeks': two_weeks.strftime('%Y-%m-%d')
            })

        # Validasi tipe spot_number
        try:
            spot_number = int(spot_number)
        except ValueError:
            messages.error(request, "Invalid slot selected.")
            return redirect('reservation')

        # Ambil objek Spot
        try:
            spot = Spot.objects.get(spot_number=spot_number)
        except Spot.DoesNotExist:
            messages.error(request, "Selected slot not found.")
            return redirect('reservation')

        # Cek apakah spot dinonaktifkan
        if spot.is_disabled:
            return render(request, 'reservation.html', {
                'error': 'This parking slot is currently disabled by admin.',
                'today': today.strftime('%Y-%m-%d'),
                'two_weeks': two_weeks.strftime('%Y-%m-%d')
            })

        # Konversi waktu
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            start_datetime = datetime.strptime(f"{formatted_date} {start_hour}:00", "%Y-%m-%d %H:%M:%S")
            end_datetime = datetime.strptime(f"{formatted_date} {end_hour}:00", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messages.error(request, "Invalid date or time format.")
            return redirect('reservation')

        # Simpan reservasi
        reservation = Reservation.objects.create(
            user=request.user,
            spot=spot,
            start_time=start_datetime,
            end_time=end_datetime,
        )

        return redirect('reservationdetails', reservation_id=reservation.id)

    # GET request: tampilkan form kosong
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
    return redirect('reservation')

def history_view(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-start_time').select_related('car')
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
    # ───────────────────────── validasi querystring ─────────────────────────
    selected_date_str = request.GET.get('date')
    if not selected_date_str:
        return JsonResponse({'error': 'No date provided'}, status=400)

    selected_date = parse_date(selected_date_str)
    if not selected_date:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # ───────────────────────── core logic ─────────────────────────
    today  = localdate()
    result = []

    for spot in Spot.objects.all().order_by('spot_number'):
        # 1) Jika admin men‑disable spot → selalu "disabled"
        if spot.is_disabled:
            status = "disabled"

        else:
            # 2) Ada/tidaknya reservasi pada tanggal yang diminta
            reserved_on_date = Reservation.objects.filter(
                spot=spot,
                start_time__date=selected_date
            ).exists()

            if selected_date == today:
                # Hari ini: pertimbangkan sensor live
                if spot.status == "occupied":
                    status = "occupied"
                elif reserved_on_date:
                    status = "reserved"
                else:
                    status = "available"
            else:
                # Tanggal lain: hanya lihat reservasi
                status = "reserved" if reserved_on_date else "available"

        result.append({
            "spot_number": spot.spot_number,
            "status":      status,
        })

    return JsonResponse(result, safe=False)

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

def slot_details_json(request):
    """
    Return detail (status, username, time) untuk semua slot di tanggal yg diminta.
    """
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'No date provided'}, status=400)

    selected_date = parse_date(date_str)
    if not selected_date:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    today = localdate()          # ← gunakan helper ini

    results = []
    for spot in Spot.objects.all().order_by('spot_number'):
        # default kosong
        data = {
            "spot_number": spot.spot_number,
            "status": "available",   # fallback
            "username": "",
            "time": ""
        }

        # --- status sensor / existing logic ---
        if selected_date == today:
            data["status"] = spot.status       # occupied / reserved / available
        else:
            data["status"] = "reserved" if Reservation.objects.filter(
                spot=spot,
                start_time__date=selected_date
            ).exists() else "available"

        # --- cari reservasi terdekat pada tanggal tsb ---
        res = Reservation.objects.filter(
            spot=spot,
            start_time__date=selected_date
        ).order_by('start_time').first()

        if res:                                              # ⇒ Reserved
            start = localtime(res.start_time).strftime("%H:%M")
            end   = localtime(res.end_time).strftime("%H:%M")
            data.update({
                "username": res.user.username,
                "time": f"{start} - {end}",
                "status": "reserved"        # paksa reserved utk konsistensi label
            })

        results.append(data)

    return JsonResponse(results, safe=False)

@require_POST
def toggle_spot_disable(request):
    """
    Body JSON = { "spot_numbers": [1,2], "disable": true }
    """
    try:
        body = json.loads(request.body.decode())
        spot_nums = body.get("spot_numbers", [])
        disable   = bool(body.get("disable", False))

        Spot.objects.filter(spot_number__in=spot_nums).update(is_disabled=disable)

        # Update status kolom status → 'disabled' / 'available'
        if disable:
            Spot.objects.filter(spot_number__in=spot_nums).update(status='disabled')
        else:
            Spot.objects.filter(spot_number__in=spot_nums, status='disabled').update(status='available')

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)