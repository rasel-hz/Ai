# -*- coding: utf-8 -*-
import firebase_admin
from firebase_admin import credentials, firestore
import time
import threading
import os
from flask import Flask

# --- 1. إعداد Flask للتشغيل على Render (الخطة المجانية) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Dhallah AI Engine is Running!"

def start_server():
    # Render يستخدم Port ديناميكي، غالباً 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. إعداد الاتصال بـ Firebase ---
# تأكدي أن هذا الاسم يطابق ما وضعتيه في Secret Files على Render
cred_path = 'firebase_key.json'

try:
    if not firebase_admin._apps:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(">>> [SUCCESS] Firebase initialized successfully.")
        else:
            print(f">>> [ERROR] Credentials file NOT FOUND at {cred_path}")
except Exception as e:
    print(f">>> [ERROR] Firebase initialization failed: {e}")

db = firestore.client()

# --- 3. دالة معالجة البيانات (on_snapshot) ---
# وضعت لكِ الهيكل الأساسي للدالة، تأكدي من وجود منطق المطابقة (Matching) داخلها
def on_snapshot(col_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'ADDED' or change.type.name == 'MODIFIED':
            doc = change.document
            data = doc.to_dict()
            doc_id = doc.id
            
            # فحص إذا كان البلاغ يحتاج معالجة
            if data.get('ai_status') == 'pending':
                print(f"\n>>> [FIREBASE] New pending report detected: {doc_id}")
                
                try:
                    # تحديث الحالة إلى جاري المعالجة
                    db.collection('reports').document(doc_id).update({'ai_status': 'processing'})
                    
                    # --- منطق الذكاء الاصطناعي الخاص بكِ يبدأ هنا ---
                    # (هنا تضعين كود الـ Embedding والمطابقة مع Qdrant أو المصفوفات)
                    
                    print(f">>> [AI] Processing logic for {doc_id} goes here...")
                    
                    # مثال لتحديث الحالة بعد النجاح:
                    db.collection('reports').document(doc_id).update({'ai_status': 'completed'})
                    print(f">>> [SUCCESS] Matching completed for {doc_id}")
                    
                except Exception as e:
                    print(f">>> [ERROR] Failed to process {doc_id}: {e}")
                    db.collection('reports').document(doc_id).update({'ai_status': 'error'})

# --- 4. تشغيل المحرك ---
if __name__ == "__main__":
    # أ. تشغيل Flask في Thread منفصل ليبقى السيرفر "Live"
    print(">>> [SYSTEM] Starting Flask Health Check Server...")
    threading.Thread(target=start_server, daemon=True).start()
    
    print(">>> [SYSTEM] Initializing Dhallah AI Engine...")
    print(">>> [SYSTEM] Listening for incoming reports in Firestore...")

    # ب. إعداد مراقب Firebase (Listener)
    try:
        reports_query = db.collection('reports')
        query_watch = reports_query.on_snapshot(on_snapshot)
    except Exception as e:
        print(f">>> [CRITICAL] Failed to start Firestore Listener: {e}")

    # ج. إبقاء الكود يعمل للأبد
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n>>> [STOP] Stopping AI Engine safely...")
