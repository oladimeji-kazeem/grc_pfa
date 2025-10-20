# audit/models.py
from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4

class AuditLog(models.Model):
    """
    Relational record of immutable actions, backed by the Blockchain Trust Ledger.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # Link to the Profile, replacing the original user_id UUID foreign key
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_entries',
        verbose_name="System Actor"
    )
    user_email = models.CharField(max_length=255, null=True, blank=True) # For logs where user is system/unauthenticated
    
    action = models.CharField(max_length=100)  # e.g., 'create', 'update', 'approve'
    entity_type = models.CharField(max_length=100) # e.g., 'risk', 'policy', 'user_role'
    entity_id = models.UUIDField(null=True, blank=True)
    
    details = models.JSONField(null=True, blank=True) # JSONB from SQL
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # FUTURE: Field to store the Blockchain Transaction Hash
    # blockchain_tx_hash = models.CharField(max_length=66, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Audit Log Entry (Trust Ledger)"
        verbose_name_plural = "Audit Log Entries (Trust Ledger)"
        # Ensures latest actions are always first in the Audit Trail view
        ordering = ['-timestamp'] 

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action} on {self.entity_type}"