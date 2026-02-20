import hashlib

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class SecureCoder:
    def __init__(self, key_str: str):
        # 1. Kalitni har doim 32 baytli (AES-256) formatga keltiramiz
        self.key = hashlib.sha256(key_str.encode()).digest()
        # 2. IV ni ham kalitdan hosil qilamiz (Bu deterministik bo'lishini ta'minlaydi)
        self.iv = hashlib.md5(key_str.encode()).digest()

    def encrypt(self, text: str) -> str:
        # Shifrlash
        cipher = Cipher(algorithms.AES(self.key), modes.CTR(self.iv))
        encryptor = cipher.encryptor()
        crypted_bytes = encryptor.update(text.encode()) + encryptor.finalize()
        # Natijani terminal va fayl tizimi uchun toza (hex) formatda qaytaramiz
        return crypted_bytes.hex()

    def decrypt(self, hex_str: str) -> str:
        # Qayta tiklash
        cipher = Cipher(algorithms.AES(self.key), modes.CTR(self.iv))
        decryptor = cipher.decryptor()
        try:
            decrypted_bytes = (
                decryptor.update(bytes.fromhex(hex_str)) + decryptor.finalize()
            )
            return decrypted_bytes.decode()
        except Exception:
            return "Xato: Noto'g'ri kalit yoki ma'lumot"
