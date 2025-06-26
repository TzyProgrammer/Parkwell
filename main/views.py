from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from .models import CustomUser, Spot, Reservation, Car
from django.contrib import messages
import logging
from datetime import datetime, time, date, timedelta
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

# Create your views here.
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        phone_number = request.POST['phone_number']
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')
        
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
            logger.warning("Authentication failed for email: %s", username)
            messages.error(request, 'Invalid email or password')
            return redirect('login')
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

def delete_reservation(request, reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    reservation.delete()
    return redirect('reservation')

def history_view(request):
    return render(request, 'history.html')

def guide_view(request):
    return render(request, 'guide.html')
