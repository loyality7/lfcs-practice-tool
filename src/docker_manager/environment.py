import docker
import tarfile
import io
import os
from typing import Dict, Any, Optional
import logging

from ..core.interfaces import Environment, ExecutionResult

logger = logging.getLogger(__name__)

class DockerEnvironment(Environment):
    """
    Docker implementation of the Environment interface.
    Wraps a Docker container to provide a standard execution interface.
    """
    
    def __init__(self, container: docker.models.containers.Container):
        self.container = container

    def execute_command(self, command: str, user: Optional[str] = None) -> ExecutionResult:
        """Execute a command in the container"""
        try:
            # Refresh container state
            self.container.reload()
            
            if self.container.status != 'running':
                return ExecutionResult(
                    exit_code=-1,
                    output="",
                    error=f"Container is not running (status: {self.container.status})"
                )
            
            # Prepare exec options
            # Wrap command in bash to support builtins (cd, source), pipes, and redirection
            escaped_command = command.replace('"', '\\"')
            wrapped_command = f'/bin/bash -c "{escaped_command}"'
            
            exec_kwargs = {
                "cmd": wrapped_command,
                "demux": True,
                "tty": False
            }
            
            if user:
                exec_kwargs["user"] = user
                
            # Execute
            exec_result = self.container.exec_run(**exec_kwargs)
            
            # Process output
            stdout, stderr = exec_result.output
            output = stdout.decode('utf-8', errors='replace') if stdout else ""
            error = stderr.decode('utf-8', errors='replace') if stderr else None
            
            return ExecutionResult(
                exit_code=exec_result.exit_code,
                output=output,
                error=error
            )
            
        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            return ExecutionResult(
                exit_code=-1,
                output="",
                error=str(e)
            )

    def read_file(self, path: str) -> str:
        """Read file content from the container"""
        try:
            # Get archive of file
            bits, stat = self.container.get_archive(path)
            
            # Read from tar stream
            file_obj = io.BytesIO()
            for chunk in bits:
                file_obj.write(chunk)
            file_obj.seek(0)
            
            with tarfile.open(fileobj=file_obj, mode='r') as tar:
                # The tar contains the file with its basename
                member = tar.next()
                if not member:
                    raise FileNotFoundError(f"File not found in archive: {path}")
                
                f = tar.extractfile(member)
                if not f:
                    raise FileNotFoundError(f"Could not extract file: {path}")
                    
                return f.read().decode('utf-8', errors='replace')
                
        except docker.errors.NotFound:
            raise FileNotFoundError(f"File not found: {path}")
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise

    def file_exists(self, path: str) -> bool:
        """Check if a file exists"""
        try:
            self.container.get_archive(path)
            return True
        except docker.errors.NotFound:
            return False
        except Exception:
            return False

    def get_file_stats(self, path: str) -> Dict[str, Any]:
        """Get file statistics"""
        # We'll use stat command inside container as it's easier than parsing tar headers for everything
        cmd = f"stat -c '%a|%U|%G|%s' {path}"
        result = self.execute_command(cmd)
        
        if result.exit_code != 0:
            raise FileNotFoundError(f"File not found or stat failed: {path}")
            
        try:
            perms, owner, group, size = result.output.strip().split('|')
            return {
                "permissions": perms,
                "owner": owner,
                "group": group,
                "size": int(size)
            }
        except ValueError:
            raise ValueError(f"Failed to parse stat output: {result.output}")
