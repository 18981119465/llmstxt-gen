"""
文档模型
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin, ActivatedMixin


class Document(Base, TimestampMixin, ActivatedMixin):
    """文档模型"""
    __tablename__ = 'documents'
    
    # 基本信息
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # pdf, word, markdown, html, text, etc.
    source_url = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    file_hash = Column(String(64), nullable=True, index=True)  # MD5 or SHA256
    
    # 文档状态
    status = Column(String(20), default='pending', nullable=False)  # pending, processing, completed, failed
    processing_status = Column(String(20), default='pending', nullable=False)  # pending, extracting, analyzing, indexing, done
    error_message = Column(Text, nullable=True)
    
    # 文档内容
    content_preview = Column(Text, nullable=True)
    content_length = Column(Integer, nullable=True)  # characters
    language = Column(String(10), nullable=True)  # en, zh, etc.
    
    # 文档属性
    is_processed = Column(Boolean, default=False, nullable=False)
    is_indexed = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_encrypted = Column(Boolean, default=False, nullable=False)
    
    # 处理信息
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    indexed_at = Column(DateTime, nullable=True)
    
    # 统计信息
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    
    # 关联关系
    project = relationship("Project", back_populates="documents")
    content = relationship("DocumentContent", back_populates="document", uselist=False)
    doc_metadata = relationship("DocumentMetadata", back_populates="document", uselist=False)
    tasks = relationship("Task", back_populates="document")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        document_dict = {
            'project_id': str(self.project_id),
            'name': self.name,
            'type': self.type,
            'source_url': self.source_url,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'status': self.status,
            'processing_status': self.processing_status,
            'error_message': self.error_message,
            'content_preview': self.content_preview,
            'content_length': self.content_length,
            'language': self.language,
            'is_processed': self.is_processed,
            'is_indexed': self.is_indexed,
            'is_public': self.is_public,
            'is_encrypted': self.is_encrypted,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'indexed_at': self.indexed_at.isoformat() if self.indexed_at else None,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'project': self.project.to_dict() if self.project else None
        }
        return {**base_dict, **document_dict}


class DocumentContent(Base, TimestampMixin):
    """文档内容模型"""
    __tablename__ = 'document_contents'
    
    # 内容信息
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    raw_content = Column(Text, nullable=True)  # 原始内容
    cleaned_content = Column(Text, nullable=True)  # 清理后的内容
    structured_content = Column(JSONB, nullable=True)  # 结构化内容
    
    # 内容分析
    summary = Column(Text, nullable=True)
    keywords = Column(JSONB, nullable=True)  # 关键词列表
    topics = Column(JSONB, nullable=True)  # 主题列表
    entities = Column(JSONB, nullable=True)  # 实体列表
    sentiment = Column(JSONB, nullable=True)  # 情感分析
    
    # 内容质量
    quality_score = Column(Integer, nullable=True)  # 0-100
    readability_score = Column(Integer, nullable=True)  # 0-100
    relevance_score = Column(Integer, nullable=True)  # 0-100
    
    # 内容统计
    word_count = Column(Integer, nullable=True)
    sentence_count = Column(Integer, nullable=True)
    paragraph_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    
    # 处理信息
    processed_at = Column(DateTime, default=func.now(), nullable=False)
    processed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    processing_version = Column(Integer, default=1, nullable=False)
    
    # 关联关系
    document = relationship("Document", back_populates="content")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        content_dict = {
            'document_id': str(self.document_id),
            'content': self.content,
            'raw_content': self.raw_content,
            'cleaned_content': self.cleaned_content,
            'structured_content': self.structured_content,
            'summary': self.summary,
            'keywords': self.keywords,
            'topics': self.topics,
            'entities': self.entities,
            'sentiment': self.sentiment,
            'quality_score': self.quality_score,
            'readability_score': self.readability_score,
            'relevance_score': self.relevance_score,
            'word_count': self.word_count,
            'sentence_count': self.sentence_count,
            'paragraph_count': self.paragraph_count,
            'character_count': self.character_count,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processing_version': self.processing_version
        }
        return {**base_dict, **content_dict}


class DocumentMetadata(Base, TimestampMixin):
    """文档元数据模型"""
    __tablename__ = 'document_metadata'
    
    # 元数据信息
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False, unique=True)
    meta_data = Column(JSONB, nullable=False)  # 完整元数据
    
    # 文件元数据
    file_metadata = Column(JSONB, nullable=True)  # 文件特定元数据
    document_metadata = Column(JSONB, nullable=True)  # 文档特定元数据
    
    # PDF元数据
    pdf_title = Column(String(500), nullable=True)
    pdf_author = Column(String(255), nullable=True)
    pdf_subject = Column(String(500), nullable=True)
    pdf_keywords = Column(String(500), nullable=True)
    pdf_creator = Column(String(255), nullable=True)
    pdf_producer = Column(String(255), nullable=True)
    pdf_creation_date = Column(DateTime, nullable=True)
    pdf_modification_date = Column(DateTime, nullable=True)
    pdf_page_count = Column(Integer, nullable=True)
    
    # Word文档元数据
    word_title = Column(String(500), nullable=True)
    word_author = Column(String(255), nullable=True)
    word_subject = Column(String(500), nullable=True)
    word_keywords = Column(String(500), nullable=True)
    word_creation_date = Column(DateTime, nullable=True)
    word_modification_date = Column(DateTime, nullable=True)
    word_page_count = Column(Integer, nullable=True)
    word_word_count = Column(Integer, nullable=True)
    
    # HTML元数据
    html_title = Column(String(500), nullable=True)
    html_description = Column(String(1000), nullable=True)
    html_keywords = Column(String(500), nullable=True)
    html_author = Column(String(255), nullable=True)
    html_canonical_url = Column(Text, nullable=True)
    html_og_title = Column(String(500), nullable=True)
    html_og_description = Column(String(1000), nullable=True)
    html_og_image = Column(Text, nullable=True)
    
    # 爬取元数据
    crawl_source = Column(String(255), nullable=True)
    crawl_url = Column(Text, nullable=True)
    crawl_date = Column(DateTime, nullable=True)
    crawl_depth = Column(Integer, nullable=True)
    crawl_status = Column(String(50), nullable=True)
    crawl_user_agent = Column(String(500), nullable=True)
    crawl_ip_address = Column(String(45), nullable=True)
    
    # 处理信息
    extracted_at = Column(DateTime, default=func.now(), nullable=False)
    extracted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    extraction_version = Column(Integer, default=1, nullable=False)
    
    # 关联关系
    document = relationship("Document", back_populates="doc_metadata")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        metadata_dict = {
            'document_id': str(self.document_id),
            'metadata': self.meta_data,
            'file_metadata': self.file_metadata,
            'document_metadata': self.document_metadata,
            'pdf_title': self.pdf_title,
            'pdf_author': self.pdf_author,
            'pdf_subject': self.pdf_subject,
            'pdf_keywords': self.pdf_keywords,
            'pdf_creator': self.pdf_creator,
            'pdf_producer': self.pdf_producer,
            'pdf_creation_date': self.pdf_creation_date.isoformat() if self.pdf_creation_date else None,
            'pdf_modification_date': self.pdf_modification_date.isoformat() if self.pdf_modification_date else None,
            'pdf_page_count': self.pdf_page_count,
            'word_title': self.word_title,
            'word_author': self.word_author,
            'word_subject': self.word_subject,
            'word_keywords': self.word_keywords,
            'word_creation_date': self.word_creation_date.isoformat() if self.word_creation_date else None,
            'word_modification_date': self.word_modification_date.isoformat() if self.word_modification_date else None,
            'word_page_count': self.word_page_count,
            'word_word_count': self.word_word_count,
            'html_title': self.html_title,
            'html_description': self.html_description,
            'html_keywords': self.html_keywords,
            'html_author': self.html_author,
            'html_canonical_url': self.html_canonical_url,
            'html_og_title': self.html_og_title,
            'html_og_description': self.html_og_description,
            'html_og_image': self.html_og_image,
            'crawl_source': self.crawl_source,
            'crawl_url': self.crawl_url,
            'crawl_date': self.crawl_date.isoformat() if self.crawl_date else None,
            'crawl_depth': self.crawl_depth,
            'crawl_status': self.crawl_status,
            'crawl_user_agent': self.crawl_user_agent,
            'crawl_ip_address': self.crawl_ip_address,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'extraction_version': self.extraction_version
        }
        return {**base_dict, **metadata_dict}


class DocumentVersion(Base, TimestampMixin):
    """文档版本模型"""
    __tablename__ = 'document_versions'
    
    # 版本信息
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    # 版本内容
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)
    content_preview = Column(Text, nullable=True)
    
    # 版本状态
    is_current = Column(Boolean, default=False, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default='draft', nullable=False)
    
    # 版本信息
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    published_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    
    # 关联关系
    document = relationship("Document")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        version_dict = {
            'document_id': str(self.document_id),
            'version_number': self.version_number,
            'version_name': self.version_name,
            'description': self.description,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'content_preview': self.content_preview,
            'is_current': self.is_current,
            'is_published': self.is_published,
            'status': self.status,
            'created_by': str(self.created_by),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'created_by_user': self.created_by_user.to_dict() if self.created_by_user else None
        }
        return {**base_dict, **version_dict}


class DocumentTag(Base, TimestampMixin):
    """文档标签模型"""
    __tablename__ = 'document_tags'
    
    # 标签信息
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    tag_name = Column(String(50), nullable=False)
    tag_type = Column(String(20), default='manual', nullable=False)  # manual, auto, system
    confidence = Column(Integer, default=100, nullable=False)  # 0-100
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # 关联关系
    document = relationship("Document")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        tag_dict = {
            'document_id': str(self.document_id),
            'tag_name': self.tag_name,
            'tag_type': self.tag_type,
            'confidence': self.confidence,
            'created_by': str(self.created_by) if self.created_by else None,
            'created_by_user': self.created_by_user.to_dict() if self.created_by_user else None
        }
        return {**base_dict, **tag_dict}


class DocumentComment(Base, TimestampMixin):
    """文档评论模型"""
    __tablename__ = 'document_comments'
    
    # 评论信息
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    
    # 评论属性
    parent_id = Column(UUID(as_uuid=True), ForeignKey('document_comments.id'), nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)
    
    # 评论状态
    status = Column(String(20), default='active', nullable=False)  # active, resolved, deleted
    
    # 关联关系
    document = relationship("Document")
    user = relationship("User")
    parent = relationship("DocumentComment", remote_side=[id])
    replies = relationship("DocumentComment", back_populates="parent")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        comment_dict = {
            'document_id': str(self.document_id),
            'user_id': str(self.user_id),
            'content': self.content,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'is_resolved': self.is_resolved,
            'is_internal': self.is_internal,
            'status': self.status,
            'user': self.user.to_dict() if self.user else None,
            'parent': self.parent.to_dict() if self.parent else None,
            'replies': [reply.to_dict() for reply in self.replies] if self.replies else []
        }
        return {**base_dict, **comment_dict}