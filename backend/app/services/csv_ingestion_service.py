"""
CSV parsing and rule ingestion service for Phase 2.2
"""
import csv
import io
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DatabaseError, OperationalError
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
from app.utils.csv_errors import (
    CSVRowError, CSVValidationError, CSVColumnError, DatabaseConnectionError
)
from app.services.csv_validation_service import CSVValidationService
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)


class CsvIngestionService:
    """Service for parsing CSV files and creating normalized FAR rules"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def ingest_csv_file(self, request_id: int, file_content: str) -> Dict[str, Any]:
        """
        Ingest CSV file content and create normalized FAR rules with comprehensive error handling
        
        Args:
            request_id: ID of the FAR request
            file_content: CSV file content as string (already validated and decoded)
            
        Returns:
            Dictionary with ingestion statistics and results
            
        Raises:
            ValueError: If request not found
            CSVValidationError: If CSV structure is invalid
            CSVColumnError: If required columns are missing
        """
        # Initialize statistics
        statistics = {
            'total_rows': 0,
            'processed_rows': 0,
            'skipped_rows': 0,
            'error_rows': 0,
            'created_rules': 0,
            'duplicate_rules': 0,
            'errors': [],
            'warnings': [],
            'row_errors': []  # Detailed per-row errors
        }
        
        far_request = None
        try:
            # Verify the request exists
            far_request = self.db.query(FarRequest).filter(FarRequest.id == request_id).first()
            if not far_request:
                raise ValueError(f"FAR request {request_id} not found")
            
            # Validate CSV structure first
            try:
                fieldnames, column_mapping = CSVValidationService.validate_csv_structure(
                    file_content,
                    filename=far_request.source_filename
                )
            except (CSVValidationError, CSVColumnError) as e:
                # Re-raise with better context
                raise CSVValidationError(
                    f"CSV validation failed: {e.message}",
                    details=e.details
                )
            
            # Count rows
            try:
                row_count = CSVValidationService.validate_row_count(file_content)
                statistics['total_rows'] = row_count
            except CSVValidationError as e:
                raise
            
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(file_content))
            processed_hashes = set()
            
            # Process rows with detailed error tracking
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
                try:
                    # Skip empty rows
                    if not any(row.values()):
                        statistics['skipped_rows'] += 1
                        continue
                    
                    # Parse and normalize the rule
                    try:
                        normalized_rule = self._parse_csv_row(row, column_mapping)
                    except ValueError as e:
                        # Row-level parsing error
                        raise CSVRowError(
                            f"Failed to parse row: {str(e)}",
                            row_number=row_num,
                            row_data=dict(row),
                            field_errors={"parsing": str(e)}
                        )
                    
                    canonical_hash = compute_canonical_hash(normalized_rule)
                    
                    # Check for duplicates within this batch
                    if canonical_hash in processed_hashes:
                        statistics['duplicate_rules'] += 1
                        statistics['warnings'].append(
                            f"Row {row_num}: Duplicate rule (skipped)"
                        )
                        continue
                    
                    # Check for existing rule in database
                    existing_rule = self.db.query(FarRule).filter(
                        FarRule.canonical_hash == canonical_hash
                    ).first()
                    
                    if existing_rule:
                        statistics['duplicate_rules'] += 1
                        statistics['warnings'].append(
                            f"Row {row_num}: Rule already exists in database (skipped)"
                        )
                        continue
                    
                    # Create rule with transaction safety
                    try:
                        await self._create_far_rule(
                            request_id=request_id,
                            normalized_rule=normalized_rule,
                            canonical_hash=canonical_hash
                        )
                        processed_hashes.add(canonical_hash)
                        statistics['created_rules'] += 1
                        statistics['processed_rows'] += 1
                        
                    except OperationalError as e:
                        # Database connection error
                        self.db.rollback()
                        logger.error(f"Database connection error on row {row_num}: {str(e)}", exc_info=True)
                        raise DatabaseConnectionError(
                            message="Database connection failed while processing row",
                            details={"row_number": row_num, "error": str(e)}
                        )
                    except IntegrityError as e:
                        # Database constraint violation
                        self.db.rollback()
                        raise CSVRowError(
                            f"Database constraint violation: {str(e)}",
                            row_number=row_num,
                            row_data=dict(row),
                            field_errors={"database": str(e)}
                        )
                    except DatabaseError as e:
                        # Other database errors
                        self.db.rollback()
                        raise CSVRowError(
                            f"Database error: {str(e)}",
                            row_number=row_num,
                            row_data=dict(row),
                            field_errors={"database": str(e)}
                        )
                    
                except CSVRowError as e:
                    # Row-specific error - log and continue
                    statistics['error_rows'] += 1
                    statistics['row_errors'].append({
                        "row_number": e.details.get('row_number'),
                        "error": e.message,
                        "field_errors": e.details.get('field_errors', {}),
                        "row_data": e.details.get('row_data')
                    })
                    statistics['errors'].append(
                        f"Row {row_num}: {e.message}"
                    )
                    logger.warning(f"Row {row_num} error: {e.message}", exc_info=True)
                    continue
                    
                except Exception as e:
                    # Unexpected error on this row
                    statistics['error_rows'] += 1
                    error_msg = f"Row {row_num}: Unexpected error - {str(e)}"
                    statistics['errors'].append(error_msg)
                    statistics['row_errors'].append({
                        "row_number": row_num,
                        "error": error_msg,
                        "field_errors": {"unexpected": str(e)},
                        "row_data": dict(row)
                    })
                    logger.error(f"Unexpected error on row {row_num}: {str(e)}", exc_info=True)
                    continue
            
            # Commit all successful rows
            try:
                self.db.commit()
            except OperationalError as e:
                # Database connection error
                self.db.rollback()
                logger.error(f"Database connection error during commit: {str(e)}", exc_info=True)
                raise DatabaseConnectionError(
                    message="Database connection failed while committing changes",
                    details={"error": str(e)}
                )
            except Exception as e:
                self.db.rollback()
                raise ValueError(f"Failed to commit database changes: {str(e)}")
            
            # Update request status based on results
            if statistics['error_rows'] > 0 and statistics['created_rules'] == 0:
                # All rows failed
                far_request.status = 'error'
            elif statistics['error_rows'] > 0:
                # Partial success
                far_request.status = 'ingested_with_errors'
            else:
                # Complete success
                far_request.status = 'ingested'
            
            self.db.commit()
            
            return statistics
            
        except (CSVValidationError, CSVColumnError) as e:
            # Validation errors - rollback and re-raise
            self.db.rollback()
            if far_request:
                try:
                    far_request.status = 'error'
                    self.db.commit()
                except:
                    pass
            raise
            
        except DatabaseConnectionError:
            # Re-raise database connection errors as-is
            self.db.rollback()
            if far_request:
                try:
                    far_request.status = 'error'
                    self.db.commit()
                except:
                    pass
            raise
            
        except OperationalError as e:
            # Database connection error
            self.db.rollback()
            if far_request:
                try:
                    far_request.status = 'error'
                    self.db.commit()
                except:
                    pass
            logger.error(f"Database connection error during CSV ingestion: {str(e)}", exc_info=True)
            raise DatabaseConnectionError(
                message="Database connection failed during CSV ingestion",
                details={"error": str(e), "request_id": request_id}
            )
            
        except Exception as e:
            # Unexpected errors
            self.db.rollback()
            if far_request:
                try:
                    far_request.status = 'error'
                    self.db.commit()
                except:
                    pass
            logger.error(f"CSV ingestion failed for request {request_id}: {str(e)}", exc_info=True)
            raise ValueError(f"CSV ingestion failed: {str(e)}")
    
    def _parse_csv_row(self, row: Dict[str, str], column_mapping: Dict[str, Optional[str]]) -> NormalizedRule:
        """
        Parse a single CSV row into a normalized rule
        
        Args:
            row: Dictionary representing a CSV row
            column_mapping: Mapping of logical names to actual column names
            
        Returns:
            NormalizedRule object
            
        Raises:
            ValueError: If required fields are missing or invalid
            CSVRowError: If parsing fails with field-level error details
        """
        field_errors = {}
        
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
        source_col = column_mapping.get('source')
        if not source_col:
            raise ValueError("Source column not found in column mapping")
        
        source_value = row.get(source_col, '').strip()
        if not source_value:
            field_errors['source'] = "Source field is empty"
        else:
            try:
                source_endpoints = self._parse_endpoints(source_value)
                if not source_endpoints:
                    field_errors['source'] = "No valid source endpoints found"
            except Exception as e:
                field_errors['source'] = f"Failed to parse source: {str(e)}"
                source_endpoints = []
        
        # Parse destination endpoints
        dest_col = column_mapping.get('destination')
        if not dest_col:
            raise ValueError("Destination column not found in column mapping")
        
        dest_value = row.get(dest_col, '').strip()
        if not dest_value:
            field_errors['destination'] = "Destination field is empty"
        else:
            try:
                destination_endpoints = self._parse_endpoints(dest_value)
                if not destination_endpoints:
                    field_errors['destination'] = "No valid destination endpoints found"
            except Exception as e:
                field_errors['destination'] = f"Failed to parse destination: {str(e)}"
                destination_endpoints = []
        
        # Parse services
        service_col = column_mapping.get('service')
        if not service_col:
            raise ValueError("Service column not found in column mapping")
        
        service_value = row.get(service_col, '').strip()
        if not service_value:
            field_errors['service'] = "Service field is empty"
        else:
            try:
                services = self._parse_services(service_value)
                if not services:
                    field_errors['service'] = "No valid services found"
            except Exception as e:
                field_errors['service'] = f"Failed to parse service: {str(e)}"
                services = []
        
        # If any required fields failed, raise error with field details
        if field_errors:
            error_messages = [f"{field}: {msg}" for field, msg in field_errors.items()]
            raise ValueError("; ".join(error_messages))
        
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
