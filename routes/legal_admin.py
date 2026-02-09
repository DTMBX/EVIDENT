"""
Legal Library Admin Tools
Admin interface for managing document collections and bulk imports
"""

from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from functools import wraps
from auth.legal_library_service import LegalLibraryService
from auth.legal_library_importer import LegalLibraryImporter
from auth.models import db
from datetime import datetime
import json

# Blueprint
legal_admin_bp = Blueprint('legal_admin', __name__, url_prefix='/admin/legal')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@legal_admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Legal library admin dashboard"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Legal Library Admin</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f3f4f6;
                padding: 2rem;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { margin-bottom: 2rem; color: #111827; }
            .card {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            .stat-card {
                background: linear-gradient(135deg, #0b73d2 0%, #1a5ba0 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 8px;
                text-align: center;
            }
            .stat-number { font-size: 2.5rem; font-weight: 700; }
            .stat-label { font-size: 0.95rem; opacity: 0.9; }
            .section-title { font-size: 1.5rem; margin: 2rem 0 1rem; font-weight: 700; }
            button {
                padding: 0.75rem 1.5rem;
                background: #0b73d2;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }
            button:hover { background: #0a5da8; }
            .button-group { display: flex; gap: 1rem; flex-wrap: wrap; }
            input[type="file"], input[type="text"], textarea, select {
                padding: 0.75rem;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-family: inherit;
                width: 100%;
                margin: 0.5rem 0 1rem;
            }
            textarea { min-height: 150px; resize: vertical; }
            .form-group { margin-bottom: 1.5rem; }
            label { font-weight: 600; color: #374151; display: block; margin-bottom: 0.5rem; }
            .success { color: #16a34a; }
            .error { color: #dc2626; }
            .message { padding: 1rem; border-radius: 6px; margin: 1rem 0; }
            .message.success { background: #dcfce7; border-left: 4px solid #16a34a; }
            .message.error { background: #fee2e2; border-left: 4px solid #dc2626; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚖️ Legal Library Admin Dashboard</h1>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalDocs">0</div>
                    <div class="stat-label">Total Documents</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalCollections">0</div>
                    <div class="stat-label">Collections</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="supremeCourtCases">0</div>
                    <div class="stat-label">Supreme Court Cases</div>
                </div>
            </div>
            
            <div class="card">
                <h2 class="section-title">Initialize Library</h2>
                <p>Load founding documents and landmark Supreme Court cases</p>
                <button onclick="initializeLibrary()">Initialize Legal Library</button>
                <div id="initMessage"></div>
            </div>
            
            <div class="card">
                <h2 class="section-title">Bulk Import From CSV</h2>
                <p>Import documents from a CSV file</p>
                <div class="form-group">
                    <label for="csvFile">CSV File:</label>
                    <input type="file" id="csvFile" accept=".csv">
                </div>
                <p>CSV format: title, category, case_number, citation, date, summary, keywords, full_text</p>
                <button onclick="uploadCSV()">Upload CSV</button>
                <div id="csvMessage"></div>
            </div>
            
            <div class="card">
                <h2 class="section-title">Create Document Manually</h2>
                <form onsubmit="createDocument(event)">
                    <div class="form-group">
                        <label for="title">Title:</label>
                        <input type="text" id="title" required>
                    </div>
                    <div class="form-group">
                        <label for="category">Category:</label>
                        <select id="category" required>
                            <option value="supreme_court">Supreme Court Case</option>
                            <option value="amendment">Amendment</option>
                            <option value="founding_document">Founding Document</option>
                            <option value="constitution">Constitution</option>
                            <option value="bill_of_rights">Bill of Rights</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="caseNumber">Case Number:</label>
                        <input type="text" id="caseNumber">
                    </div>
                    <div class="form-group">
                        <label for="dateDecided">Date Decided:</label>
                        <input type="date" id="dateDecided">
                    </div>
                    <div class="form-group">
                        <label for="summary">Summary:</label>
                        <textarea id="summary"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="fullText">Full Text:</label>
                        <textarea id="fullText"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="petitioner">Petitioner:</label>
                        <input type="text" id="petitioner">
                    </div>
                    <div class="form-group">
                        <label for="respondent">Respondent:</label>
                        <input type="text" id="respondent">
                    </div>
                    <button type="submit">Create Document</button>
                </form>
                <div id="createMessage"></div>
            </div>
            
            <div class="card">
                <h2 class="section-title">Create Collection</h2>
                <form onsubmit="createCollection(event)">
                    <div class="form-group">
                        <label for="collName">Collection Name:</label>
                        <input type="text" id="collName" required>
                    </div>
                    <div class="form-group">
                        <label for="collCategory">Category:</label>
                        <input type="text" id="collCategory" placeholder="e.g., civil-rights">
                    </div>
                    <div class="form-group">
                        <label for="collDesc">Description:</label>
                        <textarea id="collDesc"></textarea>
                    </div>
                    <button type="submit">Create Collection</button>
                </form>
                <div id="collectionMessage"></div>
            </div>
        </div>
        
        <script>
            // Load statistics
            async function loadStats() {
                try {
                    const response = await fetch('/api/legal/statistics');
                    const data = await response.json();
                    document.getElementById('totalDocs').textContent = data.total_documents || 0;
                    document.getElementById('totalCollections').textContent = data.collections || 0;
                    document.getElementById('supremeCourtCases').textContent = data.supreme_court_cases || 0;
                } catch (error) {
                    console.error('Error loading statistics:', error);
                }
            }
            
            async function initializeLibrary() {
                if (!confirm('Initialize legal library with founding documents and landmark cases?')) return;
                
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = 'Initializing...';
                
                try {
                    const response = await fetch('/admin/legal/initialize', { method: 'POST' });
                    const data = await response.json();
                    
                    const msgDiv = document.getElementById('initMessage');
                    if (data.success) {
                        msgDiv.className = 'message success';
                        msgDiv.textContent = `✓ ${data.message} (${data.documents_added} documents added)`;
                        loadStats();
                    } else {
                        msgDiv.className = 'message error';
                        msgDiv.textContent = `✗ Error: ${data.error}`;
                    }
                } catch (error) {
                    document.getElementById('initMessage').textContent = `✗ Error: ${error}`;
                } finally {
                    btn.disabled = false;
                    btn.textContent = 'Initialize Legal Library';
                }
            }
            
            async function uploadCSV() {
                const file = document.getElementById('csvFile').files[0];
                if (!file) {
                    alert('Please select a CSV file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/admin/legal/import-csv', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    
                    const msgDiv = document.getElementById('csvMessage');
                    if (data.success) {
                        msgDiv.className = 'message success';
                        msgDiv.textContent = `✓ ${data.documents_imported} documents imported`;
                        loadStats();
                    } else {
                        msgDiv.className = 'message error';
                        msgDiv.textContent = `✗ Error: ${data.error}`;
                    }
                } catch (error) {
                    document.getElementById('csvMessage').textContent = `✗ Error: ${error}`;
                }
            }
            
            async function createDocument(event) {
                event.preventDefault();
                
                const data = {
                    title: document.getElementById('title').value,
                    category: document.getElementById('category').value,
                    content_dict: {
                        case_number: document.getElementById('caseNumber').value,
                        date_decided: document.getElementById('dateDecided').value,
                        summary: document.getElementById('summary').value,
                        full_text: document.getElementById('fullText').value,
                        petitioner: document.getElementById('petitioner').value,
                        respondent: document.getElementById('respondent').value,
                    }
                };
                
                try {
                    const response = await fetch('/api/legal/documents', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    
                    const msgDiv = document.getElementById('createMessage');
                    if (result.document_id || result.success) {
                        msgDiv.className = 'message success';
                        msgDiv.textContent = '✓ Document created successfully';
                        event.target.reset();
                        loadStats();
                    } else {
                        msgDiv.className = 'message error';
                        msgDiv.textContent = `✗ Error: ${result.error}`;
                    }
                } catch (error) {
                    document.getElementById('createMessage').textContent = `✗ Error: ${error}`;
                }
            }
            
            async function createCollection(event) {
                event.preventDefault();
                
                const data = {
                    name: document.getElementById('collName').value,
                    category: document.getElementById('collCategory').value,
                    description: document.getElementById('collDesc').value
                };
                
                try {
                    const response = await fetch('/api/legal/collections', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    
                    const msgDiv = document.getElementById('collectionMessage');
                    if (result.collection_id || result.success) {
                        msgDiv.className = 'message success';
                        msgDiv.textContent = '✓ Collection created successfully';
                        event.target.reset();
                        loadStats();
                    } else {
                        msgDiv.className = 'message error';
                        msgDiv.textContent = `✗ Error: ${result.error}`;
                    }
                } catch (error) {
                    document.getElementById('collectionMessage').textContent = `✗ Error: ${error}`;
                }
            }
            
            loadStats();
            setInterval(loadStats, 30000); // Refresh stats every 30s
        </script>
    </body>
    </html>
    ''')


# ============================================================================
# ADMIN API ENDPOINTS
# ============================================================================

@legal_admin_bp.route('/initialize', methods=['POST'])
@admin_required
def initialize():
    """Initialize legal library with default data"""
    try:
        from auth.legal_library_importer import init_legal_library
        init_legal_library()
        
        return jsonify({
            'success': True,
            'message': 'Legal library initialized',
            'documents_added': 50  # Approximate count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@legal_admin_bp.route('/import-csv', methods=['POST'])
@admin_required
def import_csv():
    """Import documents from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        count = LegalLibraryImporter.import_from_csv(file.stream)
        
        return jsonify({
            'success': True,
            'documents_imported': len(count)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@legal_admin_bp.route('/documents/<doc_id>/delete', methods=['DELETE'])
@admin_required
def delete_document(doc_id):
    """Delete a document"""
    try:
        from auth.legal_library_models import LegalDocument
        doc = LegalDocument.query.get(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Document deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@legal_admin_bp.route('/collections/<coll_id>/delete', methods=['DELETE'])
@admin_required
def delete_collection(coll_id):
    """Delete a collection"""
    try:
        from auth.legal_library_models import DocumentCollection
        coll = DocumentCollection.query.get(coll_id)
        if not coll:
            return jsonify({'error': 'Collection not found'}), 404
        
        db.session.delete(coll)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Collection deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@legal_admin_bp.route('/documents/<doc_id>/sync-index', methods=['POST'])
@admin_required
def sync_search_index(doc_id):
    """Re-index document in search index"""
    try:
        from auth.legal_library_models import LegalDocument
        doc = LegalDocument.query.get(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        LegalLibraryService.index_document(doc)
        
        return jsonify({'success': True, 'message': 'Document indexed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
