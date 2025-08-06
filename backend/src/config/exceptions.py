"""
配置系统异常类
"""


class ConfigError(Exception):
    """配置系统基础异常"""
    pass


class ConfigNotFoundError(ConfigError):
    """配置文件未找到异常"""
    pass


class ConfigValidationError(ConfigError):
    """配置验证失败异常"""
    pass


class ConfigLoadError(ConfigError):
    """配置加载失败异常"""
    pass


class ConfigParseError(ConfigError):
    """配置解析失败异常"""
    pass


class ConfigMergeError(ConfigError):
    """配置合并失败异常"""
    pass


class ConfigAccessError(ConfigError):
    """配置访问失败异常"""
    pass