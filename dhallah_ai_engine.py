import firebase_admin
from firebase_admin import credentials, firestore
import time
import threading
import os
from flask import Flask
# تأكدي إن هالمكتبات موجودة في requirements.txt
from sentence_transformers import SentenceTransformer, util
from PIL import Image
import requests
from io import BytesIO

# --- 1. تحميل الموديلات (نفس اللي كانت عندك) ---
# ملاحظة: أول تشغيل بياخذ وقت عشان يحمل الموديل
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 

app = Flask(__name__)
@app.route('/')
def health_check(): return "AI Engine is Active"

# --- 2. إعداد الفايربيس ---
cred_path = 'firebase_key.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- 3. دالة المطابقة الحقيقية (التي كانت تعطيك نتائج زينة) ---
def calculate_matching(new_report):
    new_text = new_report.get('description', '')
    # نجلب كل البلاغات الأخرى للمقارنة
    all_reports = db.collection('reports').where('ai_status', '==', 'completed').stream()
    
    for old_doc in all_reports:
        old_data = old_doc.to_dict()
        old_text = old_data.get('description', '')
        
        # حساب تشابه النصوص (نفس كودك القديم)
        emb1 = model.encode(new_text, convert_to_tensor=True)
        emb2 = model.encode(old_text, convert_to_tensor=True)
        cosine_scores = util.cos_sim(emb1, emb2)
        
        score = cosine_scores.item()
        print(f"Checking {old_doc.id} - Similarity: {score:.2f}")

        # إذا التشابه عالي (مثلاً أكثر من 0.8) نعتبره تطابق
        if score > 0.80: 
            return old_doc.id # وجدنا التطابق!
    
    return None

def on_snapshot(col_snapshot, changes, read_time):
    for change in changes:
        if change.type.name in ['ADDED', 'MODIFIED']:
            doc = change.document
            data = doc.to_dict()
            if data.get('ai_status') == 'pending':
                print(f">>> Processing report: {doc.id}")
                match_id = calculate_matching(data)
                
                if match_id:
                    db.collection('reports').document(doc.id).update({
                        'ai_status': 'completed',
                        'match_found': True,
                        'matched_with': match_id
                    })
                    print(f">>> MATCH FOUND: {doc.id} with {match_id}")
                else:
                    db.collection('reports').document(doc.id).update({
                        'ai_status': 'completed',
                        'match_found': False
                    })
                    print(">>> No match found.")

# --- 4. التشغيل ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    
    print(">>> AI Engine is back with original logic...")
    db.collection('reports').on_snapshot(on_snapshot)
    while True: time.sleep(1)
