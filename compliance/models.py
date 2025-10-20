# compliance/models.py
from django.db import models
from governance.models import Policy
from core.models import Profile
from uuid import uuid4

class ComplianceRequirement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    requirement_code = models.CharField(max_length=255, unique=True) # unique constraint
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='pending')
    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='compliance_owned')
    due_date = models.DateField(null=True, blank=True)
    evidence_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.requirement_code

class ComplianceChecklist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    framework = models.CharField(max_length=100)
    requirement_code = models.CharField(max_length=255)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default='not_started')
    assigned_to = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    evidence_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class PredictiveAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    alert_type = models.CharField(max_length=255)
    severity = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    predicted_date = models.DateField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, default=0.00)
    status = models.CharField(max_length=50, default='active')
    acknowledged_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class RegulationMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, null=True) # Null=True to match foreign key on DELETE SET NULL, though relation is strong
    requirement = models.ForeignKey(ComplianceRequirement, on_delete=models.CASCADE, null=True)
    mapping_confidence = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, default=0.00)
    mapping_rationale = models.TextField(null=True, blank=True)
    mapped_at = models.DateTimeField(auto_now_add=True)
    mapped_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('policy', 'requirement') # Unique constraint