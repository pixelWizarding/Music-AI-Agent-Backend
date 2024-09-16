import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings

# Initialize Firestore with credentials
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)
db = firestore.client()


def get_firestore_db():
    return db
