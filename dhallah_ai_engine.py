import firebase_admin
from firebase_admin import credentials, firestore
import time
import threading
from flask import Flask
import os

# 1. إعداد Flask لـ Render
app = Flask(__name__)
@app.route('/')
def health_check():
    return "Dhallah AI Engine is Live!"

def start_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. إعداد Firebase
cred_path = 'firebase_key.json'
try:
    if not firebase_admin._apps:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(">>> [SUCCESS] Firebase initialized successfully.")
        else:
            print(f">>> [ERROR] JSON file not found at {cred_path}")
except Exception as e:
    print(f">>> [ERROR] Firebase init failed: {e}")

db = firestore.client()

# 3. دالة معالجة البلاغ (تأكدي أن منطق الذكاء الخاص بكِ هنا)
def process_report(doc):
    doc_id = doc.id
    data = doc.to_dict()
    print(f">>> [AI] Processing report: {doc_id}...")
    
    try:
        # --- هنا يوضع منطق المطابقة الخاص بكِ ---
        # مثال بسيط للتحديث:
        db.collection('reports').document(doc_id).update({'ai_status': 'completed'})
        print(f">>> [SUCCESS] Report {doc_id} updated to completed.")
    except Exception as e:
        print(f">>> [ERROR] Failed to process {doc_id}: {e}")
        db.collection('reports').document(doc_id).update({'ai_status': 'error'})

# 4. دالة الفحص الدوري (بديلاً عن on_snapshot)
def monitor_reports():
    print(">>> [SYSTEM] Starting periodic scan (every 20 seconds)...")
    while True:
        try:
            reports_ref = db.collection('reports').where('ai_status', '==', 'pending').stream()
            found = False
            for doc in reports_ref:
                found = True
                process_report(doc)
            
            if not found:
                print(">>> [IDLE] No pending reports found. Sleeping...")
                
        except Exception as e:
            print(f">>> [CRITICAL] Scan error: {e}")
        
        time.sleep(20)

if __name__ == "__main__":
    # تشغيل Flask في Thread منفصل
    print(">>> [SYSTEM] Launching Flask health check server...")
    threading.Thread(target=start_flask, daemon=True).start()
    
    # تشغيل مراقب التقارير
    monitor_reports()
