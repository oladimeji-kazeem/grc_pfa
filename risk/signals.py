from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from risk.models import Risk
# Import the Celery Task
from risk.tasks import process_text_embedding
from governance.graph_models import RiskNode # Assuming RiskNode is defined here or imported

# Signal to handle Risk creation/update
@receiver(post_save, sender=Risk)
def update_risk_graph_and_embed(sender, instance, created, **kwargs):
    uid_str = str(instance.id)
    text_content = f"Title: {instance.title}. Description: {instance.description or ''}. Mitigation: {instance.mitigation_plan or ''}"
    
    # 1. Synchronize basic data with Neo4j (Immediate)
    if created:
        RiskNode.create(
            uid=uid_str, 
            title=instance.title, 
            category=instance.category, 
            likelihood=instance.likelihood,
            impact=instance.impact,
            risk_score=instance.risk_score
        )
    else:
        risk_node = RiskNode.nodes.get(uid=uid_str)
        risk_node.title = instance.title
        risk_node.category = instance.category
        risk_node.likelihood = instance.likelihood
        risk_node.impact = instance.impact
        risk_node.risk_score = instance.risk_score
        risk_node.save()

    # 2. Queue AI Embedding Task (Asynchronous)
    process_text_embedding.apply_async(
        args=['risk', uid_str, text_content],
        countdown=5 # Start embedding after a small delay (5 seconds)
    )

@receiver(post_delete, sender=Risk)
def delete_risk_graph(sender, instance, **kwargs):
    """Deletes the Risk node from Neo4j when the Django object is deleted."""
    try:
        RiskNode.nodes.get(uid=str(instance.id)).delete()
    except DoesNotExist:
        pass
