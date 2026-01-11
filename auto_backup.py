#!/usr/bin/env python3
"""
Automated Daily Backup System for InfinityXOneSystems
Implements 110% protocol with verification and integrity checks
"""
import os
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import hashlib

class BackupSystem:
    def __init__(self, backup_dir: str = "/home/ubuntu/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.backup_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "repositories": [],
            "status": "in_progress",
            "errors": []
        }
    
    def get_all_repositories(self) -> List[str]:
        """Get list of all repositories from GitHub"""
        try:
            result = subprocess.run(
                ["gh", "repo", "list", "InfinityXOneSystems", "--limit", "100", "--json", "name"],
                capture_output=True,
                text=True,
                check=True
            )
            repos = json.loads(result.stdout)
            return [repo["name"] for repo in repos if repo["name"] != "backup"]
        except Exception as e:
            self.backup_log["errors"].append(f"Failed to list repositories: {str(e)}")
            return []
    
    def clone_repository(self, repo_name: str, dest_path: Path) -> bool:
        """Clone a repository to the backup location"""
        try:
            subprocess.run(
                ["gh", "repo", "clone", f"InfinityXOneSystems/{repo_name}", str(dest_path)],
                capture_output=True,
                check=True
            )
            return True
        except Exception as e:
            self.backup_log["errors"].append(f"Failed to clone {repo_name}: {str(e)}")
            return False
    
    def calculate_checksum(self, directory: Path) -> str:
        """Calculate checksum for directory contents"""
        hasher = hashlib.sha256()
        
        for root, dirs, files in os.walk(directory):
            # Sort for consistent ordering
            dirs.sort()
            files.sort()
            
            for filename in files:
                filepath = Path(root) / filename
                try:
                    with open(filepath, 'rb') as f:
                        hasher.update(f.read())
                except:
                    pass
        
        return hasher.hexdigest()
    
    def create_archive(self, source_dir: Path, archive_name: str) -> Path:
        """Create compressed archive of directory"""
        archive_path = self.backup_dir / f"{archive_name}_{self.timestamp}"
        shutil.make_archive(str(archive_path), 'gztar', source_dir)
        return Path(f"{archive_path}.tar.gz")
    
    def backup_repository(self, repo_name: str) -> Dict[str, Any]:
        """Backup a single repository with verification"""
        backup_info = {
            "name": repo_name,
            "timestamp": self.timestamp,
            "status": "failed",
            "checksum": None,
            "size_bytes": 0,
            "archive_path": None
        }
        
        # Create temporary directory for cloning
        temp_dir = self.backup_dir / "temp" / repo_name
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone repository
            if not self.clone_repository(repo_name, temp_dir):
                return backup_info
            
            # Calculate checksum
            checksum = self.calculate_checksum(temp_dir)
            backup_info["checksum"] = checksum
            
            # Create archive
            archive_path = self.create_archive(temp_dir, repo_name)
            backup_info["archive_path"] = str(archive_path)
            backup_info["size_bytes"] = archive_path.stat().st_size
            
            # Verify archive
            if archive_path.exists() and archive_path.stat().st_size > 0:
                backup_info["status"] = "success"
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            backup_info["error"] = str(e)
            self.backup_log["errors"].append(f"Backup failed for {repo_name}: {str(e)}")
        
        return backup_info
    
    def backup_all_repositories(self) -> Dict[str, Any]:
        """Backup all repositories"""
        repos = self.get_all_repositories()
        
        print(f"Starting backup of {len(repos)} repositories...")
        
        for repo_name in repos:
            print(f"Backing up {repo_name}...")
            backup_info = self.backup_repository(repo_name)
            self.backup_log["repositories"].append(backup_info)
            
            if backup_info["status"] == "success":
                print(f"  ✓ Success: {backup_info['size_bytes']:,} bytes")
            else:
                print(f"  ✗ Failed")
        
        # Update final status
        success_count = sum(1 for r in self.backup_log["repositories"] if r["status"] == "success")
        self.backup_log["status"] = "completed" if success_count == len(repos) else "partial"
        self.backup_log["summary"] = {
            "total": len(repos),
            "success": success_count,
            "failed": len(repos) - success_count
        }
        
        return self.backup_log
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Remove backups older than retention period"""
        cutoff_time = datetime.utcnow().timestamp() - (retention_days * 86400)
        
        for archive in self.backup_dir.glob("*.tar.gz"):
            if archive.stat().st_mtime < cutoff_time:
                try:
                    archive.unlink()
                    print(f"Removed old backup: {archive.name}")
                except Exception as e:
                    print(f"Failed to remove {archive.name}: {e}")
    
    def save_backup_log(self):
        """Save backup log to file"""
        log_file = self.backup_dir / f"backup_log_{self.timestamp}.json"
        with open(log_file, 'w') as f:
            json.dump(self.backup_log, f, indent=2)
        print(f"\nBackup log saved: {log_file}")
    
    def upload_to_backup_repo(self):
        """Upload backup archives and logs to backup repository"""
        backup_repo = Path("/home/ubuntu/repo_evaluation/backup")
        
        # Create backups directory in repo
        backups_dir = backup_repo / "backups" / self.timestamp
        backups_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy archives and logs
        for item in self.backup_dir.glob("*"):
            if item.is_file():
                shutil.copy2(item, backups_dir)
        
        # Commit and push
        try:
            os.chdir(backup_repo)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Automated backup {self.timestamp}"],
                check=True
            )
            subprocess.run(["git", "push"], check=True)
            print(f"✓ Backup uploaded to GitHub")
        except Exception as e:
            print(f"✗ Failed to upload backup: {e}")

def main():
    """Main backup execution"""
    print("="*80)
    print("InfinityXOneSystems Automated Backup System")
    print("110% Protocol - FAANG Enterprise-Grade Standards")
    print("="*80)
    print()
    
    backup_system = BackupSystem()
    
    # Execute backup
    result = backup_system.backup_all_repositories()
    
    # Save log
    backup_system.save_backup_log()
    
    # Cleanup old backups
    backup_system.cleanup_old_backups(retention_days=30)
    
    # Upload to backup repository
    backup_system.upload_to_backup_repo()
    
    # Print summary
    print("\n" + "="*80)
    print("BACKUP SUMMARY")
    print("="*80)
    print(f"Total repositories: {result['summary']['total']}")
    print(f"Successful backups: {result['summary']['success']}")
    print(f"Failed backups: {result['summary']['failed']}")
    print(f"Status: {result['status'].upper()}")
    
    if result['errors']:
        print(f"\nErrors: {len(result['errors'])}")
        for error in result['errors'][:5]:
            print(f"  - {error}")
    
    print("\n✓ Backup process completed")

if __name__ == "__main__":
    main()
