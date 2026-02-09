"""
Chat Admin Routes for Evident
Admin endpoints for API key management and chat statistics
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from auth.chat_models import UserAPIKey, Conversation, Message, db
from auth.api_key_manager import api_key_manager

logger = logging.getLogger(__name__)

# Create blueprint
chat_admin_bp = Blueprint('chat_admin', __name__, url_prefix='/admin/chat')


@chat_admin_bp.before_request
@login_required
def require_admin():
    """Require admin access"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403


# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

@chat_admin_bp.route('/api-keys', methods=['GET'])
def list_all_api_keys():
    """
    List all user API keys (admin view)
    
    GET /admin/chat/api-keys
    """
    try:
        keys = UserAPIKey.query.all()
        
        return jsonify({
            'success': True,
            'api_keys': [key.to_dict() for key in keys],
            'count': len(keys)
        })
    
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        return jsonify({'error': 'Failed to list API keys'}), 500


@chat_admin_bp.route('/api-keys/<key_id>', methods=['DELETE'])
def delete_user_api_key(key_id: str):
    """
    Delete a user's API key (admin override)
    
    DELETE /admin/chat/api-keys/{key_id}
    """
    try:
        user_key = UserAPIKey.query.get(key_id)
        
        if not user_key:
            return jsonify({'error': 'API key not found'}), 404
        
        db.session.delete(user_key)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'API key for user {user_key.user_id} deleted'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting API key: {e}")
        return jsonify({'error': 'Failed to delete API key'}), 500


@chat_admin_bp.route('/api-keys/user/<int:user_id>', methods=['GET'])
def get_user_api_keys(user_id: int):
    """
    Get all API keys for a specific user (admin view)
    
    GET /admin/chat/api-keys/user/{user_id}
    """
    try:
        keys = UserAPIKey.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'api_keys': [key.to_dict() for key in keys],
            'count': len(keys)
        })
    
    except Exception as e:
        logger.error(f"Error getting user API keys: {e}")
        return jsonify({'error': 'Failed to get user API keys'}), 500


# ============================================================================
# CHAT STATISTICS AND MONITORING
# ============================================================================

@chat_admin_bp.route('/statistics', methods=['GET'])
def get_chat_statistics():
    """
    Get overall chat statistics
    
    GET /admin/chat/statistics
    """
    try:
        total_conversations = Conversation.query.count()
        total_messages = Message.query.count()
        total_api_keys = UserAPIKey.query.count()
        
        # Get top users by conversation count
        from sqlalchemy import desc
        top_users = (
            db.session.query(
                Conversation.user_id,
                db.func.count(Conversation.id).label('con_count'),
                db.func.sum(Conversation.total_input_tokens).label('total_input'),
                db.func.sum(Conversation.total_output_tokens).label('total_output')
            )
            .group_by(Conversation.user_id)
            .order_by(desc(db.func.count(Conversation.id)))
            .limit(10)
            .all()
        )
        
        top_users_data = [
            {
                'user_id': u[0],
                'conversations': u[1],
                'total_input_tokens': u[2] or 0,
                'total_output_tokens': u[3] or 0,
            }
            for u in top_users
        ]
        
        # Get API key usage statistics
        api_key_stats = (
            db.session.query(
                UserAPIKey.service_name,
                db.func.count(UserAPIKey.id).label('count'),
                db.func.sum(UserAPIKey.total_requests).label('total_requests'),
                db.func.sum(UserAPIKey.total_cost).label('total_cost'),
            )
            .group_by(UserAPIKey.service_name)
            .all()
        )
        
        api_key_stats_data = [
            {
                'service': s[0],
                'key_count': s[1],
                'total_requests': s[2] or 0,
                'total_cost': float(s[3] or 0),
            }
            for s in api_key_stats
        ]
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'total_api_keys': total_api_keys,
                'top_users': top_users_data,
                'api_key_stats': api_key_stats_data,
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500


@chat_admin_bp.route('/user/<int:user_id>/conversations', methods=['GET'])
def get_user_conversations(user_id: int):
    """
    Get all conversations for a user (admin view)
    
    GET /admin/chat/user/{user_id}/conversations
    """
    try:
        conversations = Conversation.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'conversations': [c.to_dict() for c in conversations],
            'count': len(conversations)
        })
    
    except Exception as e:
        logger.error(f"Error getting user conversations: {e}")
        return jsonify({'error': 'Failed to get conversations'}), 500


@chat_admin_bp.route('/conversation/<conv_id>/messages', methods=['GET'])
def get_conversation_messages(conv_id: str):
    """
    Get all messages in a conversation (admin view)
    
    GET /admin/chat/conversation/{conv_id}/messages
    """
    try:
        messages = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at.asc()).all()
        
        return jsonify({
            'success': True,
            'conversation_id': conv_id,
            'messages': [m.to_dict() for m in messages],
            'count': len(messages)
        })
    
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return jsonify({'error': 'Failed to get messages'}), 500


# ============================================================================
# MAINTENANCE
# ============================================================================

@chat_admin_bp.route('/maintenance/reset-monthly-costs', methods=['POST'])
def reset_monthly_costs():
    """
    Reset monthly costs for all users (call at start of month)
    
    POST /admin/chat/maintenance/reset-monthly-costs
    """
    try:
        keys = UserAPIKey.query.all()
        for key in keys:
            key.monthly_cost = 0.0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Reset monthly costs for {len(keys)} API keys'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting monthly costs: {e}")
        return jsonify({'error': 'Failed to reset monthly costs'}), 500


@chat_admin_bp.route('/maintenance/cleanup-old-messages', methods=['POST'])
def cleanup_old_messages():
    """
    Archive messages older than 90 days
    
    POST /admin/chat/maintenance/cleanup-old-messages?days=90
    """
    try:
        from datetime import datetime, timedelta
        
        days = int(request.args.get('days', 90))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_messages = Message.query.filter(Message.created_at < cutoff_date).all()
        
        for msg in old_messages:
            msg.is_deleted = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Marked {len(old_messages)} messages as deleted (older than {days} days)'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cleaning up messages: {e}")
        return jsonify({'error': 'Failed to cleanup messages'}), 500


@chat_admin_bp.route('/maintenance/validate-all-keys', methods=['POST'])
def validate_all_keys():
    """
    Validate all user API keys
    
    POST /admin/chat/maintenance/validate-all-keys
    """
    try:
        keys = UserAPIKey.query.filter_by(is_active=True).all()
        
        results = {
            'valid': 0,
            'invalid': 0,
            'error': 0,
        }
        
        for key in keys:
            is_valid, message = api_key_manager.validate_user_key(key.user_id, key.service_name)
            
            if is_valid:
                results['valid'] += 1
            elif 'error' in message.lower():
                results['error'] += 1
            else:
                results['invalid'] += 1
        
        return jsonify({
            'success': True,
            'validation_results': results,
            'total_keys': len(keys)
        })
    
    except Exception as e:
        logger.error(f"Error validating keys: {e}")
        return jsonify({'error': 'Failed to validate keys'}), 500
