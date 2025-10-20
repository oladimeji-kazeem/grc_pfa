# core/models.py
from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4

class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True) # unique constraint
    code = models.CharField(max_length=20, unique=True) # unique constraint
    description = models.TextField(null=True, blank=True)
    head_of_department = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True, related_name='departments_led') # FK to Profile
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    # This replaces the default 'auth.users' and 'public.profiles' linking to Django's built-in User
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=255)
    department = models.CharField(max_length=255, null=True, blank=True) # Legacy department field
    department_fk = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members') # New FK to Department
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name

# AppRole Enum from SQL
APP_ROLES = [
    ('admin', 'Admin'), ('board', 'Board'), ('compliance', 'Compliance'), 
    ('risk', 'Risk'), ('audit', 'Audit'), ('ict', 'ICT'), ('management', 'Management')
]

class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=APP_ROLES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'role') # Unique constraint on user_id, role
        
    def __str__(self):
        return f"{self.user.username} - {self.role}"