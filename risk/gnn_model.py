import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl.nn as dglnn
from dgl.data import DGLDataset # Required if you wrap the graph loading in a Dataset

# Define the dimensions based on our requirements
BERT_EMBEDDING_DIM = 384  # From 'all-MiniLM-L6-v2'
NUMERICAL_FEATURES = 1    # Risk Score (normalized)
IN_FEATURES = BERT_EMBEDDING_DIM + NUMERICAL_FEATURES # 385
HIDDEN_DIM = 128
OUT_NODE_CLASSIFICATION_DIM = 3 # 3 classes: Low/Medium/High Mitigated Risk
FINAL_LINK_PREDICTION_DIM = 64 # Final dimension for link scoring


class HeteroGNNLayer(nn.Module):
    """
    A single layer of a Heterogeneous Graph Attention Network (HGT).
    This handles message passing over different node and edge types.
    """
    def __init__(self, in_size, out_size, canonical_etypes):
        super().__init__()
        # Use DGL's HeteroGraphConv for message passing
        self.conv = dglnn.HeteroGraphConv({
            etype[1]: dglnn.GraphConv(in_size, out_size)
            for etype in canonical_etypes
        }, aggregate='sum')

    def forward(self, graph, h):
        """h is a dict of node features indexed by node type"""
        h_new = self.conv(graph, h)
        return h_new


class GRCGNN(nn.Module):
    """
    The main Heterogeneous Graph Neural Network for GRC.
    Combines Node Classification (Risk Mitigation) and Link Prediction (AI Recommendations).
    """
    def __init__(self, canonical_etypes, node_types):
        super().__init__()
        self.node_types = node_types
        
        # 1. Input Projection: Map all node features to a uniform HIDDEN_DIM
        self.input_projections = nn.ModuleDict({
            ntype: nn.Linear(IN_FEATURES, HIDDEN_DIM)
            for ntype in node_types
        })
        
        # 2. Two hidden HGT layers for deep feature learning
        self.layer1 = HeteroGNNLayer(HIDDEN_DIM, HIDDEN_DIM, canonical_etypes)
        self.layer2 = HeteroGNNLayer(HIDDEN_DIM, HIDDEN_DIM, canonical_etypes)
        
        # 3. Task-Specific Output Heads
        
        # A) Node Classification Head (for Risks: predicting final risk status)
        self.risk_classifier = nn.Sequential(
            nn.Linear(HIDDEN_DIM, 64),
            nn.ReLU(),
            nn.Linear(64, OUT_NODE_CLASSIFICATION_DIM)
        )
        
        # B) Link Prediction Head (for generating embeddings used in dot-product scoring)
        # We only need embeddings for nodes involved in prediction (Policy, Control, Req)
        self.link_embed_proj = nn.ModuleDict({
            ntype: nn.Linear(HIDDEN_DIM, FINAL_LINK_PREDICTION_DIM)
            for ntype in ['Policy', 'Control', 'ComplianceRequirement']
        })

    def forward(self, graph, features):
        """
        Features are expected as a dictionary: {node_type: Tensor[N, IN_FEATURES]}
        """
        h = {}
        for ntype, feat in features.items():
            h[ntype] = F.relu(self.input_projections[ntype](feat))
            
        # Message passing layers
        h = self.layer1(graph, h)
        h = {k: F.relu(v) for k, v in h.items()}
        h = self.layer2(graph, h)
        h = {k: F.relu(v) for k, v in h.items()}
        
        # Final Node Embeddings (shared latent space)
        self.final_embeddings = h
        
        return h

    def classify_risks(self, h_risks):
        """Performs the Node Classification task on Risk nodes."""
        return self.risk_classifier(h_risks)
    
    def get_link_embeddings(self):
        """Generates task-specific embeddings for Link Prediction."""
        link_embeds = {}
        for ntype in self.link_embed_proj.keys():
            if ntype in self.final_embeddings:
                link_embeds[ntype] = self.link_embed_proj[ntype](self.final_embeddings[ntype])
        return link_embeds

# ----------------- Link Prediction Scoring Module -----------------

class LinkPredictor(nn.Module):
    """
    Computes the score for a potential link between two nodes using a dot-product.
    This is used to suggest missing Policy-Control links (AI Recommendations).
    """
    def forward(self, h_src, h_dst):
        # Cosine similarity (dot product of normalized vectors) is common for link prediction
        score = (h_src * h_dst).sum(dim=1)
        return score

# --- Example Initialisation ---

# The full list of canonical edge types from the graph loader (Step 3.3.2)
CANONICAL_ETYPES = [
    ('Policy', 'COVERS', 'Control'), 
    ('Policy', 'MAPS_TO', 'ComplianceRequirement'), 
    ('Risk', 'LINKED_TO', 'Objective'),
]
NODE_TYPES = ['Policy', 'Risk', 'Control', 'ComplianceRequirement', 'Objective']

grc_gnn_model = GRCGNN(CANONICAL_ETYPES, NODE_TYPES)
link_predictor = LinkPredictor()
