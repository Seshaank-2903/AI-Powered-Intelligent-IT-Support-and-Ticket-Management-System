import os
import sys
import uuid

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.models.protocol import Protocol
from app.rag.ingestion import ingest_protocol

def seed():
    db = SessionLocal()
    try:
        # Get or create company
        company = db.query(Company).first()
        if not company:
            company = Company(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                name="Acme Corp",
                slug="acme-corp",
                description="Acme Corporation IT"
            )
            db.add(company)
            db.commit()

        user = db.query(User).first()
        if not user:
            user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                email="admin@acme.com",
                name="Admin User",
                company_id=company.id,
                role="SUPER_ADMIN"
            )
            db.add(user)
            db.commit()

        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documents", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        protocols_data = [
            {
                "filename": "Wi-Fi_Access_and_Guest_Network_Protocol.txt",
                "title": "Wi-Fi Access & Guest Password Guide",
                "version": "2.1",
                "content": """COMPANY OFFICIAL IT PROTOCOL: WI-FI & GUEST NETWORK ACCESS

1. Employee Wi-Fi Network:
   - Network SSID: Corporate_Secure
   - Security: WPA2-Enterprise (802.1X)
   - Credentials: Use your standard company SSO username and password.

2. Guest Wi-Fi Network:
   - Network SSID: Company_Guest
   - Guest Wi-Fi Password: CorporateGuest2026!
   - Note: Guest access is limited to standard web browsing (HTTP/HTTPS) and requires re-authentication every 24 hours.

3. Troubleshooting Wi-Fi Issues:
   - If unable to connect, forget network 'Corporate_Secure' and re-enter SSO password.
   - For guest users, verify password 'CorporateGuest2026!' (case-sensitive)."""
            },
            {
                "filename": "VPN_Access_and_Remote_Work_Guide.txt",
                "title": "VPN Access & Connection Protocol",
                "version": "3.0",
                "content": """COMPANY OFFICIAL IT PROTOCOL: VPN ACCESS & TROUBLESHOOTING

1. VPN Client Setup:
   - Client: Cisco AnyConnect Secure Mobility Client
   - Server Portal Address: vpn.company.com

2. Connection Steps:
   - Launch Cisco AnyConnect.
   - Enter target server: vpn.company.com
   - Authenticate with 2FA / Duo Security push notification.

3. Error 800 / Connection Timeout Troubleshooting:
   - Open Command Prompt as Administrator.
   - Run: ipconfig /flushdns
   - Restart the Cisco AnyConnect service and try connecting again."""
            },
            {
                "filename": "Office_Printer_Setup_Guide.txt",
                "title": "Office Printer Setup Protocol",
                "version": "1.2",
                "content": """COMPANY OFFICIAL IT PROTOCOL: OFFICE PRINTER CONFIGURATION

1. 4th Floor Network Printer:
   - Model: HP LaserJet Enterprise M608
   - IP Address: 192.168.10.45
   - Location: 4th Floor Copy Room (East Wing)

2. 2nd Floor Network Printer:
   - Model: Canon ImageRUNNER ADVANCE
   - IP Address: 192.168.10.42
   - Location: 2nd Floor Central Hub

3. Installation:
   - Add printer via Windows Settings -> Devices -> Printers & Scanners -> Add printer using IP address."""
            }
        ]

        for p in protocols_data:
            file_path = os.path.join(uploads_dir, p["filename"])
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(p["content"])

            # Check if protocol exists in DB
            existing = db.query(Protocol).filter(Protocol.title == p["title"]).first()
            if not existing:
                protocol = Protocol(
                    company_id=company.id,
                    title=p["title"],
                    description=p["content"][:150],
                    version=p["version"],
                    file_path=file_path,
                    file_type="txt",
                    status="ACTIVE",
                    created_by=user.id
                )
                db.add(protocol)
                db.commit()
                db.refresh(protocol)

                try:
                    ingest_protocol(db, protocol)
                    print(f"Ingested and activated protocol: {p['title']}")
                except Exception as e:
                    print(f"Warning ingesting {p['title']}: {e}")
            else:
                print(f"Protocol already exists: {p['title']}")

        print("Seeding completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
