"""
CSV parsing and rule ingestion service for Phase 2.2
"""
import csv
import io
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.far_request import FarRequest
from app.models.far_rule import FarRule, FarRuleEndpoint, FarRuleService
from app.utils.ip_port_utils import (
    normalize_ip_address, 
    normalize_port_ranges, 
    compute_canonical_hash,
    NormalizedRule,
    NormalizedEndpoint,
    NormalizedService,
    format_port_ranges_for_postgres
)
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)


class CsvIngestionService:
    """Service for parsing CSV files and creating normalized FAR rules"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def ingest_csv_file(self, request_id: int, file_content: str) -> Dict[str, Any]:
        """
        Ingest CSV file content and create normalized FAR rules
        
        Args:
            request_id: ID of the FAR request
            file_content: CSV file content as string
            
        Returns:
            Dictionary with ingestion statistics and results
        """
        try:
            # Verify the request exists
            far_request = self.db.query(FarRequest).filter(FarRequest.id == request_id).first()
            if not far_request:
                raise ValueError(f"FAR request {request_id} not found")
            
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            # Validate required columns with flexible naming
            fieldnames = csv_reader.fieldnames or []
            
            # Clean up column names (remove BOM and whitespace)
            clean_fieldnames = [col.strip().lstrip('\ufeff') for col in fieldnames]
            
            # Support both singular and plural column names
            source_col = None
            dest_col = None  
            service_col = None
            action_col = None
            direction_col = None
            
            # Find source column
            for i, col in enumerate(clean_fieldnames):
                if col.lower() in ['source', 'sources']:
                    source_col = fieldnames[i]  # Use original column name for data access
                    break
            
            # Find destination column  
            for i, col in enumerate(clean_fieldnames):
                if col.lower() in ['destination', 'destinations']:
                    dest_col = fieldnames[i]  # Use original column name for data access
                    break
                    
            # Find service column
            for i, col in enumerate(clean_fieldnames):
                if col.lower() in ['service', 'services']:
                    service_col = fieldnames[i]  # Use original column name for data access
                    break
                    
            # Find optional action column
            for i, col in enumerate(clean_fieldnames):
                if col.lower() == 'action':
                    action_col = fieldnames[i]  # Use original column name for data access
                    break
                    
            # Find optional direction column
            for i, col in enumerate(clean_fieldnames):
                if col.lower() == 'direction':
                    direction_col = fieldnames[i]  # Use original column name for data access
                    break
            
            # Check required columns
            missing_cols = []
            if not source_col:
                missing_cols.append('source/sources')
            if not dest_col:
                missing_cols.append('destination/destinations') 
            if not service_col:
                missing_cols.append('service/services')
                
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            statistics = {
                'total_rows': 0,
                'processed_rows': 0,
                'skipped_rows': 0,
                'error_rows': 0,
                'created_rules': 0,
                'duplicate_rules': 0,
                'errors': []
            }
            
            processed_hashes = set()
            
            # Store column mappings for use in row parsing
            column_mapping = {
                'source': source_col,
                'destination': dest_col,
                'service': service_col,
                'action': action_col,
                'direction': direction_col
            }
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
                statistics['total_rows'] += 1
                
                try:
                    # Skip empty rows
                    if not any(row.values()):
                        statistics['skipped_rows'] += 1
                        continue
                    
                    # Parse and normalize the rule
                    normalized_rule = self._parse_csv_row(row, column_mapping)
                    canonical_hash = compute_canonical_hash(normalized_rule)
                    
                    # Check for duplicates within this batch
                    if canonical_hash in processed_hashes:
                        statistics['duplicate_rules'] += 1
                        continue
                    
                    # Check for existing rule in database
                    existing_rule = self.db.query(FarRule).filter(
                        FarRule.canonical_hash == canonical_hash
                    ).first()
                    
                    if existing_rule:
                        statistics['duplicate_rules'] += 1
                        continue
                    
                    # Create new rule
                    await self._create_far_rule(
                        request_id=request_id,
                        normalized_rule=normalized_rule,
                        canonical_hash=canonical_hash
                    )
                    
                    processed_hashes.add(canonical_hash)
                    statistics['created_rules'] += 1
                    statistics['processed_rows'] += 1
                    
                except Exception as e:
                    statistics['error_rows'] += 1
                    error_msg = f"Row {row_num}: {str(e)}"
                    statistics['errors'].append(error_msg)
                    logger.warning(error_msg)
                    continue
            
            # Update request status
            far_request.status = 'ingested'
            self.db.commit()
            
            return statistics
            
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"CSV ingestion failed: {str(e)}")
    
    def _parse_csv_row(self, row: Dict[str, str], column_mapping: Dict[str, Optional[str]]) -> NormalizedRule:
        """
        Parse a single CSV row into a normalized rule
        
        Args:
            row: Dictionary representing a CSV row
            column_mapping: Mapping of logical names to actual column names
            
        Returns:
            NormalizedRule object
        """
        # Extract and validate action (default to 'allow' if not present)
        action_col = column_mapping.get('action')
        if action_col and action_col in row:
            action = row[action_col].strip().lower()
        else:
            action = 'allow'  # Default action
            
        if action not in ['allow', 'deny', 'drop', 'reject']:
            logger.warning(f"Unknown action '{action}', defaulting to 'allow'")
            action = 'allow'
        
        # Extract optional direction
        direction_col = column_mapping.get('direction')
        direction = None
        if direction_col and direction_col in row:
            direction = row[direction_col].strip().lower() or None
            if direction and direction not in ['inbound', 'outbound', 'bidirectional']:
                logger.warning(f"Unknown direction '{direction}', ignoring")
                direction = None
        
        # Parse source endpoints
        source_col = column_mapping['source']
        if not source_col:
            raise ValueError("Source column not found")
        source_endpoints = self._parse_endpoints(row.get(source_col, '').strip())
        if not source_endpoints:
            raise ValueError("No valid source endpoints found")
        
        # Parse destination endpoints
        dest_col = column_mapping['destination']
        if not dest_col:
            raise ValueError("Destination column not found")
        destination_endpoints = self._parse_endpoints(row.get(dest_col, '').strip())
        if not destination_endpoints:
            raise ValueError("No valid destination endpoints found")
        
        # Parse services
        service_col = column_mapping['service']
        if not service_col:
            raise ValueError("Service column not found")
        services = self._parse_services(row.get(service_col, '').strip())
        if not services:
            raise ValueError("No valid services found")
        
        return NormalizedRule(
            source_endpoints=source_endpoints,
            destination_endpoints=destination_endpoints,
            services=services,
            action=action,
            direction=direction
        )
    
    def _parse_endpoints(self, endpoints_str: str) -> List[NormalizedEndpoint]:
        """
        Parse endpoint specification into normalized endpoints
        
        Args:
            endpoints_str: Comma-separated endpoint specification
            
        Returns:
            List of normalized endpoints
        """
        if not endpoints_str:
            return []
        
        endpoints = []
        for endpoint_part in endpoints_str.split(','):
            endpoint_part = endpoint_part.strip()
            if not endpoint_part:
                continue
            
            try:
                # Handle special keywords
                if endpoint_part.lower() in ['any', 'all', '*']:
                    endpoints.append(NormalizedEndpoint('0.0.0.0/0'))
                    continue
                
                # Normalize IP address/range/CIDR
                normalized_cidr = normalize_ip_address(endpoint_part)
                endpoints.append(NormalizedEndpoint(normalized_cidr))
                
            except ValueError as e:
                logger.warning(f"Skipping invalid endpoint '{endpoint_part}': {e}")
                continue
        
        return endpoints
    
    def _parse_services(self, services_str: str) -> List[NormalizedService]:
        """
        Parse service specification into normalized services
        
        Args:
            services_str: Service specification (protocol/port combinations)
            
        Returns:
            List of normalized services
        """
        if not services_str:
            return []
        
        services = []
        
        # Handle different service formats:
        # - "tcp/80,443"
        # - "tcp/80,udp/53"
        # - "80,443" (defaults to tcp)
        # - "any" or "*" (tcp+udp/1-65535)
        
        if services_str.lower() in ['any', 'all', '*']:
            # Create services for common protocols with all ports
            for protocol in ['tcp', 'udp']:
                services.append(NormalizedService(protocol=protocol, port_ranges=[(1, 65535)]))
            return services
        
        # Split by comma and parse each service
        for service_part in services_str.split(','):
            service_part = service_part.strip()
            if not service_part:
                continue
            
            try:
                # Check if protocol is specified
                if '/' in service_part:
                    protocol_str, ports_str = service_part.split('/', 1)
                    protocol = protocol_str.strip().lower()
                    ports = ports_str.strip()
                else:
                    # Default to TCP
                    protocol = 'tcp'
                    ports = service_part
                
                # Validate protocol
                if protocol not in ['tcp', 'udp', 'icmp']:
                    logger.warning(f"Unknown protocol '{protocol}', defaulting to tcp")
                    protocol = 'tcp'
                
                # Handle ICMP (no ports)
                if protocol == 'icmp':
                    services.append(NormalizedService(protocol=protocol, port_ranges=[(0, 0)]))
                    continue
                
                # Parse port specification
                normalized_service = normalize_port_ranges(ports, protocol)
                services.append(normalized_service)
                
            except ValueError as e:
                logger.warning(f"Skipping invalid service '{service_part}': {e}")
                continue
        
        return services
    
    async def _create_far_rule(
        self, 
        request_id: int, 
        normalized_rule: NormalizedRule, 
        canonical_hash: bytes
    ) -> FarRule:
        """
        Create FAR rule and related records in database
        
        Args:
            request_id: ID of the FAR request
            normalized_rule: Normalized rule object
            canonical_hash: Canonical hash for deduplication
            
        Returns:
            Created FarRule object
        """
        # Create the main rule record
        far_rule = FarRule(
            request_id=request_id,
            canonical_hash=canonical_hash,
            action=normalized_rule.action,
            direction=normalized_rule.direction
        )
        
        self.db.add(far_rule)
        self.db.flush()  # Get the ID
        
        # Create endpoint records
        for endpoint in normalized_rule.source_endpoints:
            endpoint_record = FarRuleEndpoint(
                rule_id=far_rule.id,
                endpoint_type='source',
                network_cidr=endpoint.network_cidr
            )
            self.db.add(endpoint_record)
        
        for endpoint in normalized_rule.destination_endpoints:
            endpoint_record = FarRuleEndpoint(
                rule_id=far_rule.id,
                endpoint_type='destination',
                network_cidr=endpoint.network_cidr
            )
            self.db.add(endpoint_record)
        
        # Create service records
        for service in normalized_rule.services:
            # Format port ranges for PostgreSQL
            port_ranges_str = format_port_ranges_for_postgres(service.port_ranges)
            
            service_record = FarRuleService(
                rule_id=far_rule.id,
                protocol=service.protocol,
                port_ranges=port_ranges_str  # This will be converted by SQLAlchemy
            )
            self.db.add(service_record)
        
        return far_rule
