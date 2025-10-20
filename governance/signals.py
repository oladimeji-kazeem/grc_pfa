# governance/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Policy, Control, CorporateObjective # Import relational models
from .graph_models import PolicyNode, ControlNode, CorporateObjectiveNode

# Signal to handle Policy creation/update
@receiver(post_save, sender=Policy)
def update_policy_graph(sender, instance, created, **kwargs):
    """Creates or updates a Policy node in Neo4j."""
    uid_str = str(instance.id)
    if created:
        PolicyNode.create(uid=uid_str, title=instance.title, category=instance.category, status=instance.status)
    else:
        policy_node = PolicyNode.nodes.get(uid=uid_str)
        policy_node.title = instance.title
        policy_node.category = instance.category
        policy_node.status = instance.status
        policy_node.save()

@receiver(post_delete, sender=Policy)
def delete_policy_graph(sender, instance, **kwargs):
    """Deletes the Policy node from Neo4j when the Django object is deleted."""
    try:
        PolicyNode.nodes.get(uid=str(instance.id)).delete()
    except PolicyNode.DoesNotExist:
        pass

# Signal to handle CorporateObjective creation/update
@receiver(post_save, sender=CorporateObjective)
def update_objective_graph(sender, instance, created, **kwargs):
    uid_str = str(instance.id)
    if created:
        CorporateObjectiveNode.create(uid=uid_str, title=instance.title, fiscal_year=instance.fiscal_year, department=instance.department)
    else:
        objective_node = CorporateObjectiveNode.nodes.get(uid=uid_str)
        objective_node.title = instance.title
        objective_node.fiscal_year = instance.fiscal_year
        objective_node.department = instance.department
        objective_node.save()

# TODO: Create similar post_save and post_delete signals for Control, 
#       ComplianceRequirement (in the compliance app), and Risk (in the risk app).