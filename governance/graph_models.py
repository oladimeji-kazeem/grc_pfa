# governance/graph_models.py
from neomodel import (
    StructuredNode, StringProperty, UniqueIdProperty, RelationshipTo, config,
    IntegerProperty, FloatProperty
)
from django.conf import settings

# 1. Configure the connection
config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL

# --- Define Core GRC Nodes ---

class ComplianceRequirementNode(StructuredNode):
    # 'uid' stores the UUID from the PostgreSQL model
    uid = UniqueIdProperty() 
    requirement_code = StringProperty(unique=True)
    source = StringProperty()
    category = StringProperty()
    
    class Meta:
        db_label = "ComplianceRequirement"

class ControlNode(StructuredNode):
    uid = UniqueIdProperty()
    control_code = StringProperty(unique=True)
    control_type = StringProperty()
    status = StringProperty()

    class Meta:
        db_label = "Control"

class PolicyNode(StructuredNode):
    uid = UniqueIdProperty() 
    title = StringProperty(required=True)
    category = StringProperty()
    status = StringProperty()
    
    # 2. Define Relationships based on mappings in the original schema
    maps_to_requirement = RelationshipTo(ComplianceRequirementNode, 'MAPS_TO') # From regulation_mappings
    covered_by_control = RelationshipTo(ControlNode, 'COVERS')               # From policy_control_mappings
    
    class Meta:
        db_label = "Policy"

class CorporateObjectiveNode(StructuredNode):
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    fiscal_year = StringProperty()
    department = StringProperty()
    
    class Meta:
        db_label = "Objective"

class RiskNode(StructuredNode):
    uid = UniqueIdProperty()
    title = StringProperty(required=True)
    category = StringProperty()
    likelihood = IntegerProperty()
    impact = IntegerProperty()
    risk_score = IntegerProperty()

    # 3. Define Relationship to Objectives
    linked_to_objective = RelationshipTo(CorporateObjectiveNode, 'LINKED_TO') # From risks table objective_id

    class Meta:
        db_label = "Risk"

# Note: User/Profile nodes are typically kept separate or added later for graph partitioning.