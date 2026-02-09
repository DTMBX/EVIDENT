"""
Legal Resource Library API Routes
Full API for accessing, searching, and managing legal documents
"""

from flask import Blueprint, request, jsonify, current_app
from auth.legal_library_service import LegalLibraryService
from auth.legal_library_models import (
    LegalDocument, DocumentCollection, DocumentComment, SavedDocument
)
from auth.models import db, User
from auth.decorators import token_required, admin_required
from datetime import datetime
import json

legal_library_bp = Blueprint('legal_library', __name__, url_prefix='/api/legal')


# ==================== DOCUMENT ENDPOINTS ====================

@legal_library_bp.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """Get specific legal document"""
    doc = LegalDocument.query.get(doc_id)
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    
    # Increment view count
    LegalLibraryService.increment_view_count(doc_id)
    
    return jsonify({
        'id': doc.id,
        'title': doc.title,
        'category': doc.category,
        'status': doc.status,
        'full_text': doc.full_text,
        'summary': doc.summary,
        'case_number': doc.case_number,
        'date_decided': doc.date_decided.isoformat() if doc.date_decided else None,
        'court': doc.court,
        'petitioner': doc.petitioner,
        'respondent': doc.respondent,
        'citation_supreme': doc.citation_supreme,
        'author': doc.author,
        'keywords': doc.keywords,
        'issues': doc.issues,
        'justices_concur': doc.justices_concur,
        'justices_dissent': doc.justices_dissent,
        'related_cases': doc.related_cases,
        'cases_cited': doc.cases_cited,
        'url_supremecourt': doc.url_supremecourt,
        'view_count': doc.view_count,
    })


@legal_library_bp.route('/documents/search', methods=['GET'])
def search_documents():
    """Search legal documents"""
    query = request.args.get('q', '')
    category = request.args.get('category')
    limit = request.args.get('limit', 50, type=int)
    
    results = LegalLibraryService.search_documents(query, category, limit=limit)
    
    return jsonify({
        'count': len(results),
        'results': [doc.to_dict() for doc in results]
    })


@legal_library_bp.route('/documents/by-case/<case_number>', methods=['GET'])
def get_by_case_number(case_number):
    """Get document by case number"""
    doc = LegalLibraryService.get_document_by_case_number(case_number)
    
    if not doc:
        return jsonify({'error': 'Case not found'}), 404
    
    LegalLibraryService.increment_view_count(doc.id)
    return jsonify(doc.to_dict())


@legal_library_bp.route('/documents/keywords/<keyword>', methods=['GET'])
def get_by_keyword(keyword):
    """Get documents with specific keyword"""
    limit = request.args.get('limit', 50, type=int)
    
    docs = LegalLibraryService.get_documents_by_keyword(keyword, limit=limit)
    
    return jsonify({
        'keyword': keyword,
        'count': len(docs),
        'results': [doc.to_dict() for doc in docs]
    })


@legal_library_bp.route('/documents/justice/<justice_name>', methods=['GET'])
def get_by_justice(justice_name):
    """Get documents by justice"""
    docs = LegalLibraryService.get_documents_by_justice(justice_name)
    
    return jsonify({
        'justice': justice_name,
        'count': len(docs),
        'results': [doc.to_dict() for doc in docs]
    })


@legal_library_bp.route('/documents/<doc_id>/related', methods=['GET'])
def get_related(doc_id):
    """Get related documents"""
    related = LegalLibraryService.get_related_cases(doc_id)
    
    return jsonify({
        'document_id': doc_id,
        'count': len(related),
        'related': [doc.to_dict() for doc in related]
    })


@legal_library_bp.route('/documents/<case_number>/citing', methods=['GET'])
def get_citing(case_number):
    """Get cases citing this case"""
    limit = request.args.get('limit', 100, type=int)
    citing = LegalLibraryService.get_citing_cases(case_number, limit=limit)
    
    return jsonify({
        'case_number': case_number,
        'count': len(citing),
        'citing_cases': [doc.to_dict() for doc in citing]
    })


@legal_library_bp.route('/documents/trending', methods=['GET'])
def get_trending():
    """Get trending documents"""
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    docs = LegalLibraryService.get_trending_documents(days=days, limit=limit)
    
    return jsonify({
        'period_days': days,
        'count': len(docs),
        'results': [doc.to_dict() for doc in docs]
    })


@legal_library_bp.route('/documents/recent', methods=['GET'])
def get_recent():
    """Get recently added documents"""
    limit = request.args.get('limit', 50, type=int)
    
    docs = LegalLibraryService.get_recent_documents(limit=limit)
    
    return jsonify({
        'count': len(docs),
        'results': [doc.to_dict() for doc in docs]
    })


# ==================== COLLECTION ENDPOINTS ====================

@legal_library_bp.route('/collections', methods=['GET'])
def list_collections():
    """List all collections"""
    collections = DocumentCollection.query.all()
    
    return jsonify({
        'count': len(collections),
        'collections': [{
            'id': c.id,
            'name': c.name,
            'category': c.category,
            'description': c.description,
            'document_count': c.document_count,
        } for c in collections]
    })


@legal_library_bp.route('/collections/<collection_id>', methods=['GET'])
def get_collection(collection_id):
    """Get collection"""
    collection = LegalLibraryService.get_collection(collection_id)
    
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404
    
    return jsonify({
        'id': collection.id,
        'name': collection.name,
        'category': collection.category,
        'description': collection.description,
        'document_count': collection.document_count,
        'documents': [doc.to_dict() for doc in collection.documents] if hasattr(collection, 'documents') else []
    })


@legal_library_bp.route('/collections/<collection_id>/documents', methods=['GET'])
def get_collection_documents(collection_id):
    """Get documents in collection"""
    collection = DocumentCollection.query.get(collection_id)
    
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404
    
    docs = LegalDocument.query.filter(
        LegalDocument.id.in_(collection.document_ids or [])
    ).all()
    
    return jsonify({
        'collection_id': collection_id,
        'collection_name': collection.name,
        'count': len(docs),
        'documents': [doc.to_dict() for doc in docs]
    })


# ==================== USER DOCUMENT ENDPOINTS ====================

@legal_library_bp.route('/saved', methods=['GET'])
@token_required
def get_saved_documents(current_user):
    """Get user's saved documents"""
    folder = request.args.get('folder')
    
    docs = LegalLibraryService.get_user_saved_documents(current_user.id, folder=folder)
    
    return jsonify({
        'count': len(docs),
        'documents': [doc.to_dict() for doc in docs]
    })


@legal_library_bp.route('/save/<doc_id>', methods=['POST'])
@token_required
def save_document(doc_id, current_user):
    """Save document for user"""
    data = request.get_json()
    
    saved = LegalLibraryService.save_document(
        current_user.id,
        doc_id,
        folder=data.get('folder'),
        note=data.get('note')
    )
    
    return jsonify({'message': 'Document saved', 'saved_id': saved.id}), 201


@legal_library_bp.route('/comments/<doc_id>', methods=['GET'])
def get_comments(doc_id):
    """Get comments on document"""
    comments = LegalLibraryService.get_document_comments(doc_id)
    
    return jsonify({
        'document_id': doc_id,
        'count': len(comments),
        'comments': [{
            'id': c.id,
            'user_id': c.user_id,
            'comment': c.comment,
            'highlight_text': c.highlight_text,
            'created_at': c.created_at.isoformat(),
        } for c in comments]
    })


@legal_library_bp.route('/comments/<doc_id>', methods=['POST'])
@token_required
def add_comment(doc_id, current_user):
    """Add comment to document"""
    data = request.get_json()
    
    comment = LegalLibraryService.add_comment(
        current_user.id,
        doc_id,
        data.get('comment'),
        highlight_text=data.get('highlight_text')
    )
    
    return jsonify({
        'message': 'Comment added',
        'comment_id': comment.id
    }), 201


# ==================== ADMIN ENDPOINTS ====================

@legal_library_bp.route('/documents', methods=['POST'])
@token_required
@admin_required
def create_document(current_user):
    """Create new legal document (ADMIN)"""
    data = request.get_json()
    
    doc = LegalLibraryService.add_document(
        data.get('title'),
        data.get('category'),
        data
    )
    
    return jsonify({'message': 'Document created', 'document_id': doc.id}), 201


@legal_library_bp.route('/documents/<doc_id>', methods=['PUT'])
@token_required
@admin_required
def update_document(doc_id, current_user):
    """Update document (ADMIN)"""
    doc = LegalDocument.query.get(doc_id)
    
    if not doc:
        return jsonify({'error': 'Document not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    for field in ['title', 'summary', 'full_text', 'status', 'keywords', 'issues']:
        if field in data:
            setattr(doc, field, data[field])
    
    db.session.commit()
    
    return jsonify({'message': 'Document updated'})


@legal_library_bp.route('/collections', methods=['POST'])
@token_required
@admin_required
def create_collection(current_user):
    """Create collection (ADMIN)"""
    data = request.get_json()
    
    collection = LegalLibraryService.create_collection(
        data.get('name'),
        data.get('category'),
        data.get('description')
    )
    
    return jsonify({'message': 'Collection created', 'collection_id': collection.id}), 201


@legal_library_bp.route('/collections/<collection_id>/add/<doc_id>', methods=['POST'])
@token_required
@admin_required
def add_to_collection(collection_id, doc_id, current_user):
    """Add document to collection (ADMIN)"""
    success = LegalLibraryService.add_to_collection(collection_id, doc_id)
    
    if not success:
        return jsonify({'error': 'Failed to add document'}), 400
    
    return jsonify({'message': 'Document added to collection'})


# ==================== STATISTICS & METADATA ====================

@legal_library_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get library statistics"""
    stats = LegalLibraryService.get_statistics()
    
    return jsonify(stats)


@legal_library_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get available document categories"""
    categories = [
        {'id': 'supreme_court', 'name': 'Supreme Court Cases'},
        {'id': 'court_of_appeals', 'name': 'Court of Appeals'},
        {'id': 'founding_document', 'name': 'Founding Documents'},
        {'id': 'amendment', 'name': 'Amendments'},
        {'id': 'bill_of_rights', 'name': 'Bill of Rights'},
        {'id': 'statute', 'name': 'Statutes'},
        {'id': 'constitution', 'name': 'Constitution'},
        {'id': 'opinion', 'name': 'Opinions'},
    ]
    
    return jsonify({'categories': categories})


@legal_library_bp.route('/collections/category/<category>', methods=['GET'])
def get_collections_by_category(category):
    """Get collections in category"""
    collections = DocumentCollection.query.filter_by(category=category).all()
    
    return jsonify({
        'category': category,
        'count': len(collections),
        'collections': [{
            'id': c.id,
            'name': c.name,
            'document_count': c.document_count,
        } for c in collections]
    })
