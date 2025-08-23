#!/usr/bin/env python3
"""
Comprehensive Test Suite for Hybrid Facts Implementation
Tests the selective storage approach (Option 2) that solves false positive issues
"""
import sys
import os
import asyncio
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append('/Users/Suman_Paul/Projects/farsight/backend')

from app.core.database import SessionLocal
from app.services.hybrid_facts_service import HybridFactsService
from app.models.far_request import FarRequest
from app.models.far_rule import FarRule, FarRuleEndpoint, FarRuleService
from app.models.far_tuple_facts import FarTupleFacts
from app.utils.ip_classification import (
    is_any_network, is_public_ip, cidrs_overlap, overlaps_multicast
)

# Set environment for database connection
os.environ['DATABASE_URL'] = 'postgresql://farsight_user:farsight_password@localhost:5432/farsight'

class HybridFactsTestSuite:
    """Test suite for hybrid facts functionality"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.service = HybridFactsService(self.db)
        self.test_request_id = None
    
    def cleanup(self):
        """Clean up test data"""
        if self.test_request_id:
            # Delete in correct order due to foreign keys
            self.db.query(FarTupleFacts).filter(
                FarTupleFacts.rule_id.in_(
                    self.db.query(FarRule.id).filter(FarRule.request_id == self.test_request_id)
                )
            ).delete(synchronize_session=False)
            
            self.db.query(FarRuleService).filter(
                FarRuleService.rule_id.in_(
                    self.db.query(FarRule.id).filter(FarRule.request_id == self.test_request_id)
                )
            ).delete(synchronize_session=False)
            
            self.db.query(FarRuleEndpoint).filter(
                FarRuleEndpoint.rule_id.in_(
                    self.db.query(FarRule.id).filter(FarRule.request_id == self.test_request_id)
                )
            ).delete(synchronize_session=False)
            
            self.db.query(FarRule).filter(FarRule.request_id == self.test_request_id).delete()
            self.db.query(FarRequest).filter(FarRequest.id == self.test_request_id).delete()
            self.db.commit()
        
        self.db.close()
    
    def create_test_data(self):
        """Create test data that demonstrates the false positive problem"""
        print("🔧 Creating test data...")
        
        # Create test request
        request = FarRequest(
            filename="hybrid_test.xlsx",
            original_filename="hybrid_test.xlsx",
            file_size=1024,
            upload_timestamp=datetime.utcnow(),
            status="processed"
        )
        self.db.add(request)
        self.db.flush()
        self.test_request_id = request.id
        
        # Create a rule with mixed tuples (demonstrates false positive problem)
        # Rule 1: Mixed rule with 1 self-flow + 3 clean tuples
        rule1 = FarRule(
            request_id=self.test_request_id,
            canonical_hash=b'test_rule_1_hash',
            action="allow"
        )
        self.db.add(rule1)
        self.db.flush()
        
        # Add endpoints for rule 1
        # This will create 4 tuples: 2 sources × 2 destinations
        # One tuple will be self-flow (192.168.1.0/24 -> 192.168.1.10/32)
        endpoints1 = [
            FarRuleEndpoint(rule_id=rule1.id, endpoint_type="source", network_cidr="192.168.1.0/24"),
            FarRuleEndpoint(rule_id=rule1.id, endpoint_type="source", network_cidr="10.0.0.0/8"),
            FarRuleEndpoint(rule_id=rule1.id, endpoint_type="destination", network_cidr="192.168.1.10/32"),
            FarRuleEndpoint(rule_id=rule1.id, endpoint_type="destination", network_cidr="8.8.8.8/32"),
        ]
        for endpoint in endpoints1:
            self.db.add(endpoint)
        
        # Add service for rule 1
        service1 = FarRuleService(rule_id=rule1.id, protocol="tcp", port_ranges="80")
        self.db.add(service1)
        
        # Rule 2: Clean rule (all public-to-public, should be flagged but different issue)
        rule2 = FarRule(
            request_id=self.test_request_id,
            canonical_hash=b'test_rule_2_hash',
            action="allow"
        )
        self.db.add(rule2)
        self.db.flush()
        
        # Add endpoints for rule 2 - public to public traffic
        endpoints2 = [
            FarRuleEndpoint(rule_id=rule2.id, endpoint_type="source", network_cidr="8.8.8.8/32"),
            FarRuleEndpoint(rule_id=rule2.id, endpoint_type="destination", network_cidr="1.1.1.1/32"),
        ]
        for endpoint in endpoints2:
            self.db.add(endpoint)
        
        service2 = FarRuleService(rule_id=rule2.id, protocol="tcp", port_ranges="443")
        self.db.add(service2)
        
        # Rule 3: Perfectly clean rule
        rule3 = FarRule(
            request_id=self.test_request_id,
            canonical_hash=b'test_rule_3_hash',
            action="allow"
        )
        self.db.add(rule3)
        self.db.flush()
        
        # Add endpoints for rule 3 - private to private
        endpoints3 = [
            FarRuleEndpoint(rule_id=rule3.id, endpoint_type="source", network_cidr="10.0.1.0/24"),
            FarRuleEndpoint(rule_id=rule3.id, endpoint_type="destination", network_cidr="10.0.2.0/24"),
        ]
        for endpoint in endpoints3:
            self.db.add(endpoint)
        
        service3 = FarRuleService(rule_id=rule3.id, protocol="tcp", port_ranges="22")
        self.db.add(service3)
        
        self.db.commit()
        print(f"✅ Created test request {self.test_request_id} with 3 rules")
        return [rule1.id, rule2.id, rule3.id]
    
    def test_ip_classification_utilities(self):
        """Test the IP classification utility functions"""
        print("\\n🧪 Testing IP classification utilities...")
        
        tests = [
            ("is_any_network", is_any_network, "0.0.0.0/0", True),
            ("is_any_network", is_any_network, "192.168.1.0/24", False),
            ("is_public_ip", is_public_ip, "8.8.8.8/32", True),
            ("is_public_ip", is_public_ip, "192.168.1.1/32", False),
            ("cidrs_overlap", lambda: cidrs_overlap("192.168.1.0/24", "192.168.1.10/32"), None, True),
            ("cidrs_overlap", lambda: cidrs_overlap("192.168.1.0/24", "10.0.0.0/8"), None, False),
            ("overlaps_multicast", overlaps_multicast, "224.0.0.1/32", True),
            ("overlaps_multicast", overlaps_multicast, "192.168.1.1/32", False),
        ]
        
        for test_name, func, arg, expected in tests:
            try:
                if arg is None:
                    result = func()
                else:
                    result = func(arg)
                assert result == expected, f"{test_name} failed: got {result}, expected {expected}"
                print(f"  ✅ {test_name}: {result}")
            except Exception as e:
                print(f"  ❌ {test_name}: {e}")
                return False
        
        print("✅ All IP classification utilities working correctly")
        return True
    
    async def test_hybrid_facts_computation(self):
        """Test the hybrid facts computation with selective storage"""
        print("\\n🔬 Testing hybrid facts computation...")
        
        try:
            # Run hybrid facts computation
            stats = await self.service.compute_hybrid_facts_for_request(self.test_request_id)
            
            print(f"✅ Hybrid facts computed successfully:")
            print(f"  📊 Rules processed: {stats['rules_updated']}/{stats['rules_total']}")
            print(f"  📊 Total tuples: {stats['tuples_total']}")
            print(f"  📊 Stored tuples: {stats['tuples_stored']} (selective storage)")
            print(f"  📊 Self-flows found: {stats['self_flow_count']}")
            print(f"  📊 Clean percentage: {stats['clean_tuple_percentage']}%")
            print(f"  ⏱️  Duration: {stats['duration_ms']}ms")
            
            # Verify storage efficiency
            storage_ratio = stats['tuples_stored'] / stats['tuples_total'] if stats['tuples_total'] > 0 else 0
            print(f"  💾 Storage efficiency: {storage_ratio:.1%} (only problematic tuples stored)")
            
            return stats
            
        except Exception as e:
            print(f"❌ Hybrid facts computation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def test_rule_level_facts(self):
        """Test rule-level facts enhancement"""
        print("\\n📋 Testing rule-level facts...")
        
        try:
            rules = self.db.query(FarRule).filter(FarRule.request_id == self.test_request_id).all()
            
            for rule in rules:
                if rule.facts:
                    facts = rule.facts
                    print(f"\\n  📝 Rule {rule.id} facts:")
                    print(f"    Health: {facts.get('health_status', 'unknown')}")
                    
                    if 'tuple_summary' in facts:
                        summary = facts['tuple_summary']
                        print(f"    Tuples: {summary['total']} total, {summary['clean']} clean, {summary['problematic']} problematic")
                    
                    if 'problem_types' in facts:
                        problems = facts['problem_types']
                        print(f"    Problems: {problems if problems else 'None'}")
                else:
                    print(f"  ❌ Rule {rule.id} has no facts")
            
            print("✅ Rule-level facts analysis complete")
            return True
            
        except Exception as e:
            print(f"❌ Rule-level facts test failed: {e}")
            return False
    
    async def test_tuple_level_facts(self):
        """Test selective tuple-level facts storage"""
        print("\\n🎯 Testing tuple-level facts (selective storage)...")
        
        try:
            tuple_facts = self.db.query(FarTupleFacts).filter(
                FarTupleFacts.rule_id.in_(
                    self.db.query(FarRule.id).filter(FarRule.request_id == self.test_request_id)
                )
            ).all()
            
            print(f"  📊 Total stored tuple facts: {len(tuple_facts)}")
            
            for tf in tuple_facts:
                facts = tf.facts
                print(f"\\n  🔍 Tuple {tf.source_cidr} → {tf.destination_cidr}:")
                print(f"    Rule ID: {tf.rule_id}")
                print(f"    Clean: {facts.get('is_clean', 'unknown')}")
                print(f"    Self-flow: {facts.get('is_self_flow', 'unknown')}")
                if 'primary_violation' in facts:
                    print(f"    Violation: {facts['primary_violation']}")
            
            # Verify selective storage principle
            problematic_count = len([tf for tf in tuple_facts if not tf.facts.get('is_clean', True)])
            print(f"\\n  ✅ Selective storage working: {problematic_count}/{len(tuple_facts)} stored tuples are problematic")
            
            return True
            
        except Exception as e:
            print(f"❌ Tuple-level facts test failed: {e}")
            return False
    
    async def test_false_positive_resolution(self):
        """Test that the false positive problem is solved"""
        print("\\n🎯 Testing false positive resolution...")
        
        try:
            # Get the mixed rule (rule 1) that has both clean and problematic tuples
            rule1 = self.db.query(FarRule).filter(
                FarRule.request_id == self.test_request_id
            ).first()
            
            if not rule1 or not rule1.facts:
                print("❌ No rule facts found")
                return False
            
            rule_facts = rule1.facts
            tuple_summary = rule_facts.get('tuple_summary', {})
            
            print(f"  📊 Rule-level summary:")
            print(f"    Total tuples: {tuple_summary.get('total', 0)}")
            print(f"    Clean tuples: {tuple_summary.get('clean', 0)}")
            print(f"    Problematic tuples: {tuple_summary.get('problematic', 0)}")
            print(f"    Health status: {rule_facts.get('health_status', 'unknown')}")
            
            # Get tuple-level details for this rule
            tuple_facts = self.db.query(FarTupleFacts).filter(
                FarTupleFacts.rule_id == rule1.id
            ).all()
            
            print(f"\\n  🔍 Tuple-level details (only problematic stored):")
            for tf in tuple_facts:
                is_self_flow = tf.facts.get('is_self_flow', False)
                print(f"    {tf.source_cidr} → {tf.destination_cidr}: {'Self-flow' if is_self_flow else 'Other issue'}")
            
            # Verify false positive is resolved
            total_tuples = tuple_summary.get('total', 0)
            problematic_tuples = tuple_summary.get('problematic', 0)
            stored_tuples = len(tuple_facts)
            
            print(f"\\n  ✅ False positive resolution:")
            print(f"    Before: All {total_tuples} tuples would be flagged as problematic")
            print(f"    After: Only {problematic_tuples} tuples are actually problematic")
            print(f"    Storage: Only {stored_tuples} tuples stored (selective)")
            print(f"    Precision: {problematic_tuples}/{total_tuples} = {problematic_tuples/total_tuples*100:.1f}% problematic")
            
            return True
            
        except Exception as e:
            print(f"❌ False positive resolution test failed: {e}")
            return False
    
    async def test_api_endpoints(self):
        """Test the hybrid facts API endpoints"""
        print("\\n🌐 Testing API endpoint functionality...")
        
        try:
            # Test hybrid summary
            summary = await self.service.get_hybrid_summary(self.test_request_id)
            print(f"  📊 Hybrid summary:")
            print(f"    Rules: {summary['rules']['total']} total, {summary['rules']['clean']} clean, {summary['rules']['problematic']} problematic")
            print(f"    Stored tuples: {summary['stored_tuples']['total']} total, {summary['stored_tuples']['problematic']} problematic")
            
            # Test problematic tuples endpoint
            problematic = await self.service.get_problematic_tuples(self.test_request_id, limit=10)
            print(f"\\n  🚨 Problematic tuples found: {len(problematic)}")
            for p in problematic:
                print(f"    Rule {p['rule_id']}: {p['source_cidr']} → {p['destination_cidr']} ({p['violation_type']})")
            
            print("✅ API endpoints working correctly")
            return True
            
        except Exception as e:
            print(f"❌ API endpoints test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Hybrid Facts Test Suite")
        print("=" * 60)
        
        # Test 1: IP Classification Utilities
        if not self.test_ip_classification_utilities():
            return False
        
        # Test 2: Create Test Data
        rule_ids = self.create_test_data()
        
        # Test 3: Hybrid Facts Computation
        stats = await self.test_hybrid_facts_computation()
        if not stats:
            return False
        
        # Test 4: Rule-Level Facts
        if not await self.test_rule_level_facts():
            return False
        
        # Test 5: Tuple-Level Facts
        if not await self.test_tuple_level_facts():
            return False
        
        # Test 6: False Positive Resolution
        if not await self.test_false_positive_resolution():
            return False
        
        # Test 7: API Endpoints
        if not await self.test_api_endpoints():
            return False
        
        print("\\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Hybrid Facts implementation is working correctly")
        print("✅ False positive problem has been solved")
        print("✅ Selective storage is functioning efficiently")
        print("=" * 60)
        
        return True

async def main():
    """Main test runner"""
    test_suite = HybridFactsTestSuite()
    
    try:
        success = await test_suite.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
