"""
Gann Quant AI - Python Backup Script
Cross-platform backup utility.
"""
import os
import sys
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


def print_header():
    print("\n" + "=" * 60)
    print("         GANN QUANT AI - BACKUP UTILITY")
    print("=" * 60 + "\n")


def create_backup(project_dir: str = None, keep_backups: int = 10):
    """Create a backup of trading data."""
    print_header()
    
    project_dir = Path(project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backup_dir = project_dir / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"gann_quant_backup_{timestamp}"
    backup_path = backup_dir / backup_name
    backup_path.mkdir(exist_ok=True)
    
    # Directories to backup
    dirs_to_backup = ["configs", "outputs", "data", "vault", "logs"]
    
    print("[1/3] Backing up directories...")
    for dir_name in dirs_to_backup:
        source = project_dir / dir_name
        if source.exists():
            dest = backup_path / dir_name
            shutil.copytree(source, dest)
            print(f"  ✓ {dir_name}")
        else:
            print(f"  - {dir_name} (not found)")
    
    # Create metadata
    print("[2/3] Creating backup metadata...")
    metadata = {
        "backup_name": backup_name,
        "timestamp": datetime.now().isoformat(),
        "project": "Gann Quant AI",
        "version": "2.2.0",
        "hostname": os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown")),
        "user": os.environ.get("USERNAME", os.environ.get("USER", "unknown"))
    }
    with open(backup_path / "backup_info.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Compress
    print("[3/3] Compressing backup...")
    zip_path = backup_dir / f"{backup_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in backup_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(backup_path)
                zipf.write(file_path, arcname)
    
    # Remove uncompressed folder
    shutil.rmtree(backup_path)
    
    # Get size
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    
    print(f"\n✓ Backup completed: {backup_name}.zip ({size_mb:.2f} MB)")
    print(f"  Location: {backup_dir}")
    
    # Cleanup old backups
    backups = sorted(backup_dir.glob("gann_quant_backup_*.zip"), reverse=True)
    for old_backup in backups[keep_backups:]:
        old_backup.unlink()
        print(f"  Removed old: {old_backup.name}")
    
    print(f"\nTotal backups: {min(len(backups), keep_backups)}")
    return str(zip_path)


def restore_backup(backup_file: str, project_dir: str = None, force: bool = False):
    """Restore from a backup file."""
    print_header()
    
    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"ERROR: Backup file not found: {backup_file}")
        return False
    
    project_dir = Path(project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print(f"Restoring from: {backup_path.name}")
    
    if not force:
        confirm = input("This will overwrite existing data. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Restore cancelled.")
            return False
    
    # Extract
    print("[1/2] Extracting backup...")
    temp_dir = Path(os.environ.get("TEMP", "/tmp")) / f"gann_restore_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    with zipfile.ZipFile(backup_path, 'r') as zipf:
        zipf.extractall(temp_dir)
    
    # Restore
    print("[2/2] Restoring data...")
    dirs_to_restore = ["configs", "outputs", "data", "vault", "logs"]
    for dir_name in dirs_to_restore:
        source = temp_dir / dir_name
        dest = project_dir / dir_name
        if source.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)
            print(f"  ✓ {dir_name}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("\n✓ Restore completed successfully!")
    return True


def list_backups(project_dir: str = None):
    """List available backups."""
    print_header()
    
    project_dir = Path(project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backup_dir = project_dir / "backups"
    
    if not backup_dir.exists():
        print("No backups found.")
        return
    
    backups = sorted(backup_dir.glob("gann_quant_backup_*.zip"), reverse=True)
    
    if not backups:
        print("No backups found.")
        return
    
    print(f"Available backups ({len(backups)}):\n")
    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"  {i}. {backup.name}")
        print(f"     Size: {size_mb:.2f} MB | Date: {mtime.strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gann Quant AI Backup Utility")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create backup
    create_parser = subparsers.add_parser("create", help="Create a backup")
    create_parser.add_argument("--keep", type=int, default=10, help="Number of backups to keep")
    
    # Restore backup
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("file", help="Backup file path")
    restore_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # List backups
    list_parser = subparsers.add_parser("list", help="List available backups")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_backup(keep_backups=args.keep)
    elif args.command == "restore":
        restore_backup(args.file, force=args.force)
    elif args.command == "list":
        list_backups()
    else:
        # Default: create backup
        create_backup()
