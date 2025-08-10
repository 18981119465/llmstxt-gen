"""
API工具模块 - 分页工具
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from pydantic import BaseModel
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """分页参数模型"""
    
    page: int = 1
    page_size: int = 10
    max_page_size: int = 100
    
    def __init__(self, **data):
        super().__init__(**data)
        # 验证并修正分页参数
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 10
        if self.page_size > self.max_page_size:
            self.page_size = self.max_page_size


class PaginationResult(BaseModel, Generic[T]):
    """分页结果模型"""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginationResult[T]":
        """创建分页结果"""
        total_pages = ceil(total / page_size)
        has_next = page < total_pages
        has_prev = page > 1
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )


class PaginationHelper:
    """分页助手类"""
    
    @staticmethod
    def create_pagination_params(
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 100
    ) -> PaginationParams:
        """创建分页参数"""
        return PaginationParams(
            page=page,
            page_size=page_size,
            max_page_size=max_page_size
        )
    
    @staticmethod
    def calculate_offset(page: int, page_size: int) -> int:
        """计算偏移量"""
        return (page - 1) * page_size
    
    @staticmethod
    def calculate_total_pages(total: int, page_size: int) -> int:
        """计算总页数"""
        return ceil(total / page_size)
    
    @staticmethod
    def get_page_info(
        total: int,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """获取分页信息"""
        total_pages = PaginationHelper.calculate_total_pages(total, page_size)
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
    
    @staticmethod
    def paginate_list(
        items: List[T],
        page: int,
        page_size: int
    ) -> PaginationResult[T]:
        """对列表进行分页"""
        total = len(items)
        offset = PaginationHelper.calculate_offset(page, page_size)
        end = offset + page_size
        
        paginated_items = items[offset:end]
        
        return PaginationResult.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    @staticmethod
    def create_page_links(
        base_url: str,
        total: int,
        page: int,
        page_size: int,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """创建分页链接"""
        from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
        
        if query_params is None:
            query_params = {}
        
        total_pages = PaginationHelper.calculate_total_pages(total, page_size)
        
        def build_url(page_num: int) -> str:
            params = query_params.copy()
            params.update({"page": page_num, "page_size": page_size})
            
            # 解析基础URL
            parsed = urlparse(base_url)
            
            # 合并查询参数
            existing_params = parse_qs(parsed.query)
            for key, value in params.items():
                existing_params[key] = [str(value)]
            
            # 构建新的查询字符串
            query_string = urlencode(existing_params, doseq=True)
            
            # 构建完整URL
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                query_string,
                parsed.fragment
            ))
        
        links = {}
        
        # 首页
        if page > 1:
            links["first"] = build_url(1)
        
        # 上一页
        if page > 1:
            links["prev"] = build_url(page - 1)
        
        # 下一页
        if page < total_pages:
            links["next"] = build_url(page + 1)
        
        # 末页
        if page < total_pages:
            links["last"] = build_url(total_pages)
        
        return links


class CursorPaginationHelper:
    """游标分页助手类"""
    
    @staticmethod
    def create_cursor(
        item: Dict[str, Any],
        cursor_field: str = "id"
    ) -> str:
        """创建游标"""
        import base64
        import json
        
        cursor_data = {
            "cursor": str(item[cursor_field]),
            "field": cursor_field
        }
        
        cursor_json = json.dumps(cursor_data)
        cursor_bytes = cursor_json.encode('utf-8')
        cursor_b64 = base64.b64encode(cursor_bytes)
        
        return cursor_b64.decode('utf-8')
    
    @staticmethod
    def decode_cursor(cursor: str) -> Dict[str, Any]:
        """解码游标"""
        import base64
        import json
        
        try:
            cursor_bytes = cursor.encode('utf-8')
            cursor_b64 = base64.b64decode(cursor_bytes)
            cursor_json = cursor_b64.decode('utf-8')
            cursor_data = json.loads(cursor_json)
            
            return cursor_data
        except Exception:
            return {"cursor": None, "field": "id"}
    
    @staticmethod
    def has_next_page(items: List[T], limit: int) -> bool:
        """检查是否有下一页"""
        return len(items) > limit
    
    @staticmethod
    def get_next_cursor(
        items: List[T],
        limit: int,
        cursor_field: str = "id"
    ) -> Optional[str]:
        """获取下一页游标"""
        if not CursorPaginationHelper.has_next_page(items, limit):
            return None
        
        # 获取最后一项
        last_item = items[-2] if len(items) > limit else items[-1]
        
        if hasattr(last_item, '__dict__'):
            return CursorPaginationHelper.create_cursor(last_item.__dict__, cursor_field)
        elif isinstance(last_item, dict):
            return CursorPaginationHelper.create_cursor(last_item, cursor_field)
        else:
            return None


# 常用分页配置
DEFAULT_PAGINATION = {
    "page": 1,
    "page_size": 10,
    "max_page_size": 100
}

API_PAGINATION = {
    "page": 1,
    "page_size": 20,
    "max_page_size": 100
}

ADMIN_PAGINATION = {
    "page": 1,
    "page_size": 50,
    "max_page_size": 200
}

LOG_PAGINATION = {
    "page": 1,
    "page_size": 100,
    "max_page_size": 500
}