from risk.models import AIRecommendation, Risk
from governance.models import Policy, Control
from governance.graph_models import PolicyNode, ControlNode, RiskNode
from risk.gnn_model import GRCGNN # Import your GNN model
from risk.graph_loader import GRCGraphLoader
from django.db.models import Count
from uuid import uuid4
import torch
import random

class RecommendationService:
    """
    Analyzes the GRC graph to find structural gaps (missing links) and generates
    AI recommendations based on GNN link prediction scores.
    """
    
    # Mock loaded model and loader instance for simulation
    GNN_MODEL = GRCGNN(meta_paths=[('Risk', 'Risk', 'Risk')],
                       in_feats={'Risk': 386}, 
                       num_classes=5, 
                       num_heads=2)
    GRAPH_LOADER = GRCGraphLoader()

    @classmethod
    def generate_recommendations(cls, entity_type: str, entity_id: str):
        """
        Orchestrates the GNN analysis and insertion of AIRecommendation records.
        """
        # 1. Load the current graph (GNN-ready DGL/PyG format)
        g = cls.GRAPH_LOADER.load_full_graph()
        
        # 2. Perform GNN inference to get node embeddings and link predictions
        # NOTE: This uses the link_prediction_head defined in risk/gnn_model.py
        cls.GNN_MODEL.eval()
        
        # Extract features (mock: in a real scenario, features are tensors from the graph object)
        risk_features = g.nodes['Risk'].data['feat'] 
        policy_features = g.nodes['Policy'].data['feat']

        # Mock: Generate high-potential missing links via link prediction
        high_potential_gaps = cls._mock_link_prediction(entity_type, entity_id)

        recommendations_list = []

        for gap in high_potential_gaps:
            # 3. Use LLM/Heuristic to generate rationale and final title
            rationale_text = cls._generate_rationale(gap['source_type'], gap['target_type'], gap['score'])
            
            recommendations_list.append(AIRecommendation(
                id=uuid4(),
                recommendation_type=gap['recommendation_type'],
                entity_type=entity_type,
                entity_id=entity_id,
                title=gap['title'],
                description=gap['description'],
                rationale=rationale_text,
                confidence_score=gap['score'],
                priority=gap['priority']
            ))

        # 4. Bulk insert into PostgreSQL (ai_recommendations table)
        AIRecommendation.objects.bulk_create(recommendations_list)
        return len(recommendations_list)

    @classmethod
    def _mock_link_prediction(cls, target_type, target_id):
        """
        Mocks the GNN Link Prediction module output for demo purposes.
        In production, this would execute the trained GNN model's link prediction head.
        """
        
        # --- A. Find Missing Controls for High-Risk Policies ---
        # Logic: Find policies that don't cover any controls but are related to a high-score risk
        high_risk_policies = Policy.objects.filter(
            risk__risk_score__gte=15  # Risks with score >= 15
        ).annotate(
            num_controls=Count('policycontrolmapping')
        ).filter(
            num_controls=0
        ).distinct()[:2] # Grab 2 examples

        gaps = []
        for policy in high_risk_policies:
            # Mock suggesting a link to a generic control type
            gaps.append({
                'recommendation_type': 'control_gap',
                'source_type': 'Policy',
                'target_type': 'Control',
                'title': f"Implement Core Control for Policy: {policy.title[:20]}...",
                'description': f"High-risk areas covered by Policy '{policy.title}' lack active mitigating controls. GNN predicts a strong need for Preventive Controls.",
                'score': random.uniform(0.85, 0.95),
                'priority': 'critical'
            })
            
        # --- B. Find Unmapped Compliance Requirements ---
        # Logic: Find high-priority requirements that have zero policy mappings (high compliance gap)
        # Note: ComplianceRequirement model is in compliance/models.py
        try:
            from compliance.models import ComplianceRequirement
            unmapped_reqs = ComplianceRequirement.objects.filter(
                regulationmapping__isnull=True, 
                status__in=['pending', 'in-progress']
            )[:1]
            
            for req in unmapped_reqs:
                 gaps.append({
                    'recommendation_type': 'compliance_gap',
                    'source_type': 'Requirement',
                    'target_type': 'Policy',
                    'title': f"Map Uncovered Requirement: {req.requirement_code}",
                    'description': f"Compliance Requirement {req.requirement_code} from {req.source} is not mapped to any governance policy, posing a direct compliance gap.",
                    'score': random.uniform(0.70, 0.85),
                    'priority': 'high'
                })
        except ImportError:
            # Handle case where compliance models might not be fully available yet
            pass

        return gaps

    @classmethod
    def _generate_rationale(cls, source_type, target_type, score):
        """Mocks the LLM step that generates a human-readable rationale."""
        confidence = f"{score * 100:.0f}%"
        if source_type == 'Policy' and target_type == 'Control':
            return (
                f"GNN Link Prediction score of {confidence} indicates a crucial link "
                f"is missing between the high-risk Policy and any defensive Controls. "
                f"Analysis shows the connected Risk Nodes (via the graph) are active."
            )
        elif source_type == 'Requirement' and target_type == 'Policy':
            return (
                f"Semantic analysis (BERT) shows Requirement text has high similarity "
                f"to existing Policy descriptions ({confidence}). The graph structure confirms "
                f"no direct 'MAPS_TO' link exists, indicating a data entry or review omission."
            )
        return f"AI generated rationale with {confidence} confidence."
