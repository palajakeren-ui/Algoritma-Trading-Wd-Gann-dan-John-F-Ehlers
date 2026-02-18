#!/bin/bash
# =====================================================
# Gann Quant AI - Backup Script (Linux/Mac)
# Automated backup for trading data, configs, and vault
# =====================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="gann_quant_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              GANN QUANT AI - BACKUP SCRIPT                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}[1/6] Creating backup directory...${NC}"
mkdir -p "${BACKUP_PATH}"

echo -e "${YELLOW}[2/6] Backing up configurations...${NC}"
if [ -d "${PROJECT_DIR}/configs" ]; then
    cp -r "${PROJECT_DIR}/configs" "${BACKUP_PATH}/"
    echo -e "  ${GREEN}✓ configs${NC}"
else
    echo -e "  ${YELLOW}⚠ configs directory not found${NC}"
fi

echo -e "${YELLOW}[3/6] Backing up trading data...${NC}"
if [ -d "${PROJECT_DIR}/outputs" ]; then
    cp -r "${PROJECT_DIR}/outputs" "${BACKUP_PATH}/"
    echo -e "  ${GREEN}✓ outputs (journal, trades)${NC}"
else
    echo -e "  ${YELLOW}⚠ outputs directory not found${NC}"
fi

if [ -d "${PROJECT_DIR}/data" ]; then
    cp -r "${PROJECT_DIR}/data" "${BACKUP_PATH}/"
    echo -e "  ${GREEN}✓ data (market data cache)${NC}"
else
    echo -e "  ${YELLOW}⚠ data directory not found${NC}"
fi

echo -e "${YELLOW}[4/6] Backing up secure vault (encrypted)...${NC}"
if [ -d "${PROJECT_DIR}/vault" ]; then
    cp -r "${PROJECT_DIR}/vault" "${BACKUP_PATH}/"
    echo -e "  ${GREEN}✓ vault (encrypted credentials)${NC}"
else
    echo -e "  ${YELLOW}⚠ vault directory not found${NC}"
fi

echo -e "${YELLOW}[5/6] Backing up logs...${NC}"
if [ -d "${PROJECT_DIR}/logs" ]; then
    cp -r "${PROJECT_DIR}/logs" "${BACKUP_PATH}/"
    echo -e "  ${GREEN}✓ logs${NC}"
else
    echo -e "  ${YELLOW}⚠ logs directory not found${NC}"
fi

# Create backup info file
echo -e "${YELLOW}[6/6] Creating backup metadata...${NC}"
cat > "${BACKUP_PATH}/backup_info.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "$(date -Iseconds)",
    "project": "Gann Quant AI",
    "version": "2.2.0",
    "contents": [
        "configs",
        "outputs",
        "data",
        "vault",
        "logs"
    ],
    "hostname": "$(hostname)",
    "user": "$(whoami)"
}
EOF
echo -e "  ${GREEN}✓ backup_info.json${NC}"

# Compress backup
echo -e "\n${YELLOW}Compressing backup...${NC}"
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_PATH}"

# Calculate size
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                     BACKUP COMPLETED                             ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  File: ${BACKUP_NAME}.tar.gz${NC}"
echo -e "${GREEN}║  Size: ${BACKUP_SIZE}${NC}"
echo -e "${GREEN}║  Path: ${BACKUP_DIR}/${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"

# Cleanup old backups (keep last 10)
echo -e "\n${YELLOW}Cleaning up old backups (keeping last 10)...${NC}"
cd "${BACKUP_DIR}"
ls -t *.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
BACKUP_COUNT=$(ls -1 *.tar.gz 2>/dev/null | wc -l)
echo -e "${GREEN}✓ ${BACKUP_COUNT} backups currently stored${NC}"

echo -e "\n${BLUE}Backup script completed successfully!${NC}"
