from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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
        ('disabled',  'Disabled'), 
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    is_disabled = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    buzzer_active = models.BooleanField(default=True)

    def update_status_from_distance(self, distance_cm):
        if self.is_disabled:
            return
        
        # Status sebelumnya untuk deteksi perubahan
        prev_status = self.status
        
        if distance_cm < 30:
            self.status = 'occupied'
            if prev_status != 'occupied':
                self.buzzer_active = True  # Setel buzzer hidup saat transisi masuk
        else:
            self.status = 'available'
            self.buzzer_active = False  # Matikan buzzer saat kendaraan pergi

        self.save()
    
    def __str__(self):
        return f"Spot {self.spot_number}"
    
class Reservation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        cars = self.user.cars.all()
        if cars:
            return f"Reservation by {self.user.username} from {self.start_time} to {self.end_time}"
        else:
            return f"Reservation by {self.user.username} from {self.start_time} to {self.end_time}"

    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
