import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import gc
from sentence_transformers import SentenceTransformer, util

# 1. إعداد الفايربيس
cred_path = 'firebase_key.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. تحميل الموديل (تأكدي من استخدام النسخة الخفيفة عشان الرام)
print(">>> Loading AI Model...")
model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

def calculate_matching(new_report):
    # (نفس كودك حق المطابقة اللي كان شغال تمام)
    pass 

def on_snapshot(col_snapshot, changes, read_time):
    for change in changes:
        if change.type.name in ['ADDED', 'MODIFIED']:
            doc = change.document
            data = doc.to_dict()
            if data.get('ai_status') == 'pending':
                try:
                    match_id = calculate_matching(data)
                    # ... تحديث الفايربيس ...
                finally:
                    gc.collect()

if __name__ == "__main__":
    print(">>> Background Worker is Running and Watching Firestore...")
    db.collection('reports').on_snapshot(on_snapshot)
    
    # حلقة بسيطة عشان الكود ما يوقف
    while True:
        time.sleep(10)
