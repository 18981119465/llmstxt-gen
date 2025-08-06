"""
Example service demonstrating how to use the configuration system.
This service shows how to integrate configuration management into a real application.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.config.core import ConfigManager, ConfigWatcher
from src.config.management import get_config_manager
from src.config.rollback import ConfigRollbackManager
from src.config.schemas import AppConfig, DatabaseConfig, LoggingConfig

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    Example service that processes documents and uses configuration system.
    Demonstrates how to integrate configuration management into a real service.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or get_config_manager()
        self.rollback_manager = ConfigRollbackManager()
        self.config_watcher = None
        self.is_running = False
        self._config_cache = {}
        
    async def initialize(self) -> None:
        """Initialize the service with configuration"""
        try:
            # Load initial configuration
            await self._load_config()
            
            # Set up configuration watcher for hot reload
            self.config_watcher = ConfigWatcher(
                config_path=self.config_manager.config_path,
                on_change=self._on_config_changed
            )
            
            # Start watching for configuration changes
            await self.config_watcher.start_watching()
            
            logger.info("DocumentProcessingService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DocumentProcessingService: {e}")
            raise
    
    async def _load_config(self) -> None:
        """Load configuration from config manager"""
        try:
            config = self.config_manager.load_config()
            
            # Cache configuration sections
            self._config_cache = {
                'service': config.get('service', {}),
                'database': config.get('database', {}),
                'logging': config.get('logging', {}),
                'processing': config.get('processing', {})
            }
            
            # Validate configuration using Pydantic models
            service_config = AppConfig(**self._config_cache.get('service', {}))
            db_config = DatabaseConfig(**self._config_cache.get('database', {}))
            logging_config = LoggingConfig(**self._config_cache.get('logging', {}))
            
            logger.info("Configuration loaded and validated successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    async def _on_config_changed(self, event_type: str, file_path: str) -> None:
        """Handle configuration changes"""
        try:
            logger.info(f"Configuration changed: {event_type} - {file_path}")
            
            # Create backup before reloading
            await self.rollback_manager.create_version(
                description=f"Auto-backup before config change: {event_type}"
            )
            
            # Reload configuration
            await self._load_config()
            
            # Apply new configuration to service
            await self._apply_config_changes()
            
        except Exception as e:
            logger.error(f"Failed to handle configuration change: {e}")
            # Rollback to previous version if available
            await self._rollback_config()
    
    async def _apply_config_changes(self) -> None:
        """Apply configuration changes to the service"""
        try:
            # Update logging configuration
            log_config = self._config_cache.get('logging', {})
            if log_config.get('level'):
                logging.getLogger().setLevel(log_config['level'])
            
            # Update service parameters
            service_config = self._config_cache.get('service', {})
            if service_config.get('max_workers'):
                # Update worker pool size
                logger.info(f"Updating max_workers to {service_config['max_workers']}")
            
            logger.info("Configuration changes applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply configuration changes: {e}")
            raise
    
    async def _rollback_config(self) -> None:
        """Rollback configuration to previous version"""
        try:
            versions = await self.rollback_manager.list_versions()
            if len(versions) > 1:
                # Rollback to the previous version
                previous_version = versions[-2]  # Second to last version
                await self.rollback_manager.rollback_to_version(previous_version['version_id'])
                logger.info(f"Configuration rolled back to version {previous_version['version_id']}")
            else:
                logger.warning("No previous version available for rollback")
                
        except Exception as e:
            logger.error(f"Failed to rollback configuration: {e}")
    
    async def process_document(self, document_id: int, content: str) -> Dict[str, Any]:
        """
        Process a document using current configuration.
        Demonstrates how to use configuration in business logic.
        """
        try:
            # Get processing configuration
            processing_config = self._config_cache.get('processing', {})
            
            # Apply configuration-based processing
            max_length = processing_config.get('max_document_length', 10000)
            enable_analysis = processing_config.get('enable_analysis', True)
            analysis_timeout = processing_config.get('analysis_timeout', 30)
            
            # Process document with configuration
            if len(content) > max_length:
                content = content[:max_length]
                logger.warning(f"Document truncated to {max_length} characters")
            
            result = {
                'document_id': document_id,
                'processed_at': datetime.utcnow().isoformat(),
                'original_length': len(content),
                'processing_config': {
                    'max_length': max_length,
                    'analysis_enabled': enable_analysis,
                    'timeout': analysis_timeout
                }
            }
            
            if enable_analysis:
                # Simulate document analysis
                result['analysis'] = {
                    'word_count': len(content.split()),
                    'character_count': len(content),
                    'estimated_reading_time': len(content.split()) / 200  # 200 words per minute
                }
            
            logger.info(f"Document {document_id} processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            raise
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status including configuration information"""
        try:
            return {
                'service_name': 'DocumentProcessingService',
                'status': 'running' if self.is_running else 'stopped',
                'config_path': self.config_manager.config_path,
                'config_last_updated': self.config_manager.get_config_info().get('last_modified'),
                'watcher_active': self.config_watcher.is_running if self.config_watcher else False,
                'cached_config_sections': list(self._config_cache.keys()),
                'available_versions': len(await self.rollback_manager.list_versions())
            }
            
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            raise
    
    async def start(self) -> None:
        """Start the service"""
        try:
            await self.initialize()
            self.is_running = True
            logger.info("DocumentProcessingService started")
            
        except Exception as e:
            logger.error(f"Failed to start DocumentProcessingService: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the service"""
        try:
            self.is_running = False
            
            if self.config_watcher:
                await self.config_watcher.stop_watching()
            
            logger.info("DocumentProcessingService stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop DocumentProcessingService: {e}")
            raise
    
    async def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update service configuration.
        Demonstrates how to use the configuration management API.
        """
        try:
            # Create backup before making changes
            backup_version = await self.rollback_manager.create_version(
                description=f"Manual config update: {list(config_updates.keys())}"
            )
            
            # Update configuration
            current_config = self.config_manager.load_config()
            
            # Deep merge configuration updates
            def deep_merge(base: Dict, update: Dict) -> Dict:
                result = base.copy()
                for key, value in update.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result
            
            updated_config = deep_merge(current_config, config_updates)
            
            # Save updated configuration
            self.config_manager.save_config(updated_config)
            
            # Configuration will be automatically reloaded via the watcher
            
            return {
                'success': True,
                'backup_version': backup_version,
                'updated_sections': list(config_updates.keys()),
                'config_path': self.config_manager.config_path
            }
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise


# Example usage function
async def example_usage():
    """Example of how to use the DocumentProcessingService"""
    # Create service instance
    service = DocumentProcessingService()
    
    try:
        # Start the service
        await service.start()
        
        # Get service status
        status = await service.get_service_status()
        print(f"Service status: {status}")
        
        # Process a document
        result = await service.process_document(
            document_id=1,
            content="This is a sample document content for processing."
        )
        print(f"Processing result: {result}")
        
        # Update configuration
        config_update = {
            'processing': {
                'max_document_length': 5000,
                'enable_analysis': True,
                'analysis_timeout': 60
            }
        }
        
        update_result = await service.update_config(config_update)
        print(f"Configuration update result: {update_result}")
        
        # Process another document with new configuration
        result2 = await service.process_document(
            document_id=2,
            content="This is another document that will be processed with the updated configuration."
        )
        print(f"Second processing result: {result2}")
        
    finally:
        # Stop the service
        await service.stop()


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())