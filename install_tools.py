#!/usr/bin/env python3
"""
Kali Linux Security Tools Auto-Installer
يثبت مجموعة من أدوات الأمن السيبراني على Kali Linux
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class Colors:
    """ألوان للطباعة الملونة في الترمينال"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ToolsInstaller:
    def __init__(self):
        self.tools_dir = Path("/opt")
        self.bin_dir = Path("/usr/local/bin")
        
        # قائمة الحزم من apt
        self.apt_packages = [
            "git", "curl", "wget", "python3", "python3-pip", 
            "python3-venv", "build-essential", "libssl-dev", 
            "libffi-dev", "default-jre", "libcap2-bin",
            "nmap", "nikto", "tcpdump", "whois", "dnsutils",
            "libimage-exiftool-perl", "wireshark"
        ]
        
        # أدوات Python من pip
        self.pip_tools = ["theHarvester"]
        
        # أدوات من GitHub
        self.github_tools = {
            "sqlmap": {
                "repo": "https://github.com/sqlmapproject/sqlmap.git",
                "install_path": self.tools_dir / "sqlmap",
                "bin_link": "sqlmap.py"
            },
            "theHarvester": {
                "repo": "https://github.com/laramies/theHarvester.git",
                "install_path": self.tools_dir / "theHarvester",
                "bin_link": "theHarvester.py"
            },
            "nikto": {
                "repo": "https://github.com/sullo/nikto.git",
                "install_path": self.tools_dir / "nikto",
                "bin_link": "program/nikto.pl"
            },
            "setoolkit": {
                "repo": "https://github.com/trustedsec/social-engineer-toolkit.git",
                "install_path": self.tools_dir / "setoolkit",
                "bin_link": "setoolkit"
            }
        }

    def print_msg(self, msg, color=Colors.OKBLUE):
        """طباعة رسالة ملونة"""
        print(f"{color}{msg}{Colors.ENDC}")

    def check_root(self):
        """التحقق من صلاحيات root"""
        if os.geteuid() != 0:
            self.print_msg("⚠️  يجب تشغيل السكربت بصلاحيات root!", Colors.FAIL)
            self.print_msg("استخدم: sudo python3 install_tools.py", Colors.WARNING)
            sys.exit(1)

    def run_command(self, cmd, shell=False):
        """تنفيذ أمر في الشل"""
        try:
            if shell:
                result = subprocess.run(cmd, shell=True, check=True, 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, check=True, 
                                      capture_output=True, text=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def update_system(self):
        """تحديث قوائم الحزم"""
        self.print_msg("\n[*] تحديث قوائم الحزم...", Colors.HEADER)
        success, output = self.run_command("apt update", shell=True)
        if success:
            self.print_msg("✓ تم التحديث بنجاح", Colors.OKGREEN)
        else:
            self.print_msg("✗ فشل التحديث", Colors.FAIL)
            return False
        return True

    def install_apt_packages(self):
        """تثبيت الحزم من apt"""
        self.print_msg("\n[*] تثبيت الحزم من apt...", Colors.HEADER)
        
        for package in self.apt_packages:
            self.print_msg(f"  → تثبيت {package}...", Colors.OKCYAN)
            cmd = f"apt install -y {package}"
            success, output = self.run_command(cmd, shell=True)
            
            if success:
                self.print_msg(f"  ✓ تم تثبيت {package}", Colors.OKGREEN)
            else:
                self.print_msg(f"  ✗ فشل تثبيت {package}", Colors.WARNING)

    def install_pip_tools(self):
        """تثبيت أدوات Python من pip"""
        self.print_msg("\n[*] تثبيت أدوات Python...", Colors.HEADER)
        
        # ترقية pip أولاً
        self.run_command("pip3 install --upgrade pip", shell=True)
        
        for tool in self.pip_tools:
            self.print_msg(f"  → تثبيت {tool} من pip...", Colors.OKCYAN)
            cmd = f"pip3 install {tool}"
            success, output = self.run_command(cmd, shell=True)
            
            if success:
                self.print_msg(f"  ✓ تم تثبيت {tool}", Colors.OKGREEN)
            else:
                self.print_msg(f"  ⚠ فشل تثبيت {tool} من pip، سيتم تثبيته من GitHub", Colors.WARNING)

    def clone_github_tool(self, name, info):
        """استنساخ أداة من GitHub"""
        install_path = info["install_path"]
        repo = info["repo"]
        
        # حذف المجلد القديم إذا كان موجوداً
        if install_path.exists():
            self.print_msg(f"  ⚠ {name} موجود مسبقاً، سيتم إعادة التثبيت...", Colors.WARNING)
            shutil.rmtree(install_path)
        
        # استنساخ المستودع
        self.print_msg(f"  → استنساخ {name}...", Colors.OKCYAN)
        cmd = f"git clone {repo} {install_path}"
        success, output = self.run_command(cmd, shell=True)
        
        if not success:
            self.print_msg(f"  ✗ فشل استنساخ {name}", Colors.FAIL)
            return False
        
        return True

    def setup_tool_link(self, name, info):
        """إنشاء رابط للأداة في /usr/local/bin"""
        install_path = info["install_path"]
        bin_link = info["bin_link"]
        
        tool_script = install_path / bin_link
        link_path = self.bin_dir / name
        
        if not tool_script.exists():
            self.print_msg(f"  ⚠ ملف {bin_link} غير موجود", Colors.WARNING)
            return False
        
        # جعل الملف قابلاً للتنفيذ
        os.chmod(tool_script, 0o755)
        
        # إنشاء symlink
        if link_path.exists():
            link_path.unlink()
        
        os.symlink(tool_script, link_path)
        self.print_msg(f"  ✓ تم إنشاء رابط: {link_path}", Colors.OKGREEN)
        
        return True

    def install_tool_dependencies(self, name, install_path):
        """تثبيت تبعيات الأداة إذا كان فيها requirements.txt"""
        req_file = install_path / "requirements.txt"
        
        if req_file.exists():
            self.print_msg(f"  → تثبيت تبعيات {name}...", Colors.OKCYAN)
            cmd = f"pip3 install -r {req_file}"
            success, output = self.run_command(cmd, shell=True)
            
            if success:
                self.print_msg(f"  ✓ تم تثبيت التبعيات", Colors.OKGREEN)
            else:
                self.print_msg(f"  ⚠ بعض التبعيات فشلت", Colors.WARNING)

    def install_github_tools(self):
        """تثبيت الأدوات من GitHub"""
        self.print_msg("\n[*] تثبيت الأدوات من GitHub...", Colors.HEADER)
        
        for name, info in self.github_tools.items():
            self.print_msg(f"\n  → معالجة {name}...", Colors.BOLD)
            
            # استنساخ الأداة
            if not self.clone_github_tool(name, info):
                continue
            
            # تثبيت التبعيات
            self.install_tool_dependencies(name, info["install_path"])
            
            # إنشاء الرابط
            self.setup_tool_link(name, info)
            
            self.print_msg(f"  ✓ تم تثبيت {name} بنجاح", Colors.OKGREEN)

    def final_setup(self):
        """إعدادات نهائية"""
        self.print_msg("\n[*] الإعدادات النهائية...", Colors.HEADER)
        
        # إعطاء صلاحيات tcpdump
        self.print_msg("  → إعطاء صلاحيات لـ tcpdump...", Colors.OKCYAN)
        self.run_command("setcap cap_net_raw,cap_net_admin=eip /usr/bin/tcpdump", shell=True)
        
        # إعطاء صلاحيات dumpcap (Wireshark)
        self.print_msg("  → إعطاء صلاحيات لـ dumpcap...", Colors.OKCYAN)
        dumpcap_path = "/usr/bin/dumpcap"
        if os.path.exists(dumpcap_path):
            self.run_command(f"setcap cap_net_raw,cap_net_admin=eip {dumpcap_path}", shell=True)
        
        self.print_msg("  ✓ تمت الإعدادات النهائية", Colors.OKGREEN)

    def print_summary(self):
        """طباعة ملخص التثبيت"""
        self.print_msg("\n" + "="*60, Colors.HEADER)
        self.print_msg("✓ اكتمل التثبيت!", Colors.OKGREEN)
        self.print_msg("="*60, Colors.HEADER)
        
        print("\n📦 الأدوات المثبتة:")
        print("  • nmap, nikto, tcpdump, whois, dig")
        print("  • exiftool, wireshark")
        print("  • sqlmap, theHarvester, setoolkit")
        
        print("\n📍 مواقع الأدوات:")
        for name, info in self.github_tools.items():
            print(f"  • {name}: {info['install_path']}")
        
        print("\n💡 لاستخدام الأدوات، اكتب اسم الأداة مباشرة:")
        print("  $ sqlmap --help")
        print("  $ theHarvester -h")
        print("  $ setoolkit")
        print("  $ nmap -h")
        
        self.print_msg("\n✨ تمتع بالاستخدام!", Colors.OKGREEN)

    def run(self):
        """تشغيل عملية التثبيت الكاملة"""
        self.print_msg("="*60, Colors.HEADER)
        self.print_msg("  🔧 Kali Security Tools Auto-Installer", Colors.BOLD)
        self.print_msg("="*60, Colors.HEADER)
        
        # التحقق من صلاحيات root
        self.check_root()
        
        try:
            # تحديث النظام
            if not self.update_system():
                self.print_msg("\n⚠️  تحذير: فشل تحديث النظام، لكن سنستمر...", Colors.WARNING)
            
            # تثبيت حزم apt
            self.install_apt_packages()
            
            # تثبيت أدوات pip
            self.install_pip_tools()
            
            # تثبيت أدوات GitHub
            self.install_github_tools()
            
            # الإعدادات النهائية
            self.final_setup()
            
            # طباعة الملخص
            self.print_summary()
            
        except KeyboardInterrupt:
            self.print_msg("\n\n⚠️  تم إلغاء التثبيت من قبل المستخدم", Colors.WARNING)
            sys.exit(1)
        except Exception as e:
            self.print_msg(f"\n✗ حدث خطأ: {str(e)}", Colors.FAIL)
            sys.exit(1)


if __name__ == "__main__":
    installer = ToolsInstaller()
    installer.run()