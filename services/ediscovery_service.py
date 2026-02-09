"""
E-Discovery Service Layer
Service methods for managing document discovery, productions, and compliance
"""

from datetime import datetime, timedelta
from models.ediscovery import (
    DiscoveryRequest, ResponsiveDocument, ProductionSet, ProductionItem,
    PrivilegeLog, DocumentMetadata, LitigationHold, Custodian, HoldNotice,
    DocumentSearchQuery, ESIProtocol
)
from models.evidence import EvidenceItem, ChainOfCustody
from models.legal_case import LegalCase
from auth.models import db, User
import json
import hashlib
from uuid import uuid4


class DiscoveryService:
    """Service for managing discovery requests and responses"""
    
    @staticmethod
    def create_discovery_request(case_id, request_data, created_by_user):
        """Create a new discovery request"""
        request = DiscoveryRequest(
            case_id=case_id,
            request_number=request_data['request_number'],
            request_type=request_data['request_type'],
            request_text=request_data['request_text'],
            requesting_party=request_data.get('requesting_party'),
            receiving_party=request_data.get('receiving_party'),
            received_date=request_data.get('received_date'),
            response_due_date=request_data.get('response_due_date'),
            assigned_to_id=request_data.get('assigned_to_id'),
            priority=request_data.get('priority', 'normal'),
            created_by_id=created_by_user.id
        )
        
        db.session.add(request)
        db.session.commit()
        
        # Log action
        ChainOfCustodyService.log_case_action(
            case_id=case_id,
            action='discovery_request_created',
            actor_id=created_by_user.id,
            details=f'Discovery request {request.request_number} created'
        )
        
        return request
    
    @staticmethod
    def update_discovery_request(request_id, request_data, updated_by_user):
        """Update discovery request status and response"""
        request = DiscoveryRequest.query.get(request_id)
        if not request:
            return None
        
        old_status = request.status
        
        for key, value in request_data.items():
            if hasattr(request, key) and key not in ['id', 'created_at', 'created_by_id']:
                setattr(request, key, value)
        
        if 'status' in request_data and request_data['status'] == 'responded':
            request.response_submitted_date = datetime.utcnow()
        
        request.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log status change
        if old_status != request.status:
            ChainOfCustodyService.log_case_action(
                case_id=request.case_id,
                action='discovery_request_updated',
                actor_id=updated_by_user.id,
                details=f'Request {request.request_number} status changed: {old_status} -> {request.status}'
            )
        
        return request
    
    @staticmethod
    def link_responsive_documents(discovery_request_id, evidence_ids, linked_by_user):
        """Link evidence items as responsive to a discovery request"""
        request = DiscoveryRequest.query.get(discovery_request_id)
        if not request:
            return None
        
        linked_docs = []
        for evidence_id in evidence_ids:
            # Check if already linked
            existing = ResponsiveDocument.query.filter_by(
                evidence_id=evidence_id,
                discovery_request_id=discovery_request_id
            ).first()
            
            if not existing:
                doc = ResponsiveDocument(
                    evidence_id=evidence_id,
                    discovery_request_id=discovery_request_id,
                    is_responsive=True
                )
                db.session.add(doc)
                linked_docs.append(doc)
        
        db.session.commit()
        
        # Log action
        ChainOfCustodyService.log_case_action(
            case_id=request.case_id,
            action='responsive_documents_linked',
            actor_id=linked_by_user.id,
            details=f'{len(linked_docs)} documents linked to request {request.request_number}'
        )
        
        return linked_docs
    
    @staticmethod
    def get_discovery_stats(case_id):
        """Get statistics about discoveries for a case"""
        requests = DiscoveryRequest.query.filter_by(case_id=case_id).all()
        
        stats = {
            'total_requests': len(requests),
            'pending': sum(1 for r in requests if r.status == 'pending'),
            'responded': sum(1 for r in requests if r.status == 'responded'),
            'objected': sum(1 for r in requests if r.status == 'objected'),
            'overdue': sum(1 for r in requests if datetime.utcnow() > r.response_due_date and r.status == 'pending'),
            'by_type': {}
        }
        
        for request in requests:
            req_type = request.request_type
            if req_type not in stats['by_type']:
                stats['by_type'][req_type] = {'total': 0, 'responded': 0, 'pending': 0}
            stats['by_type'][req_type]['total'] += 1
            if request.status == 'responded':
                stats['by_type'][req_type]['responded'] += 1
            elif request.status == 'pending':
                stats['by_type'][req_type]['pending'] += 1
        
        return stats


class ProductionService:
    """Service for managing document productions"""
    
    @staticmethod
    def create_production(case_id, production_data, created_by_user):
        """Create a new production set"""
        production_uuid = str(uuid4())
        
        production = ProductionSet(
            case_id=case_id,
            production_number=production_data['production_number'],
            production_uuid=production_uuid,
            production_date=production_data.get('production_date', datetime.utcnow()),
            produced_to_party=production_data['produced_to_party'],
            description=production_data.get('description'),
            delivery_format=production_data.get('delivery_format', 'native'),
            delivery_method=production_data.get('delivery_method'),
            created_by_id=created_by_user.id
        )
        
        db.session.add(production)
        db.session.commit()
        
        # Log action
        ChainOfCustodyService.log_case_action(
            case_id=case_id,
            action='production_created',
            actor_id=created_by_user.id,
            details=f'Production {production.production_number} created'
        )
        
        return production
    
    @staticmethod
    def add_document_to_production(production_id, evidence_id, bates_start, bates_end=None, added_by_user=None):
        """Add a document to a production with Bates numbering"""
        production = ProductionSet.query.get(production_id)
        if not production:
            return None
        
        evidence = EvidenceItem.query.get(evidence_id)
        if not evidence:
            return None
        
        # Determine sequence number
        last_item = ProductionItem.query.filter_by(production_id=production_id).order_by(
            ProductionItem.sequence_number.desc()
        ).first()
        sequence = (last_item.sequence_number or 0) + 1 if last_item else 1
        
        item = ProductionItem(
            production_id=production_id,
            evidence_id=evidence_id,
            bates_number_start=bates_start,
            bates_number_end=bates_end or bates_start,
            sequence_number=sequence,
            file_size_bytes=evidence.file_size_bytes
        )
        
        db.session.add(item)
        
        # Update production totals
        production.total_documents = len(production.production_items) + 1
        if bates_end:
            try:
                start_num = int(bates_start.split('-')[-1])
                end_num = int(bates_end.split('-')[-1])
                production.total_pages += (end_num - start_num + 1)
            except:
                pass
        
        if evidence.file_size_bytes:
            production.total_size_gb += evidence.file_size_bytes / (1024**3)
        
        db.session.commit()
        
        return item
    
    @staticmethod
    def apply_designation(production_id, document_ids, designation, applied_by_user):
        """Apply confidentiality designation to production items"""
        items = ProductionItem.query.filter(
            ProductionItem.production_id == production_id,
            ProductionItem.id.in_(document_ids)
        ).all()
        
        for item in items:
            item.designation = designation
            item.needs_designation = False
        
        production = ProductionSet.query.get(production_id)
        if production:
            production.has_designations = True
            production.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return len(items)
    
    @staticmethod
    def export_production_load_file(production_id, format='txt'):
        """Generate load file for production (Concordance, COL-XML, etc.)"""
        production = ProductionSet.query.get(production_id)
        if not production:
            return None
        
        items = ProductionItem.query.filter_by(production_id=production_id).order_by(
            ProductionItem.sequence_number
        ).all()
        
        load_file = []
        
        if format == 'txt':  # Concordance format
            # Header
            load_file.append('\t'.join([
                'BEGINDOC', 'FILENAME', 'PAGES', 'BATES_START', 'BATES_END',
                'DESIGNATION', 'CUSTODIAN', 'DATE'
            ]))
            
            for item in items:
                load_file.append('\t'.join([
                    'D',
                    item.evidence.original_filename or '',
                    str(item.page_count or 1),
                    item.bates_number_start,
                    item.bates_number_end or item.bates_number_start,
                    item.designation or '',
                    item.evidence.collected_by or '',
                    (item.evidence.collected_date.isoformat() if item.evidence.collected_date else '')
                ]))
        
        elif format == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'Sequence', 'Bates Start', 'Bates End', 'Filename', 'Pages',
                'Designation', 'Date', 'Custodian'
            ])
            
            for item in items:
                writer.writerow([
                    item.sequence_number,
                    item.bates_number_start,
                    item.bates_number_end or item.bates_number_start,
                    item.evidence.original_filename or '',
                    item.page_count or 1,
                    item.designation or '',
                    (item.evidence.collected_date.strftime('%m/%d/%Y') if item.evidence.collected_date else ''),
                    item.evidence.collected_by or ''
                ])
            
            load_file = output.getvalue()
        
        return '\n'.join(load_file) if isinstance(load_file, list) else load_file


class PrivilegeService:
    """Service for managing privilege logs"""
    
    @staticmethod
    def create_privilege_log_entry(case_id, evidence_id, privilege_data, created_by_user):
        """Create privilege log entry for withheld document"""
        evidence = EvidenceItem.query.get(evidence_id)
        if not evidence:
            return None
        
        entry = PrivilegeLog(
            case_id=case_id,
            evidence_id=evidence_id,
            document_date=privilege_data.get('document_date'),
            document_title=privilege_data['document_title'],
            document_type=privilege_data.get('document_type'),
            privilege_claimed=privilege_data['privilege_claimed'],
            privilege_description=privilege_data['privilege_description'],
            from_party=privilege_data['from_party'],
            to_party=privilege_data['to_party'],
            cc_parties=privilege_data.get('cc_parties'),
            general_subject=privilege_data['general_subject'],
            description=privilege_data.get('description'),
            attorney_involved=privilege_data.get('attorney_involved'),
            seeks_legal_advice=privilege_data.get('seeks_legal_advice', True),
            attorney_prepared=privilege_data.get('attorney_prepared', False),
            withholding_reason=privilege_data.get('withholding_reason'),
            created_by_id=created_by_user.id
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Mark evidence as privileged
        evidence.has_privilege = True
        evidence.privilege_type = privilege_data['privilege_claimed']
        db.session.commit()
        
        # Log action
        ChainOfCustodyService.log_case_action(
            case_id=case_id,
            action='privilege_log_created',
            actor_id=created_by_user.id,
            details=f'Privilege log entry created for {privilege_data["document_title"]}'
        )
        
        return entry
    
    @staticmethod
    def get_privilege_log(case_id):
        """Get complete privilege log for a case"""
        entries = PrivilegeLog.query.filter_by(case_id=case_id).order_by(
            PrivilegeLog.created_at.desc()
        ).all()
        
        log = {
            'total_withheld': len(entries),
            'by_privilege_type': {},
            'entries': []
        }
        
        for entry in entries:
            priv_type = entry.privilege_claimed
            if priv_type not in log['by_privilege_type']:
                log['by_privilege_type'][priv_type] = 0
            log['by_privilege_type'][priv_type] += 1
            
            log['entries'].append({
                'id': entry.id,
                'document_title': entry.document_title,
                'document_date': entry.document_date.isoformat() if entry.document_date else None,
                'privilege_type': entry.privilege_claimed,
                'from': entry.from_party,
                'to': entry.to_party,
                'subject': entry.general_subject,
                'withheld_reason': entry.withholding_reason
            })
        
        return log
    
    @staticmethod
    def validate_privilege_log(case_id):
        """Validate privilege log completeness and compliance"""
        entries = PrivilegeLog.query.filter_by(case_id=case_id).all()
        
        issues = []
        
        for entry in entries:
            # Check required fields
            if not entry.from_party:
                issues.append(f'Entry {entry.id}: Missing "from" party')
            if not entry.to_party:
                issues.append(f'Entry {entry.id}: Missing "to" party')
            if not entry.attorney_involved and entry.privilege_claimed in ['attorney_client', 'work_product']:
                issues.append(f'Entry {entry.id}: Missing attorney for {entry.privilege_claimed} privilege')
            if not entry.general_subject:
                issues.append(f'Entry {entry.id}: Missing general subject')
        
        return {
            'is_valid': len(issues) == 0,
            'total_entries': len(entries),
            'issues': issues
        }


class LitigationHoldService:
    """Service for managing litigation holds"""
    
    @staticmethod
    def create_litigation_hold(case_id, hold_data, issued_by_user):
        """Create a new litigation hold"""
        hold_uuid = str(uuid4())
        
        hold = LitigationHold(
            case_id=case_id,
            hold_name=hold_data['hold_name'],
            hold_uuid=hold_uuid,
            issued_date=hold_data.get('issued_date', datetime.utcnow()),
            effective_date=hold_data.get('effective_date'),
            initiating_event=hold_data['initiating_event'],
            hold_scope=hold_data['hold_scope'],
            affected_systems=hold_data.get('affected_systems'),
            retention_instructions=hold_data.get('retention_instructions'),
            issued_by_id=issued_by_user.id
        )
        
        db.session.add(hold)
        db.session.commit()
        
        # Log action
        ChainOfCustodyService.log_case_action(
            case_id=case_id,
            action='litigation_hold_created',
            actor_id=issued_by_user.id,
            details=f'Litigation hold "{hold.hold_name}" created'
        )
        
        return hold
    
    @staticmethod
    def add_custodian_to_hold(hold_id, custodian_data, added_by_user):
        """Add a custodian to a litigation hold"""
        hold = LitigationHold.query.get(hold_id)
        if not hold:
            return None
        
        custodian = Custodian(
            hold_id=hold_id,
            case_id=hold.case_id,
            name=custodian_data['name'],
            title=custodian_data.get('title'),
            department=custodian_data.get('department'),
            email=custodian_data['email'],
            phone=custodian_data.get('phone'),
            employee_id=custodian_data.get('employee_id'),
            email_account=custodian_data.get('email_account'),
            phone_numbers=custodian_data.get('phone_numbers'),
            file_locations=custodian_data.get('file_locations'),
            special_instructions=custodian_data.get('special_instructions')
        )
        
        db.session.add(custodian)
        db.session.commit()
        
        return custodian
    
    @staticmethod
    def send_hold_notice(custodian_id, hold_id, notice_text, sent_by_user):
        """Send hold notice to a custodian"""
        custodian = Custodian.query.get(custodian_id)
        if not custodian:
            return None
        
        notice = HoldNotice(
            hold_id=hold_id,
            custodian_id=custodian_id,
            notice_text=notice_text,
            notice_type='initial',
            sent_date=datetime.utcnow(),
            sent_via='email',
            recipient_email=custodian.email
        )
        
        db.session.add(notice)
        custodian.status = 'pending'
        db.session.commit()
        
        # TODO: Send email to custodian
        
        return notice
    
    @staticmethod
    def acknowledge_hold(custodian_id, acknowledged_date=None):
        """Record custodian acknowledgment of hold"""
        custodian = Custodian.query.get(custodian_id)
        if not custodian:
            return None
        
        custodian.acknowledgment_date = acknowledged_date or datetime.utcnow()
        custodian.has_acknowledged = True
        custodian.status = 'acknowledged'
        db.session.commit()
        
        return custodian
    
    @staticmethod
    def certify_compliance(custodian_id, certified_date=None):
        """Record custodian certification of hold compliance"""
        custodian = Custodian.query.get(custodian_id)
        if not custodian:
            return None
        
        custodian.last_certification_date = certified_date or datetime.utcnow()
        custodian.has_certified_compliance = True
        custodian.status = 'compliant'
        db.session.commit()
        
        return custodian
    
    @staticmethod
    def get_hold_status(hold_id):
        """Get status report for a litigation hold"""
        hold = LitigationHold.query.get(hold_id)
        if not hold:
            return None
        
        custodians = Custodian.query.filter_by(hold_id=hold_id).all()
        
        status = {
            'hold_name': hold.hold_name,
            'issued_date': hold.issued_date.isoformat() if hold.issued_date else None,
            'is_active': hold.is_active,
            'total_custodians': len(custodians),
            'acknowledged': sum(1 for c in custodians if c.has_acknowledged),
            'compliant': sum(1 for c in custodians if c.has_certified_compliance),
            'pending': sum(1 for c in custodians if c.status == 'pending'),
            'custodians': []
        }
        
        for custodian in custodians:
            status['custodians'].append({
                'name': custodian.name,
                'email': custodian.email,
                'status': custodian.status,
                'acknowledged_date': custodian.acknowledgment_date.isoformat() if custodian.acknowledgment_date else None,
                'certification_date': custodian.last_certification_date.isoformat() if custodian.last_certification_date else None
            })
        
        return status


class DocumentMetadataService:
    """Service for managing document metadata"""
    
    @staticmethod
    def extract_and_store_metadata(evidence_id, file_path, extracted_by_user):
        """Extract metadata from file and store in database"""
        evidence = EvidenceItem.query.get(evidence_id)
        if not evidence:
            return None
        
        # Check if metadata already exists
        metadata = DocumentMetadata.query.filter_by(evidence_id=evidence_id).first()
        if not metadata:
            metadata = DocumentMetadata(evidence_id=evidence_id)
        
        # TODO: Implement actual metadata extraction based on file type
        # For now, create basic structure
        
        db.session.add(metadata)
        db.session.commit()
        
        return metadata
    
    @staticmethod
    def search_by_metadata(case_id, **filters):
        """Search for documents by metadata"""
        query = DocumentMetadata.query.join(EvidenceItem).filter(
            EvidenceItem.case_id == case_id
        )
        
        if 'author' in filters and filters['author']:
            query = query.filter(DocumentMetadata.author.ilike(f"%{filters['author']}%"))
        
        if 'from_date' in filters and filters['from_date']:
            query = query.filter(DocumentMetadata.created_date >= filters['from_date'])
        
        if 'to_date' in filters and filters['to_date']:
            query = query.filter(DocumentMetadata.created_date <= filters['to_date'])
        
        if 'keywords' in filters and filters['keywords']:
            keywords = filters['keywords']
            query = query.filter(DocumentMetadata.keywords.ilike(f"%{keywords}%"))
        
        return query.all()


class ChainOfCustodyService:
    """Service for managing chain of custody"""
    
    @staticmethod
    def log_case_action(case_id, action, actor_id, details, ip_address='', user_agent=''):
        """Log an action in case history (general case action, not evidence specific)"""
        # This is a wrapper for general case actions
        # For evidence-specific actions, use log_evidence_action
        pass
    
    @staticmethod
    def log_evidence_action(evidence_id, action, actor_id, details='', ip_address='', user_agent='', hash_before=None, hash_after=None):
        """Log an action in evidence chain of custody"""
        evidence = EvidenceItem.query.get(evidence_id)
        if not evidence:
            return None
        
        actor = User.query.get(actor_id)
        
        coc_entry = ChainOfCustody(
            evidence_id=evidence_id,
            action=action,
            actor_id=actor_id,
            actor_name=actor.full_name if actor else 'Unknown',
            action_details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            hash_before=hash_before,
            hash_after=hash_after
        )
        
        db.session.add(coc_entry)
        db.session.commit()
        
        return coc_entry
    
    @staticmethod
    def get_evidence_chain_of_custody(evidence_id):
        """Get complete chain of custody for evidence item"""
        entries = ChainOfCustody.query.filter_by(evidence_id=evidence_id).order_by(
            ChainOfCustody.action_timestamp
        ).all()
        
        chain = []
        for entry in entries:
            chain.append({
                'action': entry.action,
                'actor': entry.actor_name,
                'timestamp': entry.action_timestamp.isoformat() if entry.action_timestamp else None,
                'details': entry.action_details,
                'hash_before': entry.hash_before,
                'hash_after': entry.hash_after
            })
        
        return chain
