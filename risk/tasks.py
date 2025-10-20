from celery import shared_task
import logging
from neomodel.exceptions import DoesNotExist
from risk.nlp_service import NLPEmbeddingService

# Import PostgreSQL Models and Neo4j Models from their respective locations
from governance.models import Policy
from risk.models import Risk
from governance.graph_models import PolicyNode, RiskNode 
# Note: You should update risk.graph_models if you follow best practices and separate graph models

logger = logging.getLogger(__name__)

@shared_task(bind=True, default_retry_delay=300, max_retries=3)
def process_text_embedding(self, entity_type: str, entity_pk: str, text_content: str):
    """
    Generates BERT embeddings for the given text and updates the corresponding Neo4j node.
    
    Args:
        entity_type (str): The type of entity ('policy' or 'risk').
        entity_pk (str): The UUID of the entity from PostgreSQL.
        text_content (str): The text content (title + description) to embed.
    """
    try:
        if not text_content:
            logger.warning(f"Skipping embedding for {entity_type} {entity_pk}: No text content.")
            return

        # 1. Generate Embedding
        embedding_vector = NLPEmbeddingService.get_embedding(text_content)
        
        # 2. Find and Update Neo4j Node
        if entity_type == 'policy':
            NodeClass = PolicyNode
        elif entity_type == 'risk':
            NodeClass = RiskNode
        else:
            logger.error(f"Unknown entity type: {entity_type}")
            return

        node = NodeClass.nodes.get(uid=entity_pk)
        
        # Update the dedicated embedding property
        node.description_embedding = embedding_vector
        node.save()
        
        logger.info(f"Successfully updated Neo4j {entity_type} {entity_pk} with {len(embedding_vector)}-dim embedding.")

    except DoesNotExist:
        logger.error(f"Neo4j Node for {entity_type} {entity_pk} not found. Retrying in 5 mins.")
        raise self.retry() # Retry mechanism for temporary Neo4j connection issues or delayed signal processing
    except Exception as exc:
        logger.error(f"Error processing embedding for {entity_type} {entity_pk}: {exc}")
        # Use exponential backoff or similar strategy for retries on transient errors
        raise self.retry(exc=exc)
