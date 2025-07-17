from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.timezone import now  # ← ini baris yang perlu Anda tambahkan

# Create your models here.
class Car(models.Model):
    license_plate = models.CharField(max_length=20, unique=True)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='cars')
    image = models.ImageField(upload_to='car_image/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"
    
class CustomUser (AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True
    )

    def __str__(self):
        return self.username
    
class Spot(models.Model):
    spot_number = models.CharField(max_length=20, unique=True)

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('disabled', 'Disabled'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    is_disabled = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    buzzer_active = models.BooleanField(default=True)

    def update_status_from_distance(self, distance_cm):
        if self.is_disabled:
            return

        current_time = now()
        prev_status = self.status

        # Cek apakah ada reservasi aktif saat ini
        active_reservation = Reservation.objects.filter(
            spot=self,
            start_time__lte=current_time,
            end_time__gte=current_time
        ).first()

        if distance_cm < 30:
            # Mobil terdeteksi
            self.status = 'occupied'

            if active_reservation:
                if not active_reservation.parked:
                    self.buzzer_active = True  # mobil baru masuk
                    active_reservation.parked = True
                    active_reservation.save()
                else:
                    self.buzzer_active = False  # sudah pernah diverifikasi
            else:
                self.buzzer_active = False  # mobil bukan pemilik slot
        else:
            # Mobil tidak terdeteksi
            if active_reservation:
                self.status = 'reserved'  # masih ada reservasi walaupun kosong
            else:
                self.status = 'available'

            self.buzzer_active = False

            if active_reservation and active_reservation.parked:
                active_reservation.parked = False
                active_reservation.save()

        self.save()

    def __str__(self):
        return f"Spot {self.spot_number}"
       
class Reservation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True)
    parked = models.BooleanField(default=False)
    
    def __str__(self):
        cars = self.user.cars.all()
        if cars:
            return f"Reservation by {self.user.username} from {self.start_time} to {self.end_time}"
        else:
            return f"Reservation by {self.user.username} from {self.start_time} to {self.end_time}"

    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
