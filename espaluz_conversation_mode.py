"""
EspaLuz Conversation Mode
========================
Real-time voice translation like Google Translate.
Voice -> Transcribe -> Translate -> Voice response

Supports: Spanish ↔ English ↔ Russian
"""

from datetime import datetime

class ConversationMode:
    """Manages conversation mode state for users"""
    
    def __init__(self):
        self._active_users = {}
    
    def is_active(self, user_id):
        """Check if user has conversation mode active"""
        user_id = str(user_id)
        return user_id in self._active_users and self._active_users[user_id].get('active', False)
    
    def get_target_language(self, user_id):
        """Get target language for translation"""
        user_id = str(user_id)
        if user_id in self._active_users:
            return self._active_users[user_id].get('target_lang', 'es')
        return 'es'
    
    def activate(self, user_id, target_lang='es'):
        """Activate conversation mode for user"""
        user_id = str(user_id)
        self._active_users[user_id] = {
            'active': True,
            'target_lang': target_lang,
            'message_count': 0,
            'started': datetime.now().isoformat()
        }
        return {'success': True, 'target_lang': target_lang}
    
    def deactivate(self, user_id):
        """Deactivate conversation mode for user"""
        user_id = str(user_id)
        if user_id in self._active_users:
            count = self._active_users[user_id].get('message_count', 0)
            del self._active_users[user_id]
            return {'success': True, 'message_count': count}
        return {'success': True, 'message_count': 0}
    
    def increment_count(self, user_id):
        """Increment message count for user"""
        user_id = str(user_id)
        if user_id in self._active_users:
            self._active_users[user_id]['message_count'] = self._active_users[user_id].get('message_count', 0) + 1

# Global instance
conversation_mode = ConversationMode()


def detect_language(text):
    """
    Detect language of text using heuristics.
    Returns: 'es' (Spanish), 'en' (English), or 'ru' (Russian)
    """
    # Russian characters
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
    
    # Spanish common words
    spanish_words = {
        'hola', 'como', 'esta', 'estas', 'que', 'donde', 'cuando', 'por', 'para', 
        'con', 'el', 'la', 'los', 'las', 'un', 'una', 'es', 'son', 'soy', 'eres',
        'tengo', 'tiene', 'quiero', 'necesito', 'puedo', 'puede', 'hay', 'aqui',
        'alli', 'bien', 'bueno', 'buena', 'gracias', 'por favor', 'si', 'no',
        'yo', 'tu', 'el', 'ella', 'nosotros', 'ellos', 'mi', 'tu', 'su',
        'cuanto', 'cuantos', 'cual', 'quien', 'porque', 'pero', 'tambien',
        'muy', 'mucho', 'poco', 'mas', 'menos', 'ahora', 'hoy', 'manana'
    }
    
    # Spanish special characters
    spanish_special = set('áéíóúüñ¿¡')
    
    text_lower = text.lower()
    
    # Check for Russian characters first
    if any(c in russian_chars for c in text):
        return 'ru'
    
    # Check for Spanish special characters
    if any(c in spanish_special for c in text_lower):
        return 'es'
    
    # Check for Spanish words
    words = text_lower.split()
    spanish_count = sum(1 for w in words if w.strip('.,!?¿¡') in spanish_words)
    
    # If significant Spanish words found
    if len(words) > 0:
        spanish_ratio = spanish_count / len(words)
        if spanish_ratio >= 0.3 or spanish_count >= 2:
            return 'es'
    
    # Default to English
    return 'en'


def get_opposite_language(lang):
    """
    Get the opposite language for translation.
    Spanish <-> English, Russian -> Spanish
    """
    if lang == 'es':
        return 'en'
    elif lang == 'en':
        return 'es'
    elif lang == 'ru':
        return 'es'  # Russian speakers usually want Spanish
    return 'es'


def get_quick_translate_prompt(source_lang, target_lang):
    """
    Get a quick translation prompt for Claude.
    Used for real-time conversation mode.
    """
    lang_names = {
        'en': 'English',
        'es': 'Spanish', 
        'ru': 'Russian'
    }
    
    source_name = lang_names.get(source_lang, 'English')
    target_name = lang_names.get(target_lang, 'Spanish')
    
    return f"""You are a real-time voice translator for a conversation.
Translate the following from {source_name} to {target_name}.

RULES:
1. Keep the translation natural and conversational
2. Just provide the translation - no explanations or alternatives
3. Preserve the tone and emotion of the original
4. If there's an important cultural nuance, add it briefly in parentheses
5. Keep it concise - this will be spoken aloud

Translate now:"""
