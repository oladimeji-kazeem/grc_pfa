# governance/models.py
from django.db import models
from core.models import Profile # Import Profile from core app
from uuid import uuid4

class CorporateObjective(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    department = models.CharField(max_length=255)
    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='objectives_owned')
    fiscal_year = models.CharField(max_length=10)
    status = models.CharField(max_length=50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Policy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100)
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=50, default='draft')
    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='policies_owned')
    review_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    document_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Control(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    control_code = models.CharField(max_length=255, unique=True) # unique constraint
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100)
    control_type = models.CharField(max_length=50) # preventive, detective, corrective
    status = models.CharField(max_length=50, default='active')
    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='controls_owned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.control_code

# Mapping tables that connect Governance models
class PolicyControlMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)
    control = models.ForeignKey(Control, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('policy', 'control') # Unique constraint