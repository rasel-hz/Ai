# -*- coding: utf-8 -*-
import firebase_admin
from firebase_admin import credentials, firestore
import time
import threading
import os
from flask import Flask
from colorama import Fore, init

# تهيئة الألوان للـ Logs
init(autoreset=True)

# --- 1. إعداد Flask للتشغيل على Render (عشان ما يطفي السيرفر) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Dhallah AI Engine is Running!"

def start_server():
    # Render يطلب تشغيل السيرفر على بورت معين (غالباً 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. إعداد الاتصال بـ Firebase ---
# تأكدي أن اسم الملف هنا يطابق ما وضعتيه في Secret Files على Render
cred_path = 'firebase_key.json'

try:
    if not firebase_admin._apps:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print(f"{Fore.GREEN}>>> Firebase initialized successfully.")
        else:
            print(f"{Fore.RED}>>> ERROR: {cred_path} NOT FOUND! Check Render Secret Files.")
except Exception as e:
    print(f"{Fore.RED}>>> Firebase initialization failed: {e}")

db = firestore.client()

# --- 3. دالة معالجة البلاغات (on_snapshot) ---
def on_snapshot(col_snapshot, changes, read_time):
    for change in changes:
        # نعالج البلاغات المضافة حديثاً أو المعدلة
        if change.type.name in ['ADDED', 'MODIFIED']:
            doc = change.document
            data = doc.to_dict()
            doc_id = doc.id
            
            # فحص إذا كانت الحالة 'pending' لبدء محرك الذكاء الاصطناعي
            if data.get('ai_status') == 'pending':
                print(f"\n{Fore.CYAN}[FIREBASE] New report detected: {doc_id}")
                
                try:
                    # تحديث الحالة إلى processing لمنع التكرار
                    db.collection('reports').document(doc_id).update({'ai_status': 'processing'})
                    
                    # -------------------------------------------------------
                    # (هنا يوضع منطق المطابقة الخاص بكِ - Matching Logic)
                    # -------------------------------------------------------
                    print(f"{Fore.YELLOW}[AI] Starting matching process for {doc_id}...")
                    
                    # مثال لمحاكاة الانتهاء (استبدليه بكود الـ Embedding الخاص بكِ)
                    time.sleep(2) 
                    
                    db.collection('reports').document(doc_id).update({'ai_status': 'completed'})
                    print(f"{Fore.GREEN}[SUCCESS] Matching completed for {doc_id}")
                    
                except Exception as e:
                    print(f"{Fore.RED}[ERROR] Processing failed for {doc_id}: {e}")
                    db.collection('reports').document(doc_id).update({'ai_status': 'error'})

# --- 4. تشغيل النظام ---
if __name__ == "__main__":
    # أ. تشغيل سيرفر الويب في Thread منفصل ليبقى Render "صاحي"
    print(f"{Fore.BLUE}>>> Starting Flask server for Health Check...")
    threading.Thread(target=start_server, daemon=True).start()
    
    print(f"{Fore.BLUE}>>> Initializing Dhallah AI Engine...")
    print(f"{Fore.BLUE}>>> Listening for incoming reports in Firestore...")

    # ب. إعداد مراقب Firebase (Listener)
    try:
        reports_query = db.collection('reports')
        query_watch = reports_query.on_snapshot(on_snapshot)
    except Exception as e:
        print(f"{Fore.RED}>>> CRITICAL: Failed to start Firestore Listener: {e}")

    # ج. حلقة لمنع البرنامج من الإغلاق
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}>>> Stopping AI Engine safely...")
