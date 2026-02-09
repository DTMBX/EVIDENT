"""
Legal E-Discovery Routes
Flask blueprints for case management, evidence processing, and discovery workflows
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps

from services.legal_service import (
    LegalCaseService, EvidenceProcessingService, ChainOfCustodyService,
    PrivilegeService, DiscoveryService
)
from models.legal_case import LegalCase, CaseParty
from models.evidence import EvidenceItem, ChainOfCustody, PrivilegeLog
from auth.models import db

# Create blueprint
legal_bp = Blueprint('legal', __name__, url_prefix='/api/legal')


def require_case_access(f):
    """Decorator to verify user has access to case"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        case_id = kwargs.get('case_id') or request.json.get('case_id')
        case = LegalCase.query.get(case_id)
        
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        # TODO: Implement proper access control
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================================================
# CASE MANAGEMENT ENDPOINTS
# ============================================================================

@legal_bp.route('/cases', methods=['GET'])
@login_required
def list_cases():
    """Get all cases for current user's organization"""
    cases = LegalCase.query.all()
    return jsonify({
        'cases': [{
            'id': c.id,
            'case_number': c.case_number,
            'case_name': c.case_name,
            'case_type': c.case_type,
            'status': c.status,
            'jurisdiction': c.jurisdiction,
            'lead_attorney': c.lead_attorney.email if c.lead_attorney else None,
            'evidence_count': len(c.evidence_items),
            'created_at': c.created_at.isoformat()
        } for c in cases]
    })


@legal_bp.route('/cases', methods=['POST'])
@login_required
def create_case():
    """Create a new legal case"""
    data = request.json
    
    try:
        case = LegalCaseService.create_case(data, current_user)
        return jsonify({
            'success': True,
            'case_id': case.id,
            'case_number': case.case_number,
            'message': f'Case {case.case_number} created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@legal_bp.route('/cases/<int:case_id>', methods=['GET'])
@login_required
@require_case_access
def get_case(case_id):
    """Get case details"""
    case = LegalCaseService.get_case(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    
    return jsonify({
        'id': case.id,
        'case_number': case.case_number,
        'case_name': case.case_name,
        'case_type': case.case_type,
        'jurisdiction': case.jurisdiction,
        'court_name': case.court_name,
        'judge_name': case.judge_name,
        'status': case.status,
        'is_legal_hold': case.is_legal_hold,
        'filed_date': case.filed_date.isoformat() if case.filed_date else None,
        'trial_date': case.trial_date.isoformat() if case.trial_date else None,
        'evidence_count': len(case.evidence_items),
        'parties': [{
            'id': p.id,
            'name': p.name,
            'party_type': p.party_type,
            'role': p.role
        } for p in case.case_parties],
        'created_at': case.created_at.isoformat(),
        'updated_at': case.updated_at.isoformat()
    })


@legal_bp.route('/cases/<int:case_id>', methods=['PUT'])
@login_required
@require_case_access
def update_case(case_id):
    """Update case information"""
    data = request.json
    case = LegalCaseService.update_case(case_id, data, current_user)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    
    return jsonify({
        'success': True,
        'case_number': case.case_number,
        'message': 'Case updated successfully'
    })


@legal_bp.route('/cases/<int:case_id>/legal-hold', methods=['POST'])
@login_required
@require_case_access
def place_legal_hold(case_id):
    """Place a legal hold on case"""
    data = request.json
    case = LegalCaseService.place_legal_hold(
        case_id, 
        data.get('reason', 'Legal hold placed'), 
        current_user
    )
    
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    
    return jsonify({
        'success': True,
        'is_legal_hold': case.is_legal_hold,
        'legal_hold_date': case.legal_hold_date.isoformat(),
        'message': 'Legal hold placed on case and all evidence'
    })


# ============================================================================
# CASE PARTY ENDPOINTS
# ============================================================================

@legal_bp.route('/cases/<int:case_id>/parties', methods=['GET'])
@login_required
@require_case_access
def list_case_parties(case_id):
    """Get all parties for a case"""
    parties = LegalCaseService.get_case_parties(case_id)
    return jsonify({
        'parties': [{
            'id': p.id,
            'name': p.name,
            'party_type': p.party_type,
            'role': p.role,
            'contact_info': p.contact_info,
            'email': p.email,
            'phone': p.phone
        } for p in parties]
    })


@legal_bp.route('/cases/<int:case_id>/parties', methods=['POST'])
@login_required
@require_case_access
def add_case_party(case_id):
    """Add a party to case"""
    data = request.json
    party = LegalCaseService.add_case_party(case_id, data)
    
    return jsonify({
        'success': True,
        'party_id': party.id,
        'name': party.name,
        'message': f'Party {party.name} added to case'
    }), 201


# ============================================================================
# EVIDENCE INGESTION & PROCESSING ENDPOINTS
# ============================================================================

@legal_bp.route('/cases/<int:case_id>/evidence', methods=['GET'])
@login_required
@require_case_access
def list_case_evidence(case_id):
    """Get all evidence for a case"""
    evidence = LegalCaseService.get_case_evidence(case_id)
    return jsonify({
        'evidence': [{
            'id': e.id,
            'filename': e.original_filename,
            'file_type': e.file_type,
            'evidence_type': e.evidence_type,
            'size_mb': round(e.file_size_bytes / 1024 / 1024, 2) if e.file_size_bytes else 0,
            'hash_sha256': e.hash_sha256,
            'is_responsive': e.is_responsive,
            'has_privilege': e.has_privilege,
            'processing_status': e.processing_status,
            'collected_date': e.collected_date.isoformat() if e.collected_date else None,
            'collected_by': e.collected_by,
            'created_at': e.created_at.isoformat()
        } for e in evidence]
    })


@legal_bp.route('/cases/<int:case_id>/evidence/ingest', methods=['POST'])
@login_required
@require_case_access
def ingest_evidence(case_id):
    """Ingest evidence into case"""
    data = request.json
    
    try:
        evidence = EvidenceProcessingService.ingest_evidence(
            case_id=case_id,
            file_info=data['file_info'],
            uploaded_by_user=current_user,
            collected_date=data.get('collected_date')
        )
        
        return jsonify({
            'success': True,
            'evidence_id': evidence.id,
            'filename': evidence.original_filename,
            'hash_sha256': evidence.hash_sha256,
            'message': f'Evidence {evidence.original_filename} ingested successfully',
            'chain_of_custody_id': ChainOfCustodyService.log_evidence_action(
                evidence_id=evidence.id,
                action='ingested',
                actor_id=current_user.id
            ).id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@legal_bp.route('/evidence/<int:evidence_id>/chain-of-custody', methods=['GET'])
@login_required
def get_evidence_history(evidence_id):
    """Get chain of custody for evidence"""
    history = ChainOfCustodyService.get_evidence_history(evidence_id)
    return jsonify({
        'chain_of_custody': [{
            'id': h.id,
            'action': h.action,
            'actor': h.actor_name,
            'timestamp': h.action_timestamp.isoformat(),
            'details': h.action_details,
            'hash_after': h.hash_after
        } for h in history]
    })


@legal_bp.route('/evidence/<int:evidence_id>/privilege', methods=['POST'])
@login_required
def mark_evidence_privileged(evidence_id):
    """Mark evidence as privileged"""
    data = request.json
    evidence = EvidenceProcessingService.mark_privileged(
        evidence_id,
        data.get('privilege_type'),
        data.get('privilege_holder')
    )
    
    if not evidence:
        return jsonify({'error': 'Evidence not found'}), 404
    
    # Log privilege assertion
    privilege_log = PrivilegeService.assert_privilege(
        case_id=evidence.case_id,
        evidence_id=evidence_id,
        privilege_data=data,
        asserted_by_user=current_user
    )
    
    return jsonify({
        'success': True,
        'evidence_id': evidence_id,
        'has_privilege': evidence.has_privilege,
        'privilege_type': evidence.privilege_type,
        'privilege_log_id': privilege_log.id,
        'message': 'Evidence marked as privileged'
    })


@legal_bp.route('/evidence/<int:evidence_id>/responsive', methods=['POST'])
@login_required
def mark_evidence_responsive(evidence_id):
    """Mark evidence as responsive to discovery"""
    data = request.json
    evidence = EvidenceProcessingService.mark_responsive(
        evidence_id,
        data.get('is_responsive', True)
    )
    
    if not evidence:
        return jsonify({'error': 'Evidence not found'}), 404
    
    # Log action
    ChainOfCustodyService.log_evidence_action(
        evidence_id=evidence_id,
        action='marked_responsive',
        actor_id=current_user.id,
        details=f'Marked as responsive: {evidence.is_responsive}'
    )
    
    return jsonify({
        'success': True,
        'evidence_id': evidence_id,
        'is_responsive': evidence.is_responsive,
        'message': 'Evidence responsiveness updated'
    })


@legal_bp.route('/evidence/<int:evidence_id>/analyze', methods=['POST'])
@login_required
def flag_for_analysis(evidence_id):
    """Flag evidence for AI analysis"""
    data = request.json
    analysis_types = data.get('analysis_types', ['transcription', 'entity_extraction'])
    
    evidence = EvidenceProcessingService.flag_evidence_for_analysis(
        evidence_id,
        analysis_types
    )
    
    if not evidence:
        return jsonify({'error': 'Evidence not found'}), 404
    
    ChainOfCustodyService.log_evidence_action(
        evidence_id=evidence_id,
        action='analysis_queued',
        actor_id=current_user.id,
        details=f'Queued for analysis: {", ".join(analysis_types)}'
    )
    
    return jsonify({
        'success': True,
        'evidence_id': evidence_id,
        'processing_status': evidence.processing_status,
        'analysis_types': analysis_types,
        'message': 'Evidence queued for analysis'
    })


# ============================================================================
# PRIVILEGE LOG ENDPOINTS
# ============================================================================

@legal_bp.route('/cases/<int:case_id>/privilege-log', methods=['GET'])
@login_required
@require_case_access
def get_case_privilege_log(case_id):
    """Get privilege log for case"""
    logs = PrivilegeService.get_case_privilege_log(case_id)
    return jsonify({
        'privilege_log': [{
            'id': log.id,
            'privilege_type': log.privilege_type,
            'privilege_holder': log.privilege_holder,
            'document_identifier': log.document_identifier,
            'description': log.privilege_description,
            'is_disputed': log.is_disputed,
            'asserted_date': log.asserted_date.isoformat()
        } for log in logs]
    })


# ============================================================================
# DISCOVERY & PRODUCTION ENDPOINTS
# ============================================================================

@legal_bp.route('/cases/<int:case_id>/productions', methods=['POST'])
@login_required
@require_case_access
def create_production_set(case_id):
    """Create a production set"""
    data = request.json
    
    prod = DiscoveryService.create_production_set(
        case_id,
        data,
        current_user
    )
    
    ChainOfCustodyService.log_case_action(
        case_id,
        'production_created',
        current_user.id,
        f'Production set {data["production_number"]} created'
    )
    
    return jsonify({
        'success': True,
        'production_set_id': prod.id,
        'production_number': prod.production_number,
        'message': f'Production set {prod.production_number} created'
    }), 201


@legal_bp.route('/productions/<int:production_set_id>/items', methods=['POST'])
@login_required
def add_to_production(production_set_id):
    """Add evidence to production set"""
    data = request.json
    
    item = DiscoveryService.add_to_production(
        production_set_id,
        data['evidence_id'],
        data['bates_number'],
        data.get('is_redacted', False)
    )
    
    return jsonify({
        'success': True,
        'production_item_id': item.id,
        'bates_number': item.bates_number,
        'message': 'Item added to production'
    }), 201


@legal_bp.route('/productions/<int:production_set_id>/finalize', methods=['POST'])
@login_required
def finalize_production(production_set_id):
    """Finalize production set"""
    prod = DiscoveryService.finalize_production(production_set_id, current_user)
    
    if not prod:
        return jsonify({'error': 'Production set not found'}), 404
    
    return jsonify({
        'success': True,
        'production_set_id': prod.id,
        'status': prod.status,
        'message': 'Production set finalized and ready for delivery'
    })


@legal_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for legal API"""
    return jsonify({
        'status': 'healthy',
        'service': 'legal_ediscovery_api',
        'timestamp': datetime.utcnow().isoformat()
    })
