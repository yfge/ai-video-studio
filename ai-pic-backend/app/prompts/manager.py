"""
提示词管理器

负责加载、管理和渲染各种AI任务的提示词模板
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """提示词管理器"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化提示词管理器
        
        Args:
            prompts_dir: 提示词文件目录，默认为当前目录下的templates文件夹
        """
        if prompts_dir is None:
            prompts_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 缓存已加载的提示词模板
        self._template_cache: Dict[str, Template] = {}
        self._metadata_cache: Dict[str, Dict] = {}
    
    def load_template(self, template_name: str) -> Template:
        """
        加载提示词模板
        
        Args:
            template_name: 模板名称（不含扩展名）
            
        Returns:
            Jinja2模板对象
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        try:
            template_file = f"{template_name}.txt"
            template = self.jinja_env.get_template(template_file)
            self._template_cache[template_name] = template
            return template
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            raise ValueError(f"Template {template_name} not found or invalid")
    
    def load_metadata(self, template_name: str) -> Dict[str, Any]:
        """
        加载模板元数据
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板元数据字典
        """
        if template_name in self._metadata_cache:
            return self._metadata_cache[template_name]
        
        metadata_file = self.prompts_dir / f"{template_name}.yaml"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = yaml.safe_load(f) or {}
                    self._metadata_cache[template_name] = metadata
                    return metadata
            except Exception as e:
                logger.warning(f"Failed to load metadata for {template_name}: {e}")
        
        return {}
    
    def render_prompt(self, template_name: str, variables: Dict[str, Any]) -> str:
        """
        渲染提示词
        
        Args:
            template_name: 模板名称
            variables: 模板变量
            
        Returns:
            渲染后的提示词文本
        """
        try:
            template = self.load_template(template_name)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise ValueError(f"Failed to render template {template_name}: {str(e)}")
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            包含模板元数据和变量信息的字典
        """
        metadata = self.load_metadata(template_name)
        
        # 分析模板中的变量
        try:
            template = self.load_template(template_name)
            variables = list(template.environment.parse(template.source).find_all(
                lambda node: hasattr(node, 'name')
            ))
            variable_names = list(set([var.name for var in variables if hasattr(var, 'name')]))
        except:
            variable_names = []
        
        return {
            'name': template_name,
            'metadata': metadata,
            'variables': variable_names,
            'description': metadata.get('description', ''),
            'category': metadata.get('category', 'general'),
            'version': metadata.get('version', '1.0'),
            'author': metadata.get('author', ''),
            'created_at': metadata.get('created_at', ''),
            'updated_at': metadata.get('updated_at', '')
        }
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有可用的模板
        
        Args:
            category: 可选的类别过滤
            
        Returns:
            模板信息列表
        """
        templates = []
        
        for template_file in self.prompts_dir.glob("*.txt"):
            template_name = template_file.stem
            try:
                info = self.get_template_info(template_name)
                if category is None or info.get('category') == category:
                    templates.append(info)
            except Exception as e:
                logger.warning(f"Failed to get info for template {template_name}: {e}")
        
        return sorted(templates, key=lambda x: x['name'])
    
    def get_categories(self) -> List[str]:
        """
        获取所有模板类别
        
        Returns:
            类别名称列表
        """
        categories = set()
        for template in self.list_templates():
            categories.add(template.get('category', 'general'))
        return sorted(list(categories))
    
    def validate_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证模板变量
        
        Args:
            template_name: 模板名称
            variables: 要验证的变量
            
        Returns:
            验证结果
        """
        info = self.get_template_info(template_name)
        required_vars = info['variables']
        metadata = info['metadata']
        
        result = {
            'valid': True,
            'missing_vars': [],
            'extra_vars': [],
            'type_errors': [],
            'validation_errors': []
        }
        
        # 检查必需变量
        required_vars_config = metadata.get('variables', {})
        for var_name in required_vars:
            if var_name not in variables:
                var_config = required_vars_config.get(var_name, {})
                if var_config.get('required', True):
                    result['missing_vars'].append(var_name)
                    result['valid'] = False
        
        # 检查额外变量
        for var_name in variables:
            if var_name not in required_vars:
                result['extra_vars'].append(var_name)
        
        # 检查变量类型和值
        for var_name, var_value in variables.items():
            var_config = required_vars_config.get(var_name, {})
            
            # 类型检查
            expected_type = var_config.get('type')
            if expected_type:
                if expected_type == 'string' and not isinstance(var_value, str):
                    result['type_errors'].append(f"{var_name} should be string")
                    result['valid'] = False
                elif expected_type == 'number' and not isinstance(var_value, (int, float)):
                    result['type_errors'].append(f"{var_name} should be number")
                    result['valid'] = False
                elif expected_type == 'list' and not isinstance(var_value, list):
                    result['type_errors'].append(f"{var_name} should be list")
                    result['valid'] = False
                elif expected_type == 'dict' and not isinstance(var_value, dict):
                    result['type_errors'].append(f"{var_name} should be dict")
                    result['valid'] = False
            
            # 值范围检查
            if 'min_length' in var_config and isinstance(var_value, str):
                if len(var_value) < var_config['min_length']:
                    result['validation_errors'].append(f"{var_name} too short")
                    result['valid'] = False
            
            if 'max_length' in var_config and isinstance(var_value, str):
                if len(var_value) > var_config['max_length']:
                    result['validation_errors'].append(f"{var_name} too long")
                    result['valid'] = False
        
        return result
    
    def create_template(self, template_name: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        创建新的模板文件
        
        Args:
            template_name: 模板名称
            content: 模板内容
            metadata: 模板元数据
            
        Returns:
            是否创建成功
        """
        try:
            # 写入模板文件
            template_file = self.prompts_dir / f"{template_name}.txt"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 写入元数据文件
            metadata_file = self.prompts_dir / f"{template_name}.yaml"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
            
            # 清理缓存
            if template_name in self._template_cache:
                del self._template_cache[template_name]
            if template_name in self._metadata_cache:
                del self._metadata_cache[template_name]
            
            return True
        except Exception as e:
            logger.error(f"Failed to create template {template_name}: {e}")
            return False

# 全局提示词管理器实例
prompt_manager = PromptManager()