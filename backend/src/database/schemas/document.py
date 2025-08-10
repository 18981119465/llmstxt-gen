"""
文档相关schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, constr

from .base import BaseSchema, BaseResponse


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    DONE = "done"
    ERROR = "error"


class TagType(str, Enum):
    """标签类型枚举"""
    MANUAL = "manual"
    AUTO = "auto"
    SYSTEM = "system"


class CommentStatus(str, Enum):
    """评论状态枚举"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    DELETED = "deleted"


# 文档schemas
class DocumentBase(BaseSchema):
    """文档基础schema"""
    name: constr(min_length=1, max_length=255) = Field(..., description="文档名称")
    type: DocumentType = Field(..., description="文档类型")
    source_url: Optional[str] = Field(None, description="来源URL")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小(字节)")
    file_hash: Optional[constr(max_length=64)] = Field(None, description="文件哈希")
    is_public: bool = Field(False, description="是否公开")
    is_encrypted: bool = Field(False, description="是否加密")


class DocumentCreate(DocumentBase):
    """文档创建schema"""
    project_id: UUID = Field(..., description="项目ID")
    content_preview: Optional[str] = Field(None, description="内容预览")
    language: Optional[str] = Field(None, description="语言")


class DocumentUpdate(BaseSchema):
    """文档更新schema"""
    name: Optional[constr(max_length=255)] = Field(None, description="文档名称")
    description: Optional[str] = Field(None, description="文档描述")
    source_url: Optional[str] = Field(None, description="来源URL")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小(字节)")
    file_hash: Optional[constr(max_length=64)] = Field(None, description="文件哈希")
    content_preview: Optional[str] = Field(None, description="内容预览")
    language: Optional[str] = Field(None, description="语言")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_encrypted: Optional[bool] = Field(None, description="是否加密")
    status: Optional[DocumentStatus] = Field(None, description="文档状态")


class DocumentResponse(DocumentBase):
    """文档响应schema"""
    id: UUID = Field(..., description="文档ID")
    project_id: UUID = Field(..., description="项目ID")
    status: DocumentStatus = Field(..., description="文档状态")
    processing_status: ProcessingStatus = Field(..., description="处理状态")
    error_message: Optional[str] = Field(None, description="错误消息")
    content_preview: Optional[str] = Field(None, description="内容预览")
    content_length: Optional[int] = Field(None, description="内容长度")
    language: Optional[str] = Field(None, description="语言")
    is_processed: bool = Field(..., description="是否已处理")
    is_indexed: bool = Field(..., description="是否已索引")
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    indexed_at: Optional[datetime] = Field(None, description="索引时间")
    view_count: int = Field(..., description="查看次数")
    download_count: int = Field(..., description="下载次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    project: Optional['ProjectResponse'] = Field(None, description="项目信息")


# 文档内容schemas
class DocumentContentBase(BaseSchema):
    """文档内容基础schema"""
    content: str = Field(..., description="文档内容")
    raw_content: Optional[str] = Field(None, description="原始内容")
    cleaned_content: Optional[str] = Field(None, description="清理后的内容")
    structured_content: Optional[Dict[str, Any]] = Field(None, description="结构化内容")
    summary: Optional[str] = Field(None, description="内容摘要")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    topics: Optional[List[str]] = Field(None, description="主题")
    entities: Optional[Dict[str, Any]] = Field(None, description="实体")
    sentiment: Optional[Dict[str, Any]] = Field(None, description="情感分析")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="质量评分")
    readability_score: Optional[int] = Field(None, ge=0, le=100, description="可读性评分")
    relevance_score: Optional[int] = Field(None, ge=0, le=100, description="相关性评分")
    word_count: Optional[int] = Field(None, ge=0, description="单词数量")
    sentence_count: Optional[int] = Field(None, ge=0, description="句子数量")
    paragraph_count: Optional[int] = Field(None, ge=0, description="段落数量")
    character_count: Optional[int] = Field(None, ge=0, description="字符数量")


class DocumentContentCreate(DocumentContentBase):
    """文档内容创建schema"""
    document_id: UUID = Field(..., description="文档ID")


class DocumentContentUpdate(BaseSchema):
    """文档内容更新schema"""
    content: Optional[str] = Field(None, description="文档内容")
    raw_content: Optional[str] = Field(None, description="原始内容")
    cleaned_content: Optional[str] = Field(None, description="清理后的内容")
    structured_content: Optional[Dict[str, Any]] = Field(None, description="结构化内容")
    summary: Optional[str] = Field(None, description="内容摘要")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    topics: Optional[List[str]] = Field(None, description="主题")
    entities: Optional[Dict[str, Any]] = Field(None, description="实体")
    sentiment: Optional[Dict[str, Any]] = Field(None, description="情感分析")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="质量评分")
    readability_score: Optional[int] = Field(None, ge=0, le=100, description="可读性评分")
    relevance_score: Optional[int] = Field(None, ge=0, le=100, description="相关性评分")
    word_count: Optional[int] = Field(None, ge=0, description="单词数量")
    sentence_count: Optional[int] = Field(None, ge=0, description="句子数量")
    paragraph_count: Optional[int] = Field(None, ge=0, description="段落数量")
    character_count: Optional[int] = Field(None, ge=0, description="字符数量")


class DocumentContentResponse(DocumentContentBase):
    """文档内容响应schema"""
    id: UUID = Field(..., description="内容ID")
    document_id: UUID = Field(..., description="文档ID")
    processed_at: datetime = Field(..., description="处理时间")
    processing_version: int = Field(..., description="处理版本")


# 文档元数据schemas
class DocumentMetadataBase(BaseSchema):
    """文档元数据基础schema"""
    meta_data: Dict[str, Any] = Field(..., description="完整元数据")
    file_metadata: Optional[Dict[str, Any]] = Field(None, description="文件元数据")
    document_metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")
    
    # PDF元数据
    pdf_title: Optional[str] = Field(None, description="PDF标题")
    pdf_author: Optional[str] = Field(None, description="PDF作者")
    pdf_subject: Optional[str] = Field(None, description="PDF主题")
    pdf_keywords: Optional[str] = Field(None, description="PDF关键词")
    pdf_creator: Optional[str] = Field(None, description="PDF创建者")
    pdf_producer: Optional[str] = Field(None, description="PDF生产者")
    pdf_creation_date: Optional[datetime] = Field(None, description="PDF创建时间")
    pdf_modification_date: Optional[datetime] = Field(None, description="PDF修改时间")
    pdf_page_count: Optional[int] = Field(None, ge=0, description="PDF页数")
    
    # Word文档元数据
    word_title: Optional[str] = Field(None, description="Word标题")
    word_author: Optional[str] = Field(None, description="Word作者")
    word_subject: Optional[str] = Field(None, description="Word主题")
    word_keywords: Optional[str] = Field(None, description="Word关键词")
    word_creation_date: Optional[datetime] = Field(None, description="Word创建时间")
    word_modification_date: Optional[datetime] = Field(None, description="Word修改时间")
    word_page_count: Optional[int] = Field(None, ge=0, description="Word页数")
    word_word_count: Optional[int] = Field(None, ge=0, description="Word字数")
    
    # HTML元数据
    html_title: Optional[str] = Field(None, description="HTML标题")
    html_description: Optional[str] = Field(None, description="HTML描述")
    html_keywords: Optional[str] = Field(None, description="HTML关键词")
    html_author: Optional[str] = Field(None, description="HTML作者")
    html_canonical_url: Optional[str] = Field(None, description="HTML规范URL")
    html_og_title: Optional[str] = Field(None, description="HTML Open Graph标题")
    html_og_description: Optional[str] = Field(None, description="HTML Open Graph描述")
    html_og_image: Optional[str] = Field(None, description="HTML Open Graph图片")
    
    # 爬取元数据
    crawl_source: Optional[str] = Field(None, description="爬取来源")
    crawl_url: Optional[str] = Field(None, description="爬取URL")
    crawl_date: Optional[datetime] = Field(None, description="爬取时间")
    crawl_depth: Optional[int] = Field(None, ge=0, description="爬取深度")
    crawl_status: Optional[str] = Field(None, description="爬取状态")
    crawl_user_agent: Optional[str] = Field(None, description="爬取用户代理")
    crawl_ip_address: Optional[str] = Field(None, description="爬取IP地址")


class DocumentMetadataCreate(DocumentMetadataBase):
    """文档元数据创建schema"""
    document_id: UUID = Field(..., description="文档ID")


class DocumentMetadataUpdate(BaseSchema):
    """文档元数据更新schema"""
    meta_data: Optional[Dict[str, Any]] = Field(None, description="完整元数据")
    file_metadata: Optional[Dict[str, Any]] = Field(None, description="文件元数据")
    document_metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")
    pdf_title: Optional[str] = Field(None, description="PDF标题")
    pdf_author: Optional[str] = Field(None, description="PDF作者")
    pdf_subject: Optional[str] = Field(None, description="PDF主题")
    pdf_keywords: Optional[str] = Field(None, description="PDF关键词")
    pdf_creator: Optional[str] = Field(None, description="PDF创建者")
    pdf_producer: Optional[str] = Field(None, description="PDF生产者")
    pdf_creation_date: Optional[datetime] = Field(None, description="PDF创建时间")
    pdf_modification_date: Optional[datetime] = Field(None, description="PDF修改时间")
    pdf_page_count: Optional[int] = Field(None, ge=0, description="PDF页数")
    word_title: Optional[str] = Field(None, description="Word标题")
    word_author: Optional[str] = Field(None, description="Word作者")
    word_subject: Optional[str] = Field(None, description="Word主题")
    word_keywords: Optional[str] = Field(None, description="Word关键词")
    word_creation_date: Optional[datetime] = Field(None, description="Word创建时间")
    word_modification_date: Optional[datetime] = Field(None, description="Word修改时间")
    word_page_count: Optional[int] = Field(None, ge=0, description="Word页数")
    word_word_count: Optional[int] = Field(None, ge=0, description="Word字数")
    html_title: Optional[str] = Field(None, description="HTML标题")
    html_description: Optional[str] = Field(None, description="HTML描述")
    html_keywords: Optional[str] = Field(None, description="HTML关键词")
    html_author: Optional[str] = Field(None, description="HTML作者")
    html_canonical_url: Optional[str] = Field(None, description="HTML规范URL")
    html_og_title: Optional[str] = Field(None, description="HTML Open Graph标题")
    html_og_description: Optional[str] = Field(None, description="HTML Open Graph描述")
    html_og_image: Optional[str] = Field(None, description="HTML Open Graph图片")
    crawl_source: Optional[str] = Field(None, description="爬取来源")
    crawl_url: Optional[str] = Field(None, description="爬取URL")
    crawl_date: Optional[datetime] = Field(None, description="爬取时间")
    crawl_depth: Optional[int] = Field(None, ge=0, description="爬取深度")
    crawl_status: Optional[str] = Field(None, description="爬取状态")
    crawl_user_agent: Optional[str] = Field(None, description="爬取用户代理")
    crawl_ip_address: Optional[str] = Field(None, description="爬取IP地址")


class DocumentMetadataResponse(DocumentMetadataBase):
    """文档元数据响应schema"""
    id: UUID = Field(..., description="元数据ID")
    document_id: UUID = Field(..., description="文档ID")
    extracted_at: datetime = Field(..., description="提取时间")
    extraction_version: int = Field(..., description="提取版本")


# 更新前向引用
from .project import ProjectResponse
DocumentResponse.model_rebuild()