"""
Legal Resource Library Service
Comprehensive service for managing and searching legal documents
"""

from auth.legal_library_models import (
    LegalDocument, DocumentCollection, SearchIndex, DocumentComment,
    SavedDocument, DocumentVersion, DocumentCategory, DocumentStatus
)
from auth.models import db
from datetime import datetime
from sqlalchemy import or_, and_, func
import json
import hashlib


class LegalLibraryService:
    """Service for managing legal resource library"""
    
    @staticmethod
    def add_document(title, category, content_dict):
        """Add a new legal document"""
        doc = LegalDocument(
            title=title,
            category=category,
            status=content_dict.get('status', 'published'),
            full_text=content_dict.get('full_text'),
            summary=content_dict.get('summary'),
            syllabus=content_dict.get('syllabus'),
            case_number=content_dict.get('case_number'),
            docket_number=content_dict.get('docket_number'),
            date_decided=content_dict.get('date_decided'),
            date_filed=content_dict.get('date_filed'),
            court=content_dict.get('court'),
            jurisdiction=content_dict.get('jurisdiction'),
            petitioner=content_dict.get('petitioner'),
            respondent=content_dict.get('respondent'),
            citation_supreme=content_dict.get('citation_supreme'),
            citation_reporter=content_dict.get('citation_reporter'),
            citation_westlaw=content_dict.get('citation_westlaw'),
            citation_lexis=content_dict.get('citation_lexis'),
            author=content_dict.get('author'),
            justices_concur=content_dict.get('justices_concur'),
            justices_dissent=content_dict.get('justices_dissent'),
            issues=content_dict.get('issues'),
            keywords=content_dict.get('keywords'),
            headnotes=content_dict.get('headnotes'),
            related_cases=content_dict.get('related_cases'),
            statutes_cited=content_dict.get('statutes_cited'),
            cases_cited=content_dict.get('cases_cited'),
            url_supremecourt=content_dict.get('url_supremecourt'),
            url_google_scholar=content_dict.get('url_google_scholar'),
            url_justia=content_dict.get('url_justia'),
            import_source=content_dict.get('import_source'),
        )
        
        # Calculate file hash for deduplication
        if content_dict.get('full_text'):
            doc.file_hash = hashlib.sha256(
                content_dict.get('full_text').encode()
            ).hexdigest()
        
        db.session.add(doc)
        db.session.commit()
        
        # Add to search index
        LegalLibraryService.index_document(doc.id)
        
        return doc
    
    @staticmethod
    def index_document(document_id):
        """Add document to search index"""
        doc = LegalDocument.query.get(document_id)
        if not doc:
            return False
        
        # Combine all searchable fields
        search_text = ' '.join(filter(None, [
            doc.title,
            doc.case_number,
            doc.petitioner,
            doc.respondent,
            doc.summary,
            ' '.join(doc.keywords) if doc.keywords else '',
            ' '.join(doc.issues) if doc.issues else '',
            doc.full_text[:2000] if doc.full_text else '',  # First 2000 chars
        ]))
        
        index = SearchIndex(
            document_id=document_id,
            search_text=search_text
        )
        db.session.add(index)
        doc.indexed_at = datetime.utcnow()
        db.session.commit()
        
        return True
    
    @staticmethod
    def search_documents(query, category=None, date_range=None, limit=50):
        """Search legal documents"""
        search_query = LegalDocument.query
        
        # Full text search
        if query:
            search_query = search_query.filter(
                or_(
                    LegalDocument.title.ilike(f'%{query}%'),
                    LegalDocument.case_number.ilike(f'%{query}%'),
                    LegalDocument.petitioner.ilike(f'%{query}%'),
                    LegalDocument.respondent.ilike(f'%{query}%'),
                    LegalDocument.keywords.astext.ilike(f'%{query}%'),
                    LegalDocument.summary.ilike(f'%{query}%'),
                    db.func.to_tsvector('english', LegalDocument.full_text).match(
                        db.func.plainto_tsquery('english', query)
                    )
                )
            )
        
        # Category filter
        if category:
            search_query = search_query.filter_by(category=category)
        
        # Date range filter
        if date_range:
            start_date, end_date = date_range
            search_query = search_query.filter(
                and_(
                    LegalDocument.date_decided >= start_date,
                    LegalDocument.date_decided <= end_date
                )
            )
        
        # Exclude withdrawn documents
        search_query = search_query.filter_by(status=DocumentStatus.PUBLISHED.value)
        
        # Order by relevance and date
        results = search_query.order_by(
            LegalDocument.date_decided.desc()
        ).limit(limit).all()
        
        return results
    
    @staticmethod
    def get_document_by_case_number(case_number):
        """Get document by case number"""
        return LegalDocument.query.filter_by(case_number=case_number).first()
    
    @staticmethod
    def get_documents_by_keyword(keyword, limit=50):
        """Find documents with keyword"""
        return LegalDocument.query.filter(
            LegalDocument.keywords.astext.ilike(f'%{keyword}%')
        ).limit(limit).all()
    
    @staticmethod
    def get_documents_by_justice(justice_name):
        """Get documents authored by or involving specific justice"""
        return LegalDocument.query.filter(
            or_(
                LegalDocument.author.ilike(f'%{justice_name}%'),
                LegalDocument.justices_concur.astext.ilike(f'%{justice_name}%'),
                LegalDocument.justices_dissent.astext.ilike(f'%{justice_name}%'),
            )
        ).all()
    
    @staticmethod
    def get_related_cases(document_id):
        """Get cases related to a document"""
        doc = LegalDocument.query.get(document_id)
        if not doc or not doc.related_cases:
            return []
        
        related_ids = [rc.get('case_id') for rc in doc.related_cases]
        return LegalDocument.query.filter(LegalDocument.id.in_(related_ids)).all()
    
    @staticmethod
    def get_citing_cases(case_number, limit=100):
        """Get cases that cite a specific case"""
        return LegalDocument.query.filter(
            LegalDocument.cases_cited.astext.ilike(f'%{case_number}%')
        ).limit(limit).all()
    
    @staticmethod
    def create_collection(name, category, description=None):
        """Create a collection"""
        collection = DocumentCollection(
            name=name,
            category=category,
            description=description,
            document_ids=[]
        )
        db.session.add(collection)
        db.session.commit()
        return collection
    
    @staticmethod
    def add_to_collection(collection_id, document_id):
        """Add document to collection"""
        collection = DocumentCollection.query.get(collection_id)
        doc = LegalDocument.query.get(document_id)
        
        if not collection or not doc:
            return False
        
        if collection.document_ids is None:
            collection.document_ids = []
        
        if document_id not in collection.document_ids:
            collection.document_ids.append(document_id)
            collection.document_count = len(collection.document_ids)
            db.session.commit()
        
        return True
    
    @staticmethod
    def get_collection(collection_id):
        """Get collection with documents"""
        collection = DocumentCollection.query.get(collection_id)
        if collection and collection.document_ids:
            collection.documents = LegalDocument.query.filter(
                LegalDocument.id.in_(collection.document_ids)
            ).all()
        return collection
    
    @staticmethod
    def save_document(user_id, document_id, folder=None, note=None):
        """Save document for user"""
        saved = SavedDocument(
            user_id=user_id,
            document_id=document_id,
            folder=folder,
            note=note
        )
        db.session.add(saved)
        db.session.commit()
        return saved
    
    @staticmethod
    def get_user_saved_documents(user_id, folder=None):
        """Get user's saved documents"""
        query = SavedDocument.query.filter_by(user_id=user_id)
        if folder:
            query = query.filter_by(folder=folder)
        
        saved = query.all()
        document_ids = [s.document_id for s in saved]
        
        return LegalDocument.query.filter(LegalDocument.id.in_(document_ids)).all()
    
    @staticmethod
    def add_comment(user_id, document_id, comment, highlight_text=None):
        """Add comment to document"""
        doc_comment = DocumentComment(
            user_id=user_id,
            document_id=document_id,
            comment=comment,
            highlight_text=highlight_text
        )
        db.session.add(doc_comment)
        db.session.commit()
        return doc_comment
    
    @staticmethod
    def get_document_comments(document_id):
        """Get all comments on document"""
        return DocumentComment.query.filter_by(document_id=document_id).order_by(
            DocumentComment.created_at.desc()
        ).all()
    
    @staticmethod
    def increment_view_count(document_id):
        """Increment view count for a document"""
        doc = LegalDocument.query.get(document_id)
        if doc:
            doc.view_count = (doc.view_count or 0) + 1
            db.session.commit()
    
    @staticmethod
    def get_trending_documents(days=30, limit=20):
        """Get most viewed documents in timeframe"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return LegalDocument.query.filter(
            LegalDocument.updated_at >= cutoff_date
        ).order_by(LegalDocument.view_count.desc()).limit(limit).all()
    
    @staticmethod
    def get_recent_documents(limit=50):
        """Get recently added documents"""
        return LegalDocument.query.order_by(
            LegalDocument.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_statistics():
        """Get library statistics"""
        total_docs = db.session.query(func.count(LegalDocument.id)).scalar()
        supreme_court = db.session.query(func.count(LegalDocument.id)).filter_by(
            category=DocumentCategory.SUPREME_COURT.value
        ).scalar()
        founding = db.session.query(func.count(LegalDocument.id)).filter_by(
            category=DocumentCategory.FOUNDING_DOCUMENT.value
        ).scalar()
        amendments = db.session.query(func.count(LegalDocument.id)).filter_by(
            category=DocumentCategory.AMENDMENT.value
        ).scalar()
        
        return {
            'total_documents': total_docs or 0,
            'supreme_court_cases': supreme_court or 0,
            'founding_documents': founding or 0,
            'amendments': amendments or 0,
            'collections': db.session.query(func.count(DocumentCollection.id)).scalar() or 0,
        }
