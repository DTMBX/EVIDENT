"""
AI Chat System with Memory & Learning
Phase 10: Chat interface, memory extraction, context-aware responses
"""

from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import logging

Base = declarative_base()
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Project(Base):
    """Legal workspace project"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)  # "Acme Corp Litigation"
    description = Column(Text, nullable=True)
    case_id = Column(Integer, ForeignKey("legal_cases.id"), nullable=True)
    
    # Storage management
    storage_limit_bytes = Column(Integer, nullable=False)
    storage_used_bytes = Column(Integer, default=0)
    
    # Settings
    visibility = Column(String(50), default="private")  # "private", "shared", "team"
    archived = Column(Boolean, default=False)
    
    # Relationships
    documents = relationship("ProjectDocument", back_populates="project")
    chats = relationship("Chat", back_populates="project")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)

class Chat(Base):
    """Chat conversation (persisted)"""
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)  # "Contract Review - Acme Corp"
    
    # System configuration
    system_prompt = Column(Text, nullable=True)  # Custom instructions
    model = Column(String(50), default="gpt-4-turbo")  # Model selection
    
    # Settings
    preserve_context = Column(Boolean, default=True)
    max_context_tokens = Column(Integer, default=4000)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")
    memory_items = relationship("ChatMemory", back_populates="chat", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="chats")

class ChatMessage(Base):
    """Individual message in chat"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    role = Column(String(50), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)  # Message text
    
    # Embeddings for semantic search
    embeddings = Column(JSON, nullable=True)  # [768-dim vector]
    
    # Citations and context
    citations = Column(JSON, default=[])  # ["doc_123", "doc_456"]
    context_used = Column(JSON, nullable=True)  # What context was used for response
    
    # Message metadata
    tokens_used = Column(Integer, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")

class ChatMemory(Base):
    """Learned facts from chat interactions"""
    __tablename__ = "chat_memory"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    
    # The learnable fact
    key = Column(String(100), nullable=False)  # "defendant", "damages_claimed", "court"
    value = Column(Text, nullable=False)  # The actual value
    
    # Metadata
    category = Column(String(50), nullable=False)  # "case_fact", "legal_principle", "custom"
    confidence = Column(Float, default=0.95)  # How sure we are (0-1)
    
    # Traceability
    source_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    learned_at = Column(DateTime, default=datetime.utcnow)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)  # Times referenced in responses
    last_used_at = Column(DateTime, nullable=True)
    
    # Embeddings for semantic search
    embeddings = Column(JSON, nullable=True)
    
    # Relationships
    chat = relationship("Chat", back_populates="memory_items")

class ProjectDocument(Base):
    """Document uploaded to project (from batch_document_processing.py)"""
    __tablename__ = "project_documents"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash_sha256 = Column(String(64), unique=True)
    
    file_path = Column(Text, nullable=False)
    storage_location = Column(String(50), nullable=False)
    
    processing_status = Column(String(50), default="uploaded")
    ocr_applied = Column(Boolean, default=False)
    ocr_confidence = Column(Float, default=0.0)
    
    text_extracted = Column(Text, nullable=True)
    text_length = Column(Integer, default=0)
    
    page_count = Column(Integer, nullable=True)
    
    document_type = Column(String(50), nullable=True)
    tags = Column(JSON, default=[])
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="documents")

# ============================================================================
# SERVICE CLASSES
# ============================================================================

class ChatMemoryService:
    """Extract, store, and retrieve learned facts from conversations"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def extract_facts_from_message(self, message: str) -> list:
        """
        Extract learnable facts from user message
        
        Returns:
            [{
                'key': 'defendant',
                'value': 'Acme Corp',
                'category': 'case_fact',
                'confidence': 0.95
            }]
        """
        from transformers import pipeline
        
        # Use token classification for fact extraction
        qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
        
        # Common legal facts to extract
        extraction_prompts = [
            {"question": "Who is the defendant?", "context": message},
            {"question": "Who is the plaintiff?", "context": message},
            {"question": "What is the case number?", "context": message},
            {"question": "What court is handling this case?", "context": message},
            {"question": "What damages are claimed?", "context": message},
            {"question": "What is the case type?", "context": message},
        ]
        
        facts = []
        
        for prompt in extraction_prompts:
            try:
                result = qa_pipeline(prompt)
                
                if result['score'] > 0.7:  # High confidence
                    fact_map = {
                        "Who is the defendant?": ("defendant", "case_fact"),
                        "Who is the plaintiff?": ("plaintiff", "case_fact"),
                        "What is the case number?": ("case_number", "case_fact"),
                        "What court is handling this case?": ("court", "case_fact"),
                        "What damages are claimed?": ("damages_claimed", "case_fact"),
                        "What is the case type?": ("case_type", "case_fact"),
                    }
                    
                    key, category = fact_map.get(prompt["question"], (None, None))
                    if key:
                        facts.append({
                            'key': key,
                            'value': result['answer'],
                            'category': category,
                            'confidence': result['score']
                        })
            
            except Exception as e:
                self.logger.debug(f"Fact extraction error: {str(e)}")
        
        return facts
    
    async def retrieve_relevant_memory(self, context: str, top_k: int = 5) -> list:
        """
        Find relevant learned facts for response generation
        
        Args:
            context: Current conversation context
            top_k: Number of memory items to retrieve
        
        Returns:
            List of ChatMemory objects, sorted by relevance
        """
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # Generate embedding for context
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        context_embedding = embedder.encode(context)
        
        # Retrieve all memory items (in production: use vector DB)
        memory_items = self.db.query(ChatMemory).all()
        
        # Calculate similarity scores
        similarities = []
        
        for item in memory_items:
            if item.embeddings:
                item_embedding = np.array(item.embeddings)
                similarity = np.dot(context_embedding, item_embedding)
                similarities.append((item, similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, score in similarities[:top_k]]
    
    async def learn_facts(self, chat_id: int, message_id: int, facts: list):
        """Store learned facts in memory"""
        
        for fact in facts:
            memory_item = ChatMemory(
                chat_id=chat_id,
                source_message_id=message_id,
                key=fact['key'],
                value=fact['value'],
                category=fact['category'],
                confidence=fact['confidence']
            )
            
            self.db.add(memory_item)
        
        self.db.commit()

class ChatService:
    """Chat message creation, retrieval, and conversation management"""
    
    def __init__(self, db_session, llm_client):
        self.db = db_session
        self.llm = llm_client  # OpenAI, Anthropic, etc.
        self.memory_service = ChatMemoryService(db_session)
        self.logger = logging.getLogger(__name__)
    
    async def create_chat(self, project_id: int, user_id: int, title: str, system_prompt: str = None):
        """Create new chat conversation"""
        
        chat = Chat(
            project_id=project_id,
            user_id=user_id,
            title=title,
            system_prompt=system_prompt
        )
        
        self.db.add(chat)
        self.db.commit()
        
        return chat
    
    async def send_message(self, chat_id: int, user_id: int, content: str, include_project_context: bool = True):
        """
        Send user message and get AI response
        
        Returns:
            {
                'message_id': int,
                'content': str,
                'memory_updated': bool,
                'facts_learned': int,
                'processing_time_seconds': float
            }
        """
        import time
        
        start_time = time.time()
        
        # Store user message
        user_message = ChatMessage(
            chat_id=chat_id,
            user_id=user_id,
            role="user",
            content=content
        )
        
        self.db.add(user_message)
        self.db.commit()
        
        # Extract facts from user message
        facts = await self.memory_service.extract_facts_from_message(content)
        
        if facts:
            await self.memory_service.learn_facts(chat_id, user_message.id, facts)
        
        # Retrieve relevant memory
        relevant_memory = await self.memory_service.retrieve_relevant_memory(content)
        
        # Build context for LLM
        memory_context = self._build_memory_context(relevant_memory)
        
        # Get project context if requested
        project_context = ""
        if include_project_context:
            project_context = await self._get_project_context(chat_id)
        
        # Build system prompt
        chat = self.db.query(Chat).filter(Chat.id == chat_id).one()
        
        system_prompt = f"""
You are a legal expert assistant specializing in e-discovery and case management.

LEARNED INFORMATION:
{memory_context}

PROJECT CONTEXT:
{project_context}

{chat.system_prompt or ''}

Use the learned information and project context to provide better responses.
Cite sources when possible.
"""
        
        # Get conversation history
        chat_messages = self.db.query(ChatMessage).filter(
            ChatMessage.chat_id == chat_id
        ).order_by(ChatMessage.created_at).all()
        
        # Format for LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in chat_messages[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call LLM
        response = await self.llm.chat.completions.create(
            model=chat.model,
            messages=messages,
            temperature=chat.temperature,
            top_p=chat.top_p,
            max_tokens=1000
        )
        
        assistant_response = response.choices[0].message.content
        
        # Store assistant message
        assistant_message = ChatMessage(
            chat_id=chat_id,
            role="assistant",
            content=assistant_response,
            tokens_used=response.usage.total_tokens,
            processing_time_seconds=time.time() - start_time
        )
        
        self.db.add(assistant_message)
        self.db.commit()
        
        return {
            'message_id': assistant_message.id,
            'content': assistant_response,
            'memory_updated': len(facts) > 0,
            'facts_learned': len(facts),
            'processing_time_seconds': time.time() - start_time
        }
    
    def _build_memory_context(self, memory_items: list) -> str:
        """Format remembered facts for LLM context"""
        
        if not memory_items:
            return "No prior knowledge."
        
        context = "Learning from this conversation:\n"
        
        for item in memory_items:
            context += f"- {item.key}: {item.value} (confidence: {item.confidence:.1%})\n"
        
        return context
    
    async def _get_project_context(self, chat_id: int) -> str:
        """Get project information for context"""
        
        chat = self.db.query(Chat).filter(Chat.id == chat_id).one()
        project = chat.project
        
        # Get recent documents
        documents = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id
        ).order_by(ProjectDocument.uploaded_at.desc()).limit(5).all()
        
        context = f"""
Project: {project.name}
Documents uploaded: {len(project.documents)}
Recent files: {', '.join([d.original_filename for d in documents])}
"""
        
        return context
    
    async def get_chat_history(self, chat_id: int, limit: int = 50) -> list:
        """Get chat message history"""
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.chat_id == chat_id
        ).order_by(ChatMessage.created_at).limit(limit).all()
        
        return [
            {
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'created_at': m.created_at
            }
            for m in messages
        ]
    
    async def get_chat_memory(self, chat_id: int) -> list:
        """Get all learned facts for chat"""
        
        memory_items = self.db.query(ChatMemory).filter(
            ChatMemory.chat_id == chat_id
        ).all()
        
        return [
            {
                'key': m.key,
                'value': m.value,
                'category': m.category,
                'confidence': m.confidence,
                'learned_at': m.learned_at,
                'usage_count': m.usage_count
            }
            for m in memory_items
        ]

class ProjectManagementService:
    """Manage projects (containers for cases, documents, chats)"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def create_project(self, user_id: int, name: str, description: str = None, storage_limit_bytes: int = 5_000_000_000):
        """Create new project (5GB default for free, unlimited for enterprise)"""
        
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            storage_limit_bytes=storage_limit_bytes
        )
        
        self.db.add(project)
        self.db.commit()
        
        return project
    
    async def get_project(self, project_id: int) -> dict:
        """Get project details"""
        
        project = self.db.query(Project).filter(Project.id == project_id).one()
        
        return {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'documents_count': len(project.documents),
            'chats_count': len(project.chats),
            'storage_used_bytes': project.storage_used_bytes,
            'storage_limit_bytes': project.storage_limit_bytes,
            'storage_percentage': (project.storage_used_bytes / project.storage_limit_bytes) * 100,
            'created_at': project.created_at,
            'last_accessed': project.last_accessed
        }
    
    async def upload_documents(self, project_id: int, file_paths: list):
        """Upload multiple documents to project"""
        
        project = self.db.query(Project).filter(Project.id == project_id).one()
        
        total_size = sum([os.path.getsize(f) for f in file_paths])
        
        # Check storage limit
        if project.storage_used_bytes + total_size > project.storage_limit_bytes:
            raise ValueError("Insufficient storage")
        
        documents = []
        
        for file_path in file_paths:
            import os
            import hashlib
            
            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            doc = ProjectDocument(
                project_id=project_id,
                filename=os.path.basename(file_path),
                original_filename=os.path.basename(file_path),
                file_type=os.path.splitext(file_path)[1],
                file_size_bytes=os.path.getsize(file_path),
                file_hash_sha256=file_hash,
                file_path=file_path,
                storage_location="local"  # or "s3"
            )
            
            self.db.add(doc)
            documents.append(doc)
        
        project.storage_used_bytes += total_size
        
        self.db.commit()
        
        return documents
    
    async def archive_project(self, project_id: int):
        """Archive project (soft delete)"""
        
        project = self.db.query(Project).filter(Project.id == project_id).one()
        project.archived = True
        
        self.db.commit()

