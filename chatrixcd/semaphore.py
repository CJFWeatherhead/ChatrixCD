"""Semaphore UI REST API client."""

import logging
import aiohttp
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class SemaphoreClient:
    """Client for interacting with Semaphore UI REST API."""

    def __init__(self, url: str, api_token: str):
        """Initialize Semaphore client.
        
        Args:
            url: Base URL of Semaphore UI instance
            api_token: API token for authentication
        """
        self.base_url = url.rstrip('/')
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of all projects.
        
        Returns:
            List of project dictionaries
        """
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.base_url}/api/projects") as resp:
                if resp.status == 200:
                    projects = await resp.json()
                    logger.info(f"Retrieved {len(projects)} projects")
                    return projects
                else:
                    logger.error(f"Failed to get projects: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []

    async def get_project_templates(self, project_id: int) -> List[Dict[str, Any]]:
        """Get templates for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of template dictionaries
        """
        await self._ensure_session()
        try:
            async with self.session.get(
                f"{self.base_url}/api/project/{project_id}/templates"
            ) as resp:
                if resp.status == 200:
                    templates = await resp.json()
                    logger.info(f"Retrieved {len(templates)} templates for project {project_id}")
                    return templates
                else:
                    logger.error(f"Failed to get templates: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []

    async def start_task(self, project_id: int, template_id: int, 
                        debug: bool = False, dry_run: bool = False) -> Optional[Dict[str, Any]]:
        """Start a new task from a template.
        
        Args:
            project_id: ID of the project
            template_id: ID of the template to run
            debug: Enable debug mode
            dry_run: Run in dry-run mode
            
        Returns:
            Task dictionary or None if failed
        """
        await self._ensure_session()
        try:
            payload = {
                'template_id': template_id,
                'debug': debug,
                'dry_run': dry_run
            }
            async with self.session.post(
                f"{self.base_url}/api/project/{project_id}/tasks",
                json=payload
            ) as resp:
                if resp.status in (200, 201):
                    task = await resp.json()
                    logger.info(f"Started task {task.get('id')} from template {template_id}")
                    return task
                else:
                    logger.error(f"Failed to start task: {resp.status}")
                    error_text = await resp.text()
                    logger.error(f"Error response: {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error starting task: {e}")
            return None

    async def get_task_status(self, project_id: int, task_id: int) -> Optional[Dict[str, Any]]:
        """Get status of a specific task.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            
        Returns:
            Task dictionary with status or None if failed
        """
        await self._ensure_session()
        try:
            async with self.session.get(
                f"{self.base_url}/api/project/{project_id}/tasks/{task_id}"
            ) as resp:
                if resp.status == 200:
                    task = await resp.json()
                    return task
                else:
                    logger.error(f"Failed to get task status: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return None

    async def get_task_output(self, project_id: int, task_id: int) -> Optional[str]:
        """Get output logs for a specific task.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            
        Returns:
            Task output as string or None if failed
        """
        await self._ensure_session()
        try:
            async with self.session.get(
                f"{self.base_url}/api/project/{project_id}/tasks/{task_id}/output"
            ) as resp:
                if resp.status == 200:
                    output = await resp.text()
                    return output
                else:
                    logger.error(f"Failed to get task output: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting task output: {e}")
            return None

    async def stop_task(self, project_id: int, task_id: int) -> bool:
        """Stop a running task.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            
        Returns:
            True if task was stopped successfully, False otherwise
        """
        await self._ensure_session()
        try:
            async with self.session.post(
                f"{self.base_url}/api/project/{project_id}/tasks/{task_id}/stop"
            ) as resp:
                if resp.status in (200, 204):
                    logger.info(f"Stopped task {task_id}")
                    return True
                else:
                    logger.error(f"Failed to stop task: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Error stopping task: {e}")
            return False
