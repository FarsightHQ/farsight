"""
Hybrid Facts Computation Service - Option 2: Selective Storage
Stores core facts for all tuples + additional facts only when they differ from rule-level facts
"""
import json
import time
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base
from app.models.far_request import FarRequest
from app.models.far_rule import FarRule
from app.models.far_tuple_facts import FarTupleFacts
from app.utils.ip_classification import (
    analyze_cidrs, cidrs_overlap, overlaps_multicast, 
    is_public_ip, is_rfc1918, is_any_network, is_broadcast,
    is_link_local, is_loopback
)

logger = logging.getLogger(__name__)


class HybridFactsService:
    """Service for computing hybrid facts with selective tuple storage"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def compute_hybrid_facts_for_request(self, request_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Compute hybrid facts for a request with selective tuple storage
        
        Args:
            request_data: Dict containing source_cidrs, destination_cidrs, port_ranges, protocols
            db: Database session
            
        Returns:
            Dict containing rule_facts and summary information
        """
        try:
            # Extract request parameters
            source_cidrs = request_data.get('source_cidrs', [])
            destination_cidrs = request_data.get('destination_cidrs', [])
            port_ranges = request_data.get('port_ranges', [])
            protocols = request_data.get('protocols', [])
            
            # Find matching rules
            matching_rules = self._find_matching_rules(
                source_cidrs, destination_cidrs, port_ranges, protocols, db
            )
            
            result = {
                'rule_facts': [],
                'total_rules': len(matching_rules),
                'computation_time': time.time()
            }
            
            # Process each matching rule
            for rule in matching_rules:
                rule_facts = await self._process_rule_hybrid_facts(
                    rule, source_cidrs, destination_cidrs, db
                )
                result['rule_facts'].append(rule_facts)
            
            # Commit all changes at once
            db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error computing hybrid facts: {e}")
            db.rollback()
            raise
    
    def _find_matching_rules(self, source_cidrs: List[str], destination_cidrs: List[str], 
                           port_ranges: List[str], protocols: List[str], db: Session) -> List[FarRule]:
        """Find rules that match the given criteria"""
        try:
            # Get all rules with their endpoints eagerly loaded
            from sqlalchemy.orm import joinedload
            rules = db.query(FarRule).options(joinedload(FarRule.endpoints)).all()
            matching_rules = []
            
            for rule in rules:
                # Check if rule overlaps with request parameters by examining endpoints
                if self._rule_overlaps_with_request(rule, source_cidrs, destination_cidrs, db):
                    matching_rules.append(rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"Error finding matching rules: {e}")
            return []
    
    def _rule_overlaps_with_request(self, rule: FarRule, source_cidrs: List[str], 
                                  destination_cidrs: List[str], db: Session) -> bool:
        """Check if a rule overlaps with request parameters"""
        try:
            # Get actual endpoints from the database
            from app.models.far_rule import FarRuleEndpoint
            endpoints = db.query(FarRuleEndpoint).filter(FarRuleEndpoint.rule_id == rule.id).all()
            
            rule_sources = [ep.network_cidr for ep in endpoints if ep.endpoint_type == 'source']
            rule_destinations = [ep.network_cidr for ep in endpoints if ep.endpoint_type == 'destination']
            
            # Simple overlap check - if any requested CIDR matches any rule CIDR
            # In production, this would use proper CIDR overlap logic
            source_overlap = any(req_src in rule_sources for req_src in source_cidrs)
            dest_overlap = any(req_dst in rule_destinations for req_dst in destination_cidrs)
            
            return source_overlap and dest_overlap
            
        except Exception as e:
            logger.error(f"Error checking rule overlap: {e}")
            return False
    
    async def _process_rule_hybrid_facts(self, rule: FarRule, source_cidrs: List[str], 
                                       destination_cidrs: List[str], db: Session) -> Dict[str, Any]:
        """Process hybrid facts for a specific rule"""
        try:
            # Generate all possible tuples for this rule
            rule_tuples = self._generate_rule_tuples(rule, source_cidrs, destination_cidrs)
            
            # Compute facts for each tuple
            tuple_facts = []
            rule_level_facts = {}
            
            for src_cidr, dst_cidr in rule_tuples:
                tuple_fact = await self._compute_individual_tuple_facts(src_cidr, dst_cidr, rule)
                tuple_facts.append({
                    'source_cidr': src_cidr,
                    'destination_cidr': dst_cidr,
                    'facts': tuple_fact
                })
            
            # Aggregate rule-level facts
            rule_level_facts = self._aggregate_rule_level_facts(tuple_facts)
            
            # Store selective tuple facts
            await self._store_selective_tuple_facts(rule, tuple_facts, rule_level_facts, db)
            
            # Update rule with aggregated facts (don't commit here, let the caller handle it)
            rule.facts = rule_level_facts
            
            return {
                'rule_id': rule.id,
                'facts': rule_level_facts,
                'tuple_count': len(tuple_facts),
                'selective_tuples_stored': await self._count_selective_tuples(rule.id, db)
            }
            
        except Exception as e:
            logger.error(f"Error processing rule hybrid facts: {e}")
            raise
    
    def _generate_rule_tuples(self, rule: FarRule, source_cidrs: List[str], 
                            destination_cidrs: List[str]) -> List[tuple]:
        """Generate all tuples (source, destination) for the rule"""
        try:
            # Get rule's source and destination CIDRs from endpoints
            rule_sources = []
            rule_destinations = []
            
            # Add safety check and logging
            logger.info(f"Processing rule {rule.id}, has {len(rule.endpoints)} endpoints")
            
            for endpoint in rule.endpoints:
                if endpoint.endpoint_type == 'source':
                    rule_sources.append(endpoint.network_cidr)
                elif endpoint.endpoint_type == 'destination':
                    rule_destinations.append(endpoint.network_cidr)
            
            logger.info(f"Rule {rule.id}: {len(rule_sources)} sources, {len(rule_destinations)} destinations")
            
            # Find overlapping CIDRs
            overlapping_sources = []
            overlapping_destinations = []
            
            for req_src in source_cidrs:
                for rule_src in rule_sources:
                    if cidrs_overlap(req_src, rule_src):
                        overlapping_sources.append(req_src)
                        break
            
            for req_dst in destination_cidrs:
                for rule_dst in rule_destinations:
                    if cidrs_overlap(req_dst, rule_dst):
                        overlapping_destinations.append(req_dst)
                        break
            
            # Generate cartesian product
            tuples = []
            for src in overlapping_sources:
                for dst in overlapping_destinations:
                    tuples.append((src, dst))
            
            logger.info(f"Rule {rule.id}: Generated {len(tuples)} tuples")
            return tuples
            
        except Exception as e:
            logger.error(f"Error generating rule tuples for rule {rule.id}: {e}")
            return []
    
    async def _compute_individual_tuple_facts(self, source_cidr: str, destination_cidr: str, 
                                            rule: FarRule) -> Dict[str, Any]:
        """Compute facts for an individual tuple"""
        try:
            facts = {}
            
            # Source analysis
            source_analysis = analyze_cidrs([source_cidr])
            facts['source_is_private'] = is_rfc1918(source_cidr)
            facts['source_is_public'] = is_public_ip(source_cidr)
            facts['source_is_multicast'] = overlaps_multicast(source_cidr)
            
            # Destination analysis  
            destination_analysis = analyze_cidrs([destination_cidr])
            facts['destination_is_private'] = is_rfc1918(destination_cidr)
            facts['destination_is_public'] = is_public_ip(destination_cidr)
            facts['destination_is_multicast'] = overlaps_multicast(destination_cidr)
            
            # Security analysis (simplified for demonstration)
            facts['has_security_issues'] = self._check_security_issues(source_cidr, destination_cidr)
            facts['risk_level'] = self._assess_risk_level(source_cidr, destination_cidr)
            
            # Traffic analysis
            facts['traffic_type'] = self._classify_traffic_type(source_cidr, destination_cidr)
            
            return facts
            
        except Exception as e:
            logger.error(f"Error computing tuple facts: {e}")
            return {}
    
    def _check_security_issues(self, source_cidr: str, destination_cidr: str) -> bool:
        """Check for security issues in the tuple"""
        try:
            # Example security checks
            # In practice, this would check against threat intelligence, etc.
            
            # Check for suspicious patterns
            if "203.0.113" in destination_cidr:  # TEST-NET-3, simulate malicious
                return True
            
            if is_any_network(source_cidr) or is_any_network(destination_cidr):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking security issues: {e}")
            return False
    
    def _assess_risk_level(self, source_cidr: str, destination_cidr: str) -> str:
        """Assess risk level for the tuple"""
        try:
            if self._check_security_issues(source_cidr, destination_cidr):
                return "high"
            
            if is_public_ip(source_cidr) and is_public_ip(destination_cidr):
                return "medium"
            
            return "low"
            
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "unknown"
    
    def _classify_traffic_type(self, source_cidr: str, destination_cidr: str) -> str:
        """Classify the type of traffic"""
        try:
            if is_rfc1918(source_cidr) and is_rfc1918(destination_cidr):
                return "internal"
            elif is_rfc1918(source_cidr) and is_public_ip(destination_cidr):
                return "outbound"
            elif is_public_ip(source_cidr) and is_rfc1918(destination_cidr):
                return "inbound"
            else:
                return "external"
                
        except Exception as e:
            logger.error(f"Error classifying traffic type: {e}")
            return "unknown"
    
    def _aggregate_rule_level_facts(self, tuple_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate facts across all tuples in the rule"""
        try:
            if not tuple_facts:
                return {}
            
            aggregated = {
                'total_tuples': len(tuple_facts),
                'has_any_security_issues': False,
                'risk_levels': {'low': 0, 'medium': 0, 'high': 0},
                'traffic_types': {},
                'source_types': {'private': 0, 'public': 0},
                'destination_types': {'private': 0, 'public': 0}
            }
            
            for tuple_data in tuple_facts:
                facts = tuple_data['facts']
                
                # Security aggregation
                if facts.get('has_security_issues', False):
                    aggregated['has_any_security_issues'] = True
                
                # Risk level aggregation
                risk_level = facts.get('risk_level', 'low')
                aggregated['risk_levels'][risk_level] = aggregated['risk_levels'].get(risk_level, 0) + 1
                
                # Traffic type aggregation
                traffic_type = facts.get('traffic_type', 'unknown')
                aggregated['traffic_types'][traffic_type] = aggregated['traffic_types'].get(traffic_type, 0) + 1
                
                # Source/destination type aggregation
                if facts.get('source_is_private', False):
                    aggregated['source_types']['private'] += 1
                elif facts.get('source_is_public', False):
                    aggregated['source_types']['public'] += 1
                
                if facts.get('destination_is_private', False):
                    aggregated['destination_types']['private'] += 1
                elif facts.get('destination_is_public', False):
                    aggregated['destination_types']['public'] += 1
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating rule-level facts: {e}")
            return {}
    
    async def _store_selective_tuple_facts(self, rule: FarRule, tuple_facts: List[Dict[str, Any]], 
                                         rule_level_facts: Dict[str, Any], db: Session):
        """Store only tuple facts that differ from rule-level patterns"""
        try:
            # Only try to delete if there might be existing data
            # Check if there are any existing tuple facts for this rule first
            existing_count = db.query(FarTupleFacts).filter_by(rule_id=rule.id).count()
            if existing_count > 0:
                db.query(FarTupleFacts).filter_by(rule_id=rule.id).delete()
            
            for tuple_data in tuple_facts:
                source_cidr = tuple_data['source_cidr']
                destination_cidr = tuple_data['destination_cidr']
                facts = tuple_data['facts']
                
                # Check if this tuple needs selective storage
                if self._should_store_selective_facts(facts, rule_level_facts):
                    tuple_fact_record = FarTupleFacts(
                        rule_id=rule.id,
                        source_cidr=source_cidr,
                        destination_cidr=destination_cidr,
                        facts=facts
                    )
                    db.add(tuple_fact_record)
            
            # Don't commit here, let the caller handle it
            
        except Exception as e:
            logger.error(f"Error storing selective tuple facts: {e}")
            raise
    
    def _should_store_selective_facts(self, tuple_facts: Dict[str, Any], 
                                    rule_level_facts: Dict[str, Any]) -> bool:
        """Determine if tuple facts should be stored selectively"""
        try:
            # Store if tuple has security issues when rule doesn't indicate universal issues
            if tuple_facts.get('has_security_issues', False):
                return True
            
            # Store if risk level is different from most common in rule
            tuple_risk = tuple_facts.get('risk_level', 'low')
            rule_risk_levels = rule_level_facts.get('risk_levels', {})
            most_common_risk = max(rule_risk_levels.items(), key=lambda x: x[1])[0] if rule_risk_levels else 'low'
            
            if tuple_risk != most_common_risk:
                return True
            
            # Store if traffic type is unusual for the rule
            tuple_traffic = tuple_facts.get('traffic_type', 'unknown')
            rule_traffic_types = rule_level_facts.get('traffic_types', {})
            total_tuples = rule_level_facts.get('total_tuples', 1)
            
            # If this traffic type represents less than 50% of rule's traffic, store it
            traffic_count = rule_traffic_types.get(tuple_traffic, 0)
            if traffic_count < (total_tuples * 0.5):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining selective storage: {e}")
            return False
    
    async def _count_selective_tuples(self, rule_id: int, db: Session) -> int:
        """Count stored selective tuple facts for a rule"""
        try:
            count = db.query(FarTupleFacts).filter_by(rule_id=rule_id).count()
            return count
            
        except Exception as e:
            logger.error(f"Error counting selective tuples: {e}")
            return 0
    
    async def get_rule_hybrid_summary(self, rule_id: int, db: Session) -> Dict[str, Any]:
        """Get hybrid facts summary for a specific rule"""
        try:
            rule = db.query(FarRule).filter_by(id=rule_id).first()
            if not rule:
                return {'error': 'Rule not found'}
            
            # Get selective tuple facts
            selective_tuples = db.query(FarTupleFacts).filter_by(rule_id=rule_id).all()
            
            return {
                'rule_id': rule_id,
                'rule_facts': rule.facts or {},
                'selective_tuple_count': len(selective_tuples),
                'selective_tuples': [
                    {
                        'source_cidr': t.source_cidr,
                        'destination_cidr': t.destination_cidr,
                        'facts': t.facts
                    }
                    for t in selective_tuples
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting rule hybrid summary: {e}")
            return {'error': str(e)}
    
    async def get_problematic_tuples(self, db: Session, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tuples with security issues from selective storage"""
        try:
            # Query tuples with security issues
            problematic_tuples = db.query(FarTupleFacts).filter(
                FarTupleFacts.facts['has_security_issues'].astext.cast(db.Boolean) == True
            ).limit(limit).all()
            
            return [
                {
                    'rule_id': t.rule_id,
                    'source_cidr': t.source_cidr,
                    'destination_cidr': t.destination_cidr,
                    'facts': t.facts,
                    'created_at': t.created_at.isoformat() if t.created_at else None
                }
                for t in problematic_tuples
            ]
            
        except Exception as e:
            logger.error(f"Error getting problematic tuples: {e}")
            return []
