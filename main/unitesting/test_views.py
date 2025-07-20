import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime, time  # Perbaikan: tambah impor datetime dan time
from main.models import CustomUser, Spot, Reservation, Car
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch


pytestmark = pytest.mark.django_db


@pytest.fixture
def client_logged_user(client):
    user = CustomUser.objects.create_user(username="testuser", password="password123", role="user")
    client.login(username="testuser", password="password123")
    return user


@pytest.fixture
def client_logged_admin(client):
    # Login admin via session, bypass password logic
    session = client.session
    session['admin_logged_in'] = True
    session.save()


@pytest.fixture
def spot():
    return Spot.objects.create(spot_number="99")


def test_register_login_logout(client):
    # Register
    response = client.post(reverse('register'), {
        'username': 'newuser',
        'email': 'user@example.com',
        'password': '1234',
        'confirm_password': '1234',
        'phone_number': '08123456789'
    })
    assert response.status_code == 302  # redirect ke login

    # Login
    response = client.post(reverse('login'), {
        'username': 'newuser',
        'password': '1234',
    })
    assert response.status_code == 302

    # Logout
    response = client.get(reverse('logout'))
    assert response.status_code == 302


def test_user_reservation_flow(client):
    # 1. Daftarkan dan login user
    user = CustomUser.objects.create_user(username="testuser", password="password123", role="user")
    assert client.login(username="testuser", password="password123")

    # 2. Tambahkan mobil ke user
    Car.objects.create(
        license_plate="B1234XYZ",
        brand="Toyota",
        model="Avanza",
        color="Silver",
        user=user
    )

    # 3. Buat spot dengan spot_number sebagai string
    spot_number = "99"
    spot = Spot.objects.create(spot_number=spot_number)

    # 4. Siapkan tanggal dan waktu di masa depan - gunakan format yang sesuai dengan view
    today = timezone.localtime().date()
    tomorrow = today + timedelta(days=1)
    
    # Format tanggal: YYYY-MM-DD (sesuai dengan yang diharapkan view)
    date_str = tomorrow.strftime("%Y-%m-%d")
    
    # 5. Kirim POST request ke /reservation/
    response = client.post(reverse('reservation'), {
        'date': date_str,  # Format yang benar
        'start_time': "09:00",  # Format dengan menit
        'end_time': "10:00",    # Format dengan menit
        'slot': spot_number,
    }, follow=True)

    # 6. Debug output
    print("✅ Spot tersedia:", list(Spot.objects.values_list("spot_number", flat=True)))
    print("✅ Semua reservasi:", list(Reservation.objects.values("user_id", "spot_id", "start_time", "end_time")))

    # 7. Verifikasi respons dan data
    assert response.status_code == 200, f"Tidak berhasil redirect, status: {response.status_code}"
    assert Reservation.objects.filter(user=user).exists(), "❌ Reservation tidak tersimpan"
    
    reservation = Reservation.objects.get(user=user)
    assert reservation.spot == spot, "❌ Spot yang disimpan tidak sesuai"
    
    # Verifikasi waktu dengan toleransi zona waktu
    # Perbaikan: gunakan combine dengan date dan time yang benar
    start_expected = timezone.make_aware(datetime.combine(tomorrow, time(9, 0)))
    end_expected = timezone.make_aware(datetime.combine(tomorrow, time(10, 0)))
    
    assert reservation.start_time == start_expected, f"❌ Waktu mulai tidak sesuai: {reservation.start_time} vs {start_expected}"
    assert reservation.end_time == end_expected, f"❌ Waktu selesai tidak sesuai: {reservation.end_time} vs {end_expected}"


def test_update_account(client, client_logged_user):
    client.login(username='testuser', password='password123')
    response = client.post(reverse('update_account'), {
        'username': 'updateduser',
        'password': 'newpass123',
        'confirm_password': 'newpass123',
        'phone_number': '080000000'
    })
    assert response.status_code == 302
    user = CustomUser.objects.get(id=client_logged_user.id)
    assert user.username == 'updateduser'


def test_user_park_and_buzzer_then_available(client_logged_user, spot):
    now = timezone.now()
    reservation = Reservation.objects.create(
        user=client_logged_user,
        spot=spot,
        start_time=now - timedelta(minutes=10),
        end_time=now + timedelta(hours=1)
    )

    # Mobil datang
    spot.update_status_from_distance(10)
    spot.refresh_from_db()
    assert spot.status == 'occupied'
    assert spot.buzzer_active is True

    # Admin mematikan buzzer
    spot.buzzer_active = False
    spot.save()
    spot.refresh_from_db()
    assert spot.buzzer_active is False
    assert spot.status == 'occupied'

    # Reservasi berakhir + mobil pergi
    reservation.start_time = now - timedelta(hours=3)
    reservation.end_time = now - timedelta(hours=1)
    reservation.save()
    spot.update_status_from_distance(100)
    spot.refresh_from_db()
    assert spot.status == 'available'


def test_admin_login_logout(client):
    # Login admin
    response = client.post(reverse('adminlogin'), {'password': 'parkircerdas'})
    assert response.status_code == 302
    # Logout admin
    response = client.get(reverse('adminlogout'))
    assert response.status_code == 302


@patch("main.views.publish.single")
def test_admin_turn_off_buzzer_api(mock_publish, client_logged_admin, spot, client):
    client.session['admin_logged_in'] = True
    client.session.save()

    spot.buzzer_active = True
    spot.status = "occupied"
    spot.save()

    response = client.post(reverse('admin_turn_off_buzzer'), content_type="application/json", data={
        "slot_number": spot.spot_number
    })
    assert response.status_code == 200
    spot.refresh_from_db()
    assert spot.buzzer_active is False


@patch("main.views.publish.single")
def test_toggle_spot_disable_api(mock_publish, client_logged_admin, spot, client):
    client.session['admin_logged_in'] = True
    client.session.save()

    response = client.post(reverse('toggle_spot_disable'), content_type="application/json", data={
        "spot_numbers": [spot.spot_number],
        "disable": True
    })
    assert response.status_code == 200
    spot.refresh_from_db()
    assert spot.is_disabled is True


# TEST ALL ENDPOINTS YANG TIDAK BUTUH POST
def test_get_all_pages(client, client_logged_user):
    client.login(username='testuser', password='password123')
    urls = [
        'home', 'reservation', 'account', 'status', 'guide', 'contact', 'history'
    ]
    for name in urls:
        response = client.get(reverse(name))
        assert response.status_code == 200


def test_api_spots_dynamic_status(client, spot):
    date_str = timezone.localdate().strftime('%Y-%m-%d')
    url = reverse('spots_dynamic_status_json') + f'?date={date_str}'
    response = client.get(url)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_reserved_intervals(client, spot):
    date_str = timezone.localdate().strftime('%Y-%m-%d')
    url = reverse('reserved_intervals') + f'?date={date_str}&spot={spot.spot_number}'
    response = client.get(url)
    assert response.status_code == 200
    assert 'blocked_intervals' in response.json()


def test_api_admin_home_details(client):
    date_str = timezone.localdate().strftime('%Y-%m-%d')
    url = reverse('admin_home_details_json') + f'?date={date_str}'
    response = client.get(url)
    assert response.status_code == 200
    assert isinstance(response.json(), list)