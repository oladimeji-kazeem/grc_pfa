from neomodel import (
    StructuredNode, StringProperty, UniqueIdProperty, RelationshipTo, config,
    IntegerProperty, FloatProperty, ArrayProperty # <-- Added ArrayProperty
)
from django.conf import settings

# 1. Configure the connection (Assumes settings are already set up)
# config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL

# --- Define Core GRC Nodes ---

class ComplianceRequirementNode(StructuredNode):
    uid = UniqueIdProperty() 
    requirement_code = StringProperty(unique=True)
    source = StringProperty()
    category = StringProperty()
    description_embedding = ArrayProperty(FloatProperty(), default=[]) # Added Embedding Field
    
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
    description_embedding = ArrayProperty(FloatProperty(), default=[]) # Added Embedding Field
    
    maps_to_requirement = RelationshipTo(ComplianceRequirementNode, 'MAPS_TO')
    covered_by_control = RelationshipTo(ControlNode, 'COVERS')
    
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
    description_embedding = ArrayProperty(FloatProperty(), default=[]) # Added Embedding Field

    linked_to_objective = RelationshipTo(CorporateObjectiveNode, 'LINKED_TO')

    class Meta:
        db_label = "Risk"

# Note: The Neo4j connection initialization is usually done in settings.py or app config.
