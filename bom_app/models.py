from django.contrib.auth.models import AbstractUser
from django.db import models



class Item(models.Model):

    head = models.CharField(max_length=50)
    make = models.CharField(max_length=1000)
    mat_name = models.CharField(max_length=150)
    type_no = models.CharField(max_length=100)
    least_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.head}: {self.mat_name} ({self.type_no})"
 