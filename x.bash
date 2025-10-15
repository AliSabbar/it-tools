py "$@"
SH
    chmod +x /usr/local/bin/setoolkit || true
  fi
fi

# ---------- wireshark non-root setup ----------
if cmd_exists wireshark || dpkg -l | grep -qi wireshark; then
  log "Configuring Wireshark for non-root capture (setuid via debconf and group)..."
  echo "wireshark-common/install-setuid boolean true" | debconf-set-selections || true
  groupadd -f wireshark || true
  usermod -aG wireshark "$TARGET_USER" || true

  if cmd_exists dumpcap; then
    DUMPCAP_PATH=$(command -v dumpcap)
    log "Setting dumpcap group and capabilities ($DUMPCAP_PATH)..."
    chgrp wireshark "$DUMPCAP_PATH" || true
    chmod 750 "$DUMPCAP_PATH" || true
    # setcap may fail if not supported, ignore errors
    setcap 'cap_net_raw,cap_net_admin+eip' "$DUMPCAP_PATH" || true
  fi
fi

# ---------- post-install: upgrade pip tools ----------
log "Upgrading pip-installed tools (best-effort)..."
pip3 install --upgrade theHarvester || true

# ---------- cleanup ----------
log "Cleaning up apt caches..."
apt-get autoremove -y || true
apt-get autoclean -y || true

# ---------- summary ----------
log "Installation summary (locations or 'not found'):"
echo " - nmap:    $(command -v nmap || echo 'not found')"
echo " - wireshark: $(command -v wireshark || echo 'not found')"
echo " - nikto:   $(command -v nikto || echo '/usr/local/bin/nikto (or not found)')"
echo " - exiftool: $(command -v exiftool || echo 'libimage-exiftool-perl (module)')"
echo " - tcpdump: $(command -v tcpdump || echo 'not found')"
echo " - sqlmap:  $(command -v sqlmap || echo '/usr/local/bin/sqlmap (or not found)')"
echo " - whois:   $(command -v whois || echo 'not found')"
echo " - dig:     $(command -v dig || echo 'not found')"
echo " - theHarvester: $(command -v theHarvester || echo '/usr/local/bin/theHarvester (or not found)')"
echo " - setoolkit: $(command -v setoolkit || echo '/usr/local/bin/setoolkit (or not found)')"

cat <<'INFO'

ملاحظات نهائية:
- لازم تسوّي logout/login أو تشغّل: newgrp wireshark
  حتى تنفّذ تغييرات مجموعة wireshark للمستخدم.
- بعض الأوامر (مثلاً setcap) تحتاج امتيازات kernel/policies مناسبة؛ قد تفشل على بعض الأنظمة.
- شغّل فقط على أجهزة تملكها أو لديك إذن لاختبارها.

INFO

log "Done."

#!/usr/bin/env bash
# install_security_tools.sh
# بسيط وعملي: يثبت أدوات أمنية شائعة، ويعمل fallbacks من GitHub عند الحاجة.
# Targets: Debian / Ubuntu / Kali
set -euo pipefail
IFS=$'\n\t'

# -------- config --------
DEBIAN_FRONTEND=noninteractive
APT_COMMON=(
  git curl wget python3 python3-pip python3-venv build-essential \
  libssl-dev libffi-dev default-jre libcap2-bin
)
APT_TOOLS=(
  nmap nikto tcpdump whois dnsutils libimage-exiftool-perl wireshark
)
# Git fallbacks (if not in apt)
SQLMAP_REPO="https://github.com/sqlmapproject/sqlmap.git"
THEHARV_REPO="https://github.com/laramies/theHarvester.git"
NIKTO_REPO="https://github.com/sullo/nikto.git"
SETOOLKIT_REPO="https://github.com/trustedsec/social-engineer-toolkit.git"

# -------- helpers --------
log(){ echo -e "\n\033[1;34m==> $*\033[0m"; }
err(){ echo -e "\n\033[1;31m!! $*\033[0m" >&2; }
require_root(){
  if [[ $EUID -ne 0 ]]; then
    err "Please run as root: sudo bash $0"
    exit 1
  fi
}
cmd_exists(){ command -v "$1" >/dev/null 2>&1; }

# -------- start --------
require_root
export DEBIAN_FRONTEND

TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
log "Target user for wireshark group: $TARGET_USER"

if ! cmd_exists apt-get; then
  err "apt-get not found. Supported: Debian/Ubuntu/Kali only."
  exit 1
fi

log "Updating & upgrading system (this may take time)..."
apt-get update -y
apt-get upgrade -y

log "Installing common packages..."
apt-get install -y "${APT_COMMON[@]}"

log "Installing tools from apt (if available)..."
# try to install all; apt will return non-zero if a package name is wrong,
# so install joined but ignore failures to proceed to fallbacks
if ! apt-get install -y "${APT_TOOLS[@]}"; then
  log "Some apt packages failed to install — continuing with fallbacks where possible."
fi

# ensure pip exists and is fresh
if ! cmd_exists pip3; then
  log "Installing python3-pip..."
  apt-get install -y python3-pip
fi
log "Upgrading pip..."
pip3 install --upgrade pip setuptools wheel

# theHarvester via pip preferred
if ! cmd_exists theHarvester; then
  log "Installing theHarvester via pip..."
  if ! pip3 install theHarvester --upgrade; then
    log "pip install theHarvester failed — will use git fallback."
  fi
fi

# ---------- fallbacks: sqlmap ----------
if ! cmd_exists sqlmap; then
  log "Installing sqlmap from GitHub..."
  if [[ -d /opt/sqlmap ]]; then
    git -C /opt/sqlmap pull || true
  else
    git clone --depth=1 "$SQLMAP_REPO" /opt/sqlmap || true
  fi
  if [[ -f /opt/sqlmap/sqlmap.py ]]; then
    ln -sf /opt/sqlmap/sqlmap.py /usr/local/bin/sqlmap
    chmod +x /usr/local/bin/sqlmap || true
  fi
fi

# ---------- fallbacks: theHarvester ----------
if ! cmd_exists theHarvester; then
  log "Installing theHarvester from GitHub to /opt/theHarvester..."
  if [[ -d /opt/theHarvester ]]; then
    git -C /opt/theHarvester pull || true
  else
    git clone --depth=1 "$THEHARV_REPO" /opt/theHarvester || true
  fi
  if [[ -f /opt/theHarvester/theHarvester.py ]]; then
    cat > /usr/local/bin/theHarvester <<'PY'
#!/usr/bin/env python3
import sys, os
os.execv("/usr/bin/python3", ["/usr/bin/python3", "/opt/theHarvester/theHarvester.py"] + sys.argv[1:])
PY
    chmod +x /usr/local/bin/theHarvester || true
  fi
fi

# ---------- fallbacks: nikto ----------
if ! cmd_exists nikto; then
  log "Installing nikto from GitHub to /opt/nikto..."
  if [[ -d /opt/nikto ]]; then
    git -C /opt/nikto pull || true
  else
    git clone --depth=1 "$NIKTO_REPO" /opt/nikto || true
  fi
  if [[ -f /opt/nikto/program/nikto.pl ]]; then
    ln -sf /opt/nikto/program/nikto.pl /usr/local/bin/nikto
    chmod +x /usr/local/bin/nikto || true
  fi
fi

# ---------- fallbacks: setoolkit ----------
if ! cmd_exists setoolkit; then
  log "Installing Social-Engineer Toolkit (setoolkit) fallback..."
  if [[ -d /opt/setoolkit ]]; then
    git -C /opt/setoolkit pull || true
  else
    git clone --depth=1 "$SETOOLKIT_REPO" /opt/setoolkit || true
  fi
  if [[ -f /opt/setoolkit/setup.py ]]; then
    cat > /usr/local/bin/setoolkit <<'SH'
#!/usr/bin/env bash
python3 /opt/setoolkit/setup.

