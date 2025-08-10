"""
API工具模块 - 验证工具
"""

from typing import Any, Dict, List, Optional, Union, get_type_hints
from pydantic import BaseModel, ValidationError, validator
from datetime import datetime, date
import re
import logging

logger = logging.getLogger(__name__)


class ValidationHelper:
    """验证助手类"""
    
    # 常用验证正则表达式
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    URL_PATTERN = re.compile(
        r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    )
    
    PHONE_PATTERN = re.compile(
        r'^(\+?86)?1[3-9]\d{9}$'
    )
    
    ZIP_CODE_PATTERN = re.compile(
        r'^\d{6}$'
    )
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """验证必填字段"""
        errors = {}
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors[field] = f"{field}是必填字段"
        
        return errors
    
    @staticmethod
    def validate_data_types(data: Dict[str, Any], type_hints: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据类型"""
        errors = {}
        
        for field, expected_type in type_hints.items():
            if field in data and data[field] is not None:
                try:
                    # 处理Optional类型
                    if hasattr(expected_type, '__origin__'):
                        origin_type = expected_type.__origin__
                        if origin_type is Union:
                            # 检查Union中的任何类型
                            type_args = expected_type.__args__
                            if not any(isinstance(data[field], arg) for arg in type_args):
                                errors[field] = f"{field}类型错误，期望 {expected_type}"
                    else:
                        if not isinstance(data[field], expected_type):
                            errors[field] = f"{field}类型错误，期望 {expected_type.__name__}"
                except Exception as e:
                    errors[field] = f"{field}类型验证失败: {str(e)}"
        
        return errors
    
    @staticmethod
    def validate_string_length(
        data: Dict[str, Any], 
        field_rules: Dict[str, Dict[str, int]]
    ) -> Dict[str, Any]:
        """验证字符串长度"""
        errors = {}
        
        for field, rules in field_rules.items():
            if field in data and isinstance(data[field], str):
                value = data[field]
                
                if 'min_length' in rules and len(value) < rules['min_length']:
                    errors[field] = f"{field}长度不能少于{rules['min_length']}个字符"
                
                if 'max_length' in rules and len(value) > rules['max_length']:
                    errors[field] = f"{field}长度不能超过{rules['max_length']}个字符"
        
        return errors
    
    @staticmethod
    def validate_numeric_range(
        data: Dict[str, Any], 
        field_rules: Dict[str, Dict[str, Union[int, float]]]
    ) -> Dict[str, Any]:
        """验证数值范围"""
        errors = {}
        
        for field, rules in field_rules.items():
            if field in data and isinstance(data[field], (int, float)):
                value = data[field]
                
                if 'min_value' in rules and value < rules['min_value']:
                    errors[field] = f"{field}不能小于{rules['min_value']}"
                
                if 'max_value' in rules and value > rules['max_value']:
                    errors[field] = f"{field}不能大于{rules['max_value']}"
        
        return errors
    
    @staticmethod
    def validate_enum_values(
        data: Dict[str, Any], 
        field_rules: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """验证枚举值"""
        errors = {}
        
        for field, allowed_values in field_rules.items():
            if field in data and data[field] not in allowed_values:
                errors[field] = f"{field}必须是以下值之一: {allowed_values}"
        
        return errors
    
    @staticmethod
    def validate_patterns(
        data: Dict[str, Any], 
        field_rules: Dict[str, re.Pattern]
    ) -> Dict[str, Any]:
        """验证正则表达式"""
        errors = {}
        
        for field, pattern in field_rules.items():
            if field in data and isinstance(data[field], str):
                if not pattern.match(data[field]):
                    errors[field] = f"{field}格式不正确"
        
        return errors
    
    @staticmethod
    def validate_custom_rules(
        data: Dict[str, Any], 
        field_rules: Dict[str, callable]
    ) -> Dict[str, Any]:
        """验证自定义规则"""
        errors = {}
        
        for field, validator_func in field_rules.items():
            if field in data:
                try:
                    result = validator_func(data[field])
                    if result is not True:
                        errors[field] = result if isinstance(result, str) else f"{field}验证失败"
                except Exception as e:
                    errors[field] = f"{field}验证失败: {str(e)}"
        
        return errors
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """验证UUID格式"""
        return bool(ValidationHelper.UUID_PATTERN.match(uuid_string))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式"""
        return bool(ValidationHelper.URL_PATTERN.match(url))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        return bool(ValidationHelper.PHONE_PATTERN.match(phone))
    
    @staticmethod
    def validate_zip_code(zip_code: str) -> bool:
        """验证邮编格式"""
        return bool(ValidationHelper.ZIP_CODE_PATTERN.match(zip_code))
    
    @staticmethod
    def validate_date_format(date_string: str, format_string: str = "%Y-%m-%d") -> bool:
        """验证日期格式"""
        try:
            datetime.strptime(date_string, format_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_future_date(date_string: str, format_string: str = "%Y-%m-%d") -> bool:
        """验证未来日期"""
        try:
            input_date = datetime.strptime(date_string, format_string).date()
            today = date.today()
            return input_date > today
        except ValueError:
            return False
    
    @staticmethod
    def validate_past_date(date_string: str, format_string: str = "%Y-%m-%d") -> bool:
        """验证过去日期"""
        try:
            input_date = datetime.strptime(date_string, format_string).date()
            today = date.today()
            return input_date < today
        except ValueError:
            return False
    
    @staticmethod
    def validate_email_domain(email: str, allowed_domains: List[str]) -> bool:
        """验证邮箱域名"""
        if '@' not in email:
            return False
        
        domain = email.split('@')[1]
        return domain in allowed_domains
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """验证文件大小"""
        return file_size <= max_size
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """验证文件扩展名"""
        if '.' not in filename:
            return False
        
        extension = filename.split('.')[-1].lower()
        return extension in allowed_extensions
    
    @staticmethod
    def validate_list_items(
        items: List[Any], 
        item_validator: callable,
        max_items: Optional[int] = None
    ) -> Dict[str, Any]:
        """验证列表项"""
        errors = {}
        
        if max_items and len(items) > max_items:
            errors["list"] = f"列表项不能超过{max_items}个"
        
        for i, item in enumerate(items):
            try:
                result = item_validator(item)
                if result is not True:
                    errors[f"item_{i}"] = result if isinstance(result, str) else f"第{i+1}项验证失败"
            except Exception as e:
                errors[f"item_{i}"] = f"第{i+1}项验证失败: {str(e)}"
        
        return errors
    
    @staticmethod
    def validate_dict_keys(
        data: Dict[str, Any], 
        allowed_keys: List[str],
        required_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """验证字典键"""
        errors = {}
        
        # 检查未知键
        for key in data.keys():
            if key not in allowed_keys:
                errors[key] = f"未知的字段: {key}"
        
        # 检查必填键
        if required_keys:
            for key in required_keys:
                if key not in data:
                    errors[key] = f"缺少必填字段: {key}"
        
        return errors
    
    @staticmethod
    def validate_with_pydantic(data: Any, model_class: type[BaseModel]) -> tuple[Any, Dict[str, Any]]:
        """使用Pydantic进行验证"""
        errors = {}
        
        try:
            if isinstance(data, dict):
                validated_data = model_class(**data)
            else:
                validated_data = model_class.model_validate(data)
            
            return validated_data, errors
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors[field] = error["msg"]
            return None, errors
        except Exception as e:
            errors["general"] = f"验证失败: {str(e)}"
            return None, errors
    
    @staticmethod
    def combine_validation_results(*validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """合并多个验证结果"""
        combined_errors = {}
        
        for result in validation_results:
            combined_errors.update(result)
        
        return combined_errors
    
    @staticmethod
    def format_validation_errors(errors: Dict[str, Any]) -> List[Dict[str, str]]:
        """格式化验证错误"""
        formatted_errors = []
        
        for field, message in errors.items():
            formatted_errors.append({
                "field": field,
                "message": message
            })
        
        return formatted_errors


class RequestValidator:
    """请求验证器"""
    
    def __init__(self):
        self.validation_rules = {}
    
    def add_rule(self, field: str, rule_type: str, **kwargs):
        """添加验证规则"""
        if field not in self.validation_rules:
            self.validation_rules[field] = {}
        
        self.validation_rules[field][rule_type] = kwargs
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据"""
        all_errors = {}
        
        for field, rules in self.validation_rules.items():
            field_errors = {}
            
            # 必填字段验证
            if 'required' in rules and rules['required']:
                if field not in data or data[field] is None or data[field] == "":
                    field_errors['required'] = f"{field}是必填字段"
            
            # 跳过空值的后续验证
            if field not in data or data[field] is None:
                if field_errors:
                    all_errors[field] = field_errors
                continue
            
            value = data[field]
            
            # 类型验证
            if 'type' in rules:
                expected_type = rules['type']
                if not isinstance(value, expected_type):
                    field_errors['type'] = f"{field}类型错误，期望 {expected_type.__name__}"
            
            # 长度验证
            if 'min_length' in rules and isinstance(value, str):
                if len(value) < rules['min_length']:
                    field_errors['min_length'] = f"{field}长度不能少于{rules['min_length']}个字符"
            
            if 'max_length' in rules and isinstance(value, str):
                if len(value) > rules['max_length']:
                    field_errors['max_length'] = f"{field}长度不能超过{rules['max_length']}个字符"
            
            # 数值范围验证
            if 'min_value' in rules and isinstance(value, (int, float)):
                if value < rules['min_value']:
                    field_errors['min_value'] = f"{field}不能小于{rules['min_value']}"
            
            if 'max_value' in rules and isinstance(value, (int, float)):
                if value > rules['max_value']:
                    field_errors['max_value'] = f"{field}不能大于{rules['max_value']}"
            
            # 枚举值验证
            if 'choices' in rules:
                if value not in rules['choices']:
                    field_errors['choices'] = f"{field}必须是以下值之一: {rules['choices']}"
            
            # 正则表达式验证
            if 'pattern' in rules and isinstance(value, str):
                if not rules['pattern'].match(value):
                    field_errors['pattern'] = f"{field}格式不正确"
            
            # 自定义验证函数
            if 'validator' in rules:
                try:
                    result = rules['validator'](value)
                    if result is not True:
                        field_errors['custom'] = result if isinstance(result, str) else f"{field}验证失败"
                except Exception as e:
                    field_errors['custom'] = f"{field}验证失败: {str(e)}"
            
            if field_errors:
                all_errors[field] = field_errors
        
        return all_errors