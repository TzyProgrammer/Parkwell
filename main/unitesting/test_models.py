import pytest
from django.utils import timezone
from datetime import timedelta
from main.models import CustomUser, Car, Spot, Reservation

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(username='testuser', password='password123', role='user')


@pytest.fixture
def car(user):
    return Car.objects.create(
        license_plate='B123ABC',
        brand='Toyota',
        model='Avanza',
        color='Silver',
        user=user
    )


@pytest.fixture
def spot():
    return Spot.objects.create(spot_number='A1')


@pytest.fixture
def reservation(user, spot, car):
    now = timezone.now()
    return Reservation.objects.create(
        user=user,
        spot=spot,
        car=car,
        start_time=now,
        end_time=now + timedelta(hours=2)
    )

def test_reservation_and_parking_buzzer_behavior(user, car):
    """
    Simulasi alur lengkap:
    1. User melakukan reservasi aktif.
    2. Sensor mendeteksi mobil datang → spot berubah menjadi 'occupied' dan buzzer menyala.
    3. Admin mematikan buzzer secara manual.
    4. Status spot tetap 'occupied' meskipun buzzer sudah dimatikan.
    """

    # Step 1: Buat Spot dan Reservasi aktif (waktu sekarang)
    spot = Spot.objects.create(spot_number='A99')
    now = timezone.now()

    reservation = Reservation.objects.create(
        user=user,
        car=car,
        spot=spot,
        start_time=now - timedelta(minutes=10),  # dimulai 10 menit lalu
        end_time=now + timedelta(hours=1)        # selesai 1 jam ke depan
    )

    # Step 2: Simulasikan sensor mendeteksi kendaraan (jarak < 30 cm)
    spot.update_status_from_distance(10)
    spot.refresh_from_db()

    # → Setelah kendaraan terdeteksi, status menjadi 'occupied' dan buzzer menyala
    assert spot.status == 'occupied', "Status harus berubah menjadi 'occupied'"
    assert spot.buzzer_active is True, "Buzzer harus menyala ketika kendaraan terdeteksi"

    # Step 3: Admin mematikan buzzer secara manual
    spot.buzzer_active = False
    spot.save()

    # Step 4: Cek lagi: buzzer sudah mati, tapi status tetap 'occupied'
    spot.refresh_from_db()
    assert spot.buzzer_active is False, "Buzzer harus bisa dimatikan manual oleh admin"
    assert spot.status == 'occupied', "Status spot tetap 'occupied' meskipun buzzer dimatikan"


def test_reserve_park_and_leave_flow(spot, reservation):
    """
    Simulasi alur lengkap:
    1. User reservasi slot
    2. Mobil datang → jarak < 30cm → status: 'occupied', parked: True
    3. Mobil pergi → jarak > 30cm → status: 'available', parked: False
    """

    # STEP 1: Saat baru reservasi, spot masih kosong
    spot.update_status_from_distance(100)  # mobil tidak ada
    spot.refresh_from_db()
    reservation.refresh_from_db()
    assert spot.status == 'reserved'
    assert reservation.parked is False
    assert spot.buzzer_active is False

    # STEP 2: Mobil masuk
    spot.update_status_from_distance(10)
    spot.refresh_from_db()
    reservation.refresh_from_db()
    assert spot.status == 'occupied'
    assert reservation.parked is True
    assert spot.buzzer_active is True

    # STEP 3: Mobil keluar
    spot.update_status_from_distance(100)
    spot.refresh_from_db()
    reservation.refresh_from_db()
    assert spot.status == 'reserved'  # masih dalam waktu reservasi
    assert reservation.parked is False
    assert spot.buzzer_active is False

def test_spot_becomes_available_after_reservation_ends(spot, reservation):
    """
    Uji skenario ketika:
    - Mobil sudah pergi (jarak > 30 cm)
    - Waktu reservasi sudah habis
    Hasil: Spot harus menjadi 'available'
    """

    # STEP 1: Simulasi mobil datang (mengaktifkan parked)
    spot.update_status_from_distance(10)
    spot.refresh_from_db()
    reservation.refresh_from_db()
    assert spot.status == 'occupied'
    assert reservation.parked is True

    # STEP 2: Mobil pergi (jarak > 30cm), tapi masih dalam waktu reservasi
    spot.update_status_from_distance(100)
    spot.refresh_from_db()
    reservation.refresh_from_db()
    assert spot.status == 'reserved'
    assert reservation.parked is False

    # STEP 3: Simulasikan waktu reservasi sudah habis
    reservation.start_time = timezone.now() - timedelta(hours=3)
    reservation.end_time = timezone.now() - timedelta(hours=1)
    reservation.save()

    # Update ulang spot untuk merefleksikan waktu sekarang
    spot.update_status_from_distance(100)
    spot.refresh_from_db()

    # Hasil akhir: spot menjadi available karena reservasi habis dan tidak ada mobil
    assert spot.status == 'available'
    assert spot.buzzer_active is False
