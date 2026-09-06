from sqlalchemy.orm import Session
from app.models.knowledge_gap import KnowledgeGap
from app.models.ticket import Ticket
import logging

logger = logging.getLogger(__name__)

class KnowledgeGapService:
    @staticmethod
    def record_gap(db: Session, ticket: Ticket):
        """
        Records a knowledge gap when a ticket is escalated.
        For simplicity in this prototype, we use the ticket's title/category as the topic.
        In a production system, this could use an LLM to group semantic topics.
        """
        try:
            topic = ticket.title if ticket.title else "Unknown IT Issue"
            
            # Simple exact match for grouping, a real system would use embeddings
            existing_gap = db.query(KnowledgeGap).filter(
                KnowledgeGap.company_id == ticket.company_id,
                KnowledgeGap.topic == topic,
                KnowledgeGap.status.in_(["OPEN", "UNDER_REVIEW"])
            ).first()

            if existing_gap:
                existing_gap.occurrence_count += 1
                db.commit()
                logger.info(f"Incremented Knowledge Gap for topic: {topic}")
            else:
                new_gap = KnowledgeGap(
                    company_id=ticket.company_id,
                    topic=topic,
                    description=ticket.description,
                    occurrence_count=1,
                    example_ticket_id=ticket.id,
                    status="OPEN"
                )
                db.add(new_gap)
                db.commit()
                logger.info(f"Created new Knowledge Gap for topic: {topic}")
        except Exception as e:
            logger.error(f"Failed to record knowledge gap: {e}")
            db.rollback()
