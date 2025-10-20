# risk/models.py
from django.db import models
from governance.models import CorporateObjective
from core.models import Profile
from uuid import uuid4

class Risk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100)
    likelihood = models.IntegerField() # CHECK (likelihood >= 1 AND likelihood <= 5)
    impact = models.IntegerField()     # CHECK (impact >= 1 AND impact <= 5)
    
    # risk_score calculated field can be implemented as a property in Django or calculated before save
    # risk_score = models.IntegerField(editable=False) # GENERATED ALWAYS AS (likelihood * impact) STORED
    
    status = models.CharField(max_length=50, default='open')
    mitigation_plan = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='risks_owned')
    
    # Fields for Objective and Approval Workflow
    objective = models.ForeignKey(CorporateObjective, on_delete=models.SET_NULL, null=True, blank=True)
    risk_champion = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='risks_championed')
    approval_status = models.CharField(max_length=50, default='pending')
    approved_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='risks_approved')
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def risk_score(self):
        return self.likelihood * self.impact

    def __str__(self):
        return self.title

class RiskFactor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE)
    factor_name = models.CharField(max_length=255)
    factor_value = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.risk.title} - {self.factor_name}"

class Incident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default='reported')
    reported_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name='incidents_reported')
    assigned_to = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents_assigned')
    root_cause = models.TextField(null=True, blank=True)
    corrective_action = models.TextField(null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class AIRecommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    recommendation_type = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    rationale = models.TextField()
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, default=0.00)
    priority = models.CharField(max_length=50, default='medium')
    status = models.CharField(max_length=50, default='pending')
    implemented_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    implemented_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title