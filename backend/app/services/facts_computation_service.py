"""
Phase 2.3 Facts Computation Service
"""
import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.facts_config import facts_config
from app.models.far_request import FarRequest
from app.models.far_rule import FarRule
from app.utils.ip_classification import analyze_cidrs, cidrs_overlap
from app.services.asset_service import AssetService
from app.services.tuple_generation_service import TupleGenerationService

logger = logging.getLogger(__name__)


class FactsComputationService:
    """Service for computing policy-independent facts for FAR rules"""
    
    def __init__(self, db: Session):
        self.db = db
        self.asset_service = AssetService(db)
        self.tuple_service = TupleGenerationService()
    
    async def compute_facts_for_request(self, request_id: int) -> Dict[str, Any]:
        """
        Compute facts for all rules in a given request
        
        Args:
            request_id: ID of the FAR request
            
        Returns:
            Dict containing computation statistics and results
        """
        start_time = time.time()
        
        # Verify request exists
        far_request = self.db.query(FarRequest).filter(FarRequest.id == request_id).first()
        if not far_request:
            raise ValueError(f"Request {request_id} not found")
        
        # Check if request has rules
        rules_count = self.db.query(FarRule).filter(FarRule.request_id == request_id).count()
        if rules_count == 0:
            raise ValueError(f"Request {request_id} has no rules - run ingestion first")
        
        logger.info(f"Computing facts for request {request_id} with {rules_count} rules")
        
        # Initialize statistics
        stats = {
            'request_id': request_id,
            'rules_total': rules_count,
            'rules_updated': 0,
            'self_flow_count': 0,
            'src_any': 0,
            'dst_any': 0,
            'public_src': 0,
            'public_dst': 0,
            'duration_ms': 0
        }
        
        # Get rule IDs in batches to avoid memory issues
        rule_ids = self._get_rule_ids_for_request(request_id)
        
        # Pre-compute expensive SQL queries
        self_flow_rule_ids = self._find_self_flow_rules(request_id)
        src_any_rule_ids = self._find_any_rules(request_id, 'source')
        dst_any_rule_ids = self._find_any_rules(request_id, 'destination')
        
        # Process rules in batches
        batch_size = facts_config.FACTS_BATCH_SIZE
        for i in range(0, len(rule_ids), batch_size):
            batch_rule_ids = rule_ids[i:i + batch_size]
            try:
                await self._process_rule_batch(
                    batch_rule_ids, 
                    self_flow_rule_ids, 
                    src_any_rule_ids, 
                    dst_any_rule_ids, 
                    stats
                )
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                # Continue with next batch
                continue
        
        # Update statistics
        stats['duration_ms'] = int((time.time() - start_time) * 1000)
        stats['self_flow_count'] = len(self_flow_rule_ids)
        stats['src_any'] = len(src_any_rule_ids)
        stats['dst_any'] = len(dst_any_rule_ids)
        
        logger.info(f"Facts computation completed for request {request_id}: {stats}")
        return stats
    
    def _get_rule_ids_for_request(self, request_id: int) -> List[int]:
        """Get all rule IDs for a request"""
        result = self.db.execute(
            text("SELECT id FROM far_rules WHERE request_id = :request_id ORDER BY id"),
            {"request_id": request_id}
        )
        return [row[0] for row in result.fetchall()]
    
    def _find_self_flow_rules(self, request_id: int) -> set:
        """Find rules where source and destination CIDRs overlap (excluding 0.0.0.0/0 false positives)"""
        query = text("""
            SELECT DISTINCT r.id
            FROM far_rules r
            JOIN far_rule_endpoints s ON s.rule_id = r.id AND s.endpoint_type = 'source'
            JOIN far_rule_endpoints d ON d.rule_id = r.id AND d.endpoint_type = 'destination'
            WHERE r.request_id = :request_id
              AND s.network_cidr::inet && d.network_cidr::inet
              AND NOT (s.network_cidr = '0.0.0.0/0' AND d.network_cidr != '0.0.0.0/0')
              AND NOT (s.network_cidr != '0.0.0.0/0' AND d.network_cidr = '0.0.0.0/0')
        """)
        
        result = self.db.execute(query, {"request_id": request_id})
        return {row[0] for row in result.fetchall()}
    
    def _find_any_rules(self, request_id: int, endpoint_type: str) -> set:
        """Find rules with 0.0.0.0/0 (any) in source or destination"""
        query = text("""
            SELECT DISTINCT r.id
            FROM far_rules r
            JOIN far_rule_endpoints e ON e.rule_id = r.id
            WHERE r.request_id = :request_id
              AND e.endpoint_type = :endpoint_type
              AND e.network_cidr = '0.0.0.0/0'
        """)
        
        result = self.db.execute(query, {
            "request_id": request_id,
            "endpoint_type": endpoint_type
        })
        return {row[0] for row in result.fetchall()}
    
    async def _process_rule_batch(
        self, 
        rule_ids: List[int], 
        self_flow_rule_ids: set,
        src_any_rule_ids: set,
        dst_any_rule_ids: set,
        stats: Dict[str, Any]
    ):
        """Process a batch of rules and compute their facts"""
        
        for rule_id in rule_ids:
            # Process each rule with proper transaction handling
            try:
                # Get rule data
                rule_data = self._get_rule_data(rule_id)
                if not rule_data:
                    continue
                
                # Compute facts
                facts = await self._compute_rule_facts(
                    rule_id,
                    rule_data,
                    self_flow_rule_ids,
                    src_any_rule_ids,
                    dst_any_rule_ids
                )
                
                # Update rule with facts
                self._update_rule_facts(rule_id, facts)
                
                # Update statistics only after successful processing
                stats['rules_updated'] += 1
                if facts.get('src_has_public', False):
                    stats['public_src'] += 1
                if facts.get('dst_has_public', False):
                    stats['public_dst'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing rule {rule_id}: {e}")
                # Rollback any failed changes
                try:
                    self.db.rollback()
                except Exception as rollback_error:
                    logger.warning(f"Error during rollback for rule {rule_id}: {rollback_error}")
                continue
        
        # Commit all successful updates at the end
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            self.db.rollback()
            raise
    
    def _get_rule_data(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """Get rule endpoints and services"""
        
        # Get endpoints
        endpoints_query = text("""
            SELECT endpoint_type, network_cidr
            FROM far_rule_endpoints
            WHERE rule_id = :rule_id
        """)
        endpoints_result = self.db.execute(endpoints_query, {"rule_id": rule_id})
        
        sources = []
        destinations = []
        for row in endpoints_result:
            if row[0] == 'source':
                sources.append(row[1])
            elif row[0] == 'destination':
                destinations.append(row[1])
        
        # Get services count
        services_query = text("""
            SELECT COUNT(s.id) as service_count
            FROM far_rule_services s
            WHERE s.rule_id = :rule_id
        """)
        services_result = self.db.execute(services_query, {"rule_id": rule_id}).fetchone()
        service_count = services_result[0] if services_result else 0
        
        # Calculate tuple estimate
        tuple_estimate = len(sources) * len(destinations) * max(service_count, 1)
        
        return {
            'sources': sources,
            'destinations': destinations,
            'service_count': service_count,
            'max_port_span': 1,  # Default value, can be enhanced later
            'tuple_estimate': tuple_estimate
        }
    
    async def _compute_rule_facts(
        self, 
        rule_id: int,
        rule_data: Dict[str, Any],
        self_flow_rule_ids: set,
        src_any_rule_ids: set,
        dst_any_rule_ids: set
    ) -> Dict[str, Any]:
        """Compute facts for a single rule"""
        
        sources = rule_data['sources']
        destinations = rule_data['destinations']
        
        # Analyze source and destination CIDRs
        src_analysis = analyze_cidrs(sources)
        dst_analysis = analyze_cidrs(destinations)
        
        # Check for self-flow (more precise check if needed)
        is_self_flow = rule_id in self_flow_rule_ids
        if not is_self_flow and sources and destinations:
            # Double-check with Python if SQL missed some cases
            for src in sources:
                for dst in destinations:
                    if cidrs_overlap(src, dst):
                        is_self_flow = True
                        break
                if is_self_flow:
                    break
        
        # Compute expansion capped flag
        tuple_estimate = rule_data.get('tuple_estimate', 0)
        expansion_capped = tuple_estimate > facts_config.MAX_TUPLE_ESTIMATE_CAP
        
        return {
            'src_is_any': rule_id in src_any_rule_ids,
            'dst_is_any': rule_id in dst_any_rule_ids,
            'is_self_flow': is_self_flow,
            'src_has_public': src_analysis['has_public'],
            'dst_has_public': dst_analysis['has_public'],
            'src_has_broadcast': src_analysis['has_broadcast'],
            'dst_has_broadcast': dst_analysis['has_broadcast'],
            'src_has_multicast': src_analysis['has_multicast'],
            'dst_has_multicast': dst_analysis['has_multicast'],
            'src_has_link_local': src_analysis['has_link_local'],
            'dst_has_link_local': dst_analysis['has_link_local'],
            'src_has_loopback': src_analysis['has_loopback'],
            'dst_has_loopback': dst_analysis['has_loopback'],
            'service_count': rule_data.get('service_count', 0),
            'max_port_span': rule_data.get('max_port_span', 0),
            'tuple_estimate': tuple_estimate,
            'expansion_capped': expansion_capped
        }
    
    def _update_rule_facts(self, rule_id: int, facts: Dict[str, Any]):
        """Update rule with computed facts"""
        update_query = text("""
            UPDATE far_rules 
            SET facts = :facts_json
            WHERE id = :rule_id
        """)
        
        self.db.execute(update_query, {
            "rule_id": rule_id,
            "facts_json": json.dumps(facts)
        })
