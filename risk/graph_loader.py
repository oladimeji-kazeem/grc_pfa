import numpy as np
import dgl # Deep Graph Library (DGL)
import torch
from neo4j import GraphDatabase, Driver
from django.conf import settings
from typing import Dict, Tuple, List, Any

class GRCGraphLoader:
    """
    Loads the Neo4j GRC Graph into a DGL Heterogeneous Graph object
    ready for GNN training, including node features (embeddings/scores).
    """
    # Define Node Types and Features needed for the GNN
    NODE_TYPES = ['Policy', 'Risk', 'Control', 'ComplianceRequirement', 'Objective']
    
    # Define Edge Types (Heterogeneous Relationships)
    EDGE_TYPES = [
        ('Policy', 'COVERS', 'Control'), 
        ('Policy', 'MAPS_TO', 'ComplianceRequirement'), 
        ('Risk', 'LINKED_TO', 'Objective'),
        # Add bidirectional edges or other complex relationships as needed for GNN
    ]

    def __init__(self):
        # Use settings from Django configuration
        uri = settings.NEOMODEL_NEO4J_BOLT_URL
        # Parse Bolt URL to extract connection details (username and password)
        # Assuming the URL is in format: bolt://user:password@host:port
        parts = uri.split('@')
        auth_part = parts[0].split('//')[1]
        user, password = auth_part.split(':')
        host_port = parts[1]
        
        self.driver: Driver = GraphDatabase.driver(f"bolt://{host_port}", auth=(user, password))

    def close(self):
        self.driver.close()

    def _fetch_graph_data(self, tx) -> Tuple[Dict[str, Any], Dict[Tuple[str, str, str], List[Tuple[int, int]]]]:
        """Executes Cypher queries to retrieve nodes and relationships."""
        
        # --- 1. Fetch Nodes and Features ---
        # Fetch node IDs, their UID (Django FK), and critical features (embeddings, scores)
        node_query = """
        MATCH (n)
        WHERE n:Policy OR n:Risk OR n:Control OR n:ComplianceRequirement OR n:Objective
        RETURN 
            ID(n) AS node_id, 
            LABELS(n)[0] AS node_type, 
            n.uid AS uid, 
            n.risk_score AS risk_score,
            n.description_embedding AS embedding
        """
        nodes_result = tx.run(node_query).data()

        # --- 2. Fetch Relationships ---
        # Returns triplet: (source_type, edge_type, destination_type) and the node IDs
        rel_query = """
        MATCH (u)-[r]->(v)
        WHERE TYPE(r) IN ['COVERS', 'MAPS_TO', 'LINKED_TO']
        RETURN 
            ID(u) AS source_id, 
            LABELS(u)[0] AS source_type, 
            TYPE(r) AS rel_type, 
            ID(v) AS dest_id, 
            LABELS(v)[0] AS dest_type
        """
        rels_result = tx.run(rel_query).data()
        
        return nodes_result, rels_result

    def load_dgl_heterogeneous_graph(self) -> dgl.DGLGraph:
        """
        Connects to Neo4j, fetches the heterogeneous graph, processes features,
        and returns a DGLGraph object ready for GNN.
        """
        with self.driver.session() as session:
            nodes_data, rels_data = session.execute_read(self._fetch_graph_data)

        # 1. Map Neo4j IDs to continuous integer IDs (essential for DGL/PyG)
        neo4j_to_dgl_id = {node['node_id']: i for i, node in enumerate(nodes_data)}
        
        # 2. Separate nodes and features by type
        node_data_by_type = {ntype: [] for ntype in self.NODE_TYPES}
        feature_data_by_type = {ntype: [] for ntype in self.NODE_TYPES}
        
        # Determine embedding dimension (e.g., 384 from BERT)
        EMB_DIM = 384 

        for node in nodes_data:
            ntype = node['node_type']
            
            # --- Feature Engineering: Combine features ---
            features = []
            
            # A) BERT Embedding Feature (List[Float])
            embedding = node['embedding']
            features.extend(embedding if embedding and len(embedding) == EMB_DIM else [0.0] * EMB_DIM)
            
            # B) Numerical Features (Risk Score)
            risk_score = node.get('risk_score', 0) 
            features.append(risk_score / 25.0) # Normalize score (Max score 5x5=25)

            # Convert features list to a tensor
            feature_data_by_type[ntype].append(torch.tensor(features, dtype=torch.float32))
            node_data_by_type[ntype].append(neo4j_to_dgl_id[node['node_id']])

        # Pad and stack features into tensors per node type
        node_features = {
            ntype: torch.stack(feature_data_by_type[ntype])
            for ntype in self.NODE_TYPES if feature_data_by_type[ntype]
        }

        # 3. Prepare Edges for DGL
        canonical_etypes = {}
        for row in rels_data:
            src_type = row['source_type']
            rel_type = row['rel_type']
            dst_type = row['dest_type']
            
            # DGL canonical edge type: (source_node_type, edge_type, dest_node_type)
            canonical_etype = (src_type, rel_type, dst_type)

            if canonical_etype not in canonical_etypes:
                canonical_etypes[canonical_etype] = []

            # Map Neo4j IDs to DGL IDs
            src_dgl_id = neo44j_to_dgl_id[row['source_id']]
            dst_dgl_id = neo44j_to_dgl_id[row['dest_id']]
            
            canonical_etypes[canonical_etype].append((src_dgl_id, dst_dgl_id))

        # Convert edge lists to DGL format (source indices, destination indices)
        data_dict = {}
        for etype, edges in canonical_etypes.items():
            if edges:
                src_ids = torch.tensor([e[0] for e in edges])
                dst_ids = torch.tensor([e[1] for e in edges])
                data_dict[etype] = (src_ids, dst_ids)
        
        # 4. Construct Heterogeneous DGL Graph
        if not data_dict:
            raise ValueError("No relationships found to build the DGL Graph.")

        graph = dgl.heterograph(data_dict)
        
        # 5. Assign Node Features to the DGL Graph
        for ntype, features in node_features.items():
            graph.ndata['feat'] = features
        
        return graph

# Example of use within a Django/Celery Task:
# def train_gnn_model():
#     loader = GRCGraphLoader()
#     try:
#         graph = loader.load_dgl_heterogeneous_graph()
#         # Now 'graph' is ready for GNN training (Step 3.3.3)
#         print(f"Loaded DGL Graph: {graph}")
#         # GNN Training Logic would go here
#     finally:
#         loader.close()
