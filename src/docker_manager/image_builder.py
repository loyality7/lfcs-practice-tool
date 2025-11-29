"""
Docker Image Builder Module
Handles automatic building of Docker images with progress display
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
import docker
from docker.errors import BuildError, APIError

logger = logging.getLogger(__name__)


class DockerImageBuilder:
    """Builds Docker images automatically with progress tracking"""
    
    def __init__(self, client: docker.DockerClient):
        """
        Initialize the image builder
        
        Args:
            client: Docker client instance
        """
        self.client = client
        self.base_path = self._get_dockerfiles_path()
    
    def _get_dockerfiles_path(self) -> Path:
        """Get the path to Dockerfiles in the package"""
        # Try to find Dockerfiles in package data
        import src.data
        package_path = Path(src.data.__file__).parent
        docker_path = package_path / "docker"
        
        if docker_path.exists():
            return docker_path
        
        # Fallback to development path
        return Path(__file__).parent.parent.parent / "docker" / "base_images"
    
    def check_image_exists(self, image_name: str) -> bool:
        """
        Check if a Docker image exists locally
        
        Args:
            image_name: Name of the image to check
            
        Returns:
            True if image exists, False otherwise
        """
        try:
            self.client.images.get(image_name)
            return True
        except docker.errors.ImageNotFound:
            return False
    
    def build_image(self, distribution: str, show_progress: bool = True) -> bool:
        """
        Build a Docker image for a specific distribution
        
        Args:
            distribution: Distribution name (ubuntu, centos, rocky)
            show_progress: Whether to show build progress
            
        Returns:
            True if build succeeded, False otherwise
        """
        image_name = f"lfcs-practice-{distribution}:latest"
        
        # Check if already exists
        if self.check_image_exists(image_name):
            logger.info(f"Image {image_name} already exists")
            return True
        
        # Get Dockerfile path
        dockerfile_path = self.base_path / distribution
        
        if not dockerfile_path.exists():
            logger.error(f"Dockerfile not found at {dockerfile_path}")
            return False
        
        print(f"\n🔨 Building Docker image: {image_name}")
        print(f"📁 From: {dockerfile_path}")
        print(f"⏱️  This may take 5-20 minutes on first run...\n")
        
        try:
            # Build the image
            image, build_logs = self.client.images.build(
                path=str(dockerfile_path),
                tag=image_name,
                rm=True,
                forcerm=True,
                nocache=False
            )
            
            if show_progress:
                for log in build_logs:
                    if 'stream' in log:
                        print(log['stream'], end='')
                    elif 'status' in log:
                        print(f"  {log['status']}")
                    elif 'error' in log:
                        print(f"❌ Error: {log['error']}")
                        return False
            
            print(f"\n✅ Successfully built {image_name}\n")
            logger.info(f"Successfully built image {image_name}")
            return True
            
        except BuildError as e:
            print(f"\n❌ Build failed for {image_name}")
            print(f"Error: {e}")
            logger.error(f"Build failed for {image_name}: {e}")
            return False
        except APIError as e:
            print(f"\n❌ Docker API error while building {image_name}")
            print(f"Error: {e}")
            logger.error(f"API error building {image_name}: {e}")
            return False
    
    def build_all_images(self, show_progress: bool = True) -> Dict[str, bool]:
        """
        Build all required Docker images
        
        Args:
            show_progress: Whether to show build progress
            
        Returns:
            Dictionary mapping distribution names to build success status
        """
        distributions = ['ubuntu', 'centos', 'rocky']
        results = {}
        
        print("\n" + "="*70)
        print("  DOCKER IMAGE SETUP")
        print("="*70)
        print("\nBuilding Docker images for LFCS practice environments...")
        print("This is a one-time setup that will take 15-20 minutes.\n")
        
        for dist in distributions:
            results[dist] = self.build_image(dist, show_progress)
            
            if not results[dist]:
                print(f"\n⚠️  Warning: Failed to build {dist} image")
                print("You can continue with other distributions or try again later.\n")
        
        # Summary
        print("\n" + "="*70)
        print("  BUILD SUMMARY")
        print("="*70)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        for dist, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"  {dist.ljust(10)} : {status}")
        
        print(f"\n  Built {success_count}/{total_count} images successfully")
        print("="*70 + "\n")
        
        return results
    
    def build_ubuntu_only(self, show_progress: bool = True) -> bool:
        """
        Build only Ubuntu image (faster option)
        
        Args:
            show_progress: Whether to show build progress
            
        Returns:
            True if build succeeded, False otherwise
        """
        print("\n" + "="*70)
        print("  DOCKER IMAGE SETUP (Ubuntu Only)")
        print("="*70)
        print("\nBuilding Ubuntu Docker image for LFCS practice...")
        print("This is a one-time setup that will take ~5 minutes.\n")
        
        result = self.build_image('ubuntu', show_progress)
        
        if result:
            print("\n✅ Ubuntu image ready! You can start practicing now.")
        else:
            print("\n❌ Failed to build Ubuntu image.")
            print("Please check Docker daemon and try again.")
        
        print("="*70 + "\n")
        
        return result
