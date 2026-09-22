import random
import string

STATUS_LABELS = {
    "yangi": "🆕 Yangi",
    "jarayonda": "⏳ Jarayonda",
    "bajarildi": "✅ Bajarildi",
    "rad_etildi": "❌ Rad etildi",
}


def generate_anon_code() -> str:
    """Talaba uchun tasodifiy anonim kod, masalan: T-8F2A1"""
    chars = string.ascii_uppercase + string.digits
    return "T-" + "".join(random.choices(chars, k=5))
