"""
EspaLuz Neural TTS Module
========================
High-quality Microsoft Edge neural voices for all bot responses.

Voices:
- Spanish (MX): es-MX-DaliaNeural (warm, clear female)
- Spanish (ES): es-ES-ElviraNeural (European Spanish)
- English (US): en-US-JennyNeural (friendly, natural)
- English (UK): en-GB-SoniaNeural (British accent)
- Russian: ru-RU-SvetlanaNeural (native Russian)

Usage:
    from espaluz_neural_tts import generate_voice, generate_voice_sync
    
    # Async (preferred for speed)
    audio_path = await generate_voice("Hola, ¿cómo estás?", lang="es")
    
    # Sync (for compatibility with existing code)
    audio_path = generate_voice_sync("Hello, how are you?", lang="en")
"""

import asyncio
import os
import subprocess
from typing import Optional
import logging

# Try edge-tts, fall back to gTTS
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("edge-tts not available, falling back to gTTS")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


# =============================================================================
# VOICE CONFIGURATION - Beautiful Neural Voices
# =============================================================================

NEURAL_VOICES = {
    # Spanish voices
    "es": "es-MX-DaliaNeural",        # Mexican Spanish - warm, clear
    "es-mx": "es-MX-DaliaNeural",     # Mexican Spanish
    "es-es": "es-ES-ElviraNeural",    # European Spanish  
    "es-co": "es-CO-SalomeNeural",    # Colombian Spanish
    "es-ar": "es-AR-ElenaNeural",     # Argentine Spanish
    
    # English voices
    "en": "en-US-JennyNeural",        # American English - friendly
    "en-us": "en-US-JennyNeural",     # American English
    "en-gb": "en-GB-SoniaNeural",     # British English
    "en-au": "en-AU-NatashaNeural",   # Australian English
    
    # Russian voice
    "ru": "ru-RU-SvetlanaNeural",     # Russian - native
    
    # Portuguese (for Brazil expats)
    "pt": "pt-BR-FranciscaNeural",    # Brazilian Portuguese
}

# Voice settings for different contexts
VOICE_STYLES = {
    "tutor": {
        "rate": "+0%",      # Normal speed for learning
        "pitch": "+0Hz",
    },
    "conversation": {
        "rate": "+10%",     # Slightly faster for real-time
        "pitch": "+0Hz",
    },
    "slow": {
        "rate": "-20%",     # Slower for beginners
        "pitch": "+0Hz",
    },
    "excited": {
        "rate": "+5%",
        "pitch": "+5Hz",
    }
}


# =============================================================================
# ASYNC TTS GENERATION (Preferred - Fast)
# =============================================================================

async def generate_voice(
    text: str,
    lang: str = "es",
    style: str = "tutor",
    output_format: str = "mp3",
    message_id: Optional[int] = None
) -> Optional[str]:
    """
    Generate high-quality neural voice audio.
    
    Args:
        text: Text to speak
        lang: Language code (es, en, ru, etc.)
        style: Voice style (tutor, conversation, slow, excited)
        output_format: Output format (mp3 or ogg)
        message_id: Optional message ID for unique filename
        
    Returns:
        Path to generated audio file, or None if failed
    """
    if not EDGE_TTS_AVAILABLE:
        return generate_voice_gtts_fallback(text, lang, message_id)
    
    try:
        # Get voice for language
        voice = NEURAL_VOICES.get(lang.lower(), NEURAL_VOICES["es"])
        
        # Get style settings
        settings = VOICE_STYLES.get(style, VOICE_STYLES["tutor"])
        rate = settings["rate"]
        pitch = settings["pitch"]
        
        # Generate unique filename
        file_id = message_id or hash(text) % 100000
        output_path = f"neural_tts_{file_id}.{output_format}"
        
        # Generate with edge-tts
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        
        await communicate.save(output_path)
        
        # Convert to OGG if needed for Telegram voice notes
        if output_format == "ogg":
            ogg_path = output_path
        else:
            ogg_path = f"neural_tts_{file_id}.ogg"
            # Convert MP3 to OGG opus for Telegram
            subprocess.run([
                "ffmpeg", "-y", "-i", output_path,
                "-c:a", "libopus", "-b:a", "64k",
                ogg_path
            ], capture_output=True)
            # Clean up MP3
            if os.path.exists(output_path) and output_path != ogg_path:
                os.remove(output_path)
            output_path = ogg_path
        
        return output_path
        
    except Exception as e:
        logging.error(f"Neural TTS error: {e}")
        # Fall back to gTTS
        return generate_voice_gtts_fallback(text, lang, message_id)


# =============================================================================
# SYNC TTS GENERATION (For compatibility with existing code)
# =============================================================================

def generate_voice_sync(
    text: str,
    lang: str = "es",
    style: str = "tutor",
    output_format: str = "mp3",
    message_id: Optional[int] = None
) -> Optional[str]:
    """
    Synchronous wrapper for generate_voice.
    Use this in existing code that isn't async.
    """
    try:
        # Create new event loop if none exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If we're already in an async context, use run_coroutine_threadsafe
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(
                generate_voice(text, lang, style, output_format, message_id),
                loop
            )
            return future.result(timeout=30)
        else:
            # Run directly
            return loop.run_until_complete(
                generate_voice(text, lang, style, output_format, message_id)
            )
    except Exception as e:
        logging.error(f"Sync TTS wrapper error: {e}")
        return generate_voice_gtts_fallback(text, lang, message_id)


# =============================================================================
# GTTS FALLBACK (If edge-tts fails)
# =============================================================================

def generate_voice_gtts_fallback(
    text: str,
    lang: str = "es",
    message_id: Optional[int] = None
) -> Optional[str]:
    """Fallback to gTTS if edge-tts is unavailable"""
    if not GTTS_AVAILABLE:
        logging.error("Neither edge-tts nor gTTS available!")
        return None
    
    try:
        # Map language codes
        gtts_lang = {
            "es": "es",
            "es-mx": "es",
            "es-es": "es",
            "en": "en",
            "en-us": "en",
            "en-gb": "en",
            "ru": "ru",
            "pt": "pt"
        }.get(lang.lower(), "es")
        
        file_id = message_id or hash(text) % 100000
        output_path = f"gtts_fallback_{file_id}.mp3"
        
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(output_path)
        
        return output_path
        
    except Exception as e:
        logging.error(f"gTTS fallback error: {e}")
        return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_voice_for_country(country_code: str) -> str:
    """Get the best voice for a specific country"""
    country_voices = {
        "panama": "es-MX-DaliaNeural",      # Use Mexican (closest)
        "mexico": "es-MX-DaliaNeural",
        "colombia": "es-CO-SalomeNeural",
        "argentina": "es-AR-ElenaNeural",
        "spain": "es-ES-ElviraNeural",
        "costa_rica": "es-MX-DaliaNeural",  # Use Mexican
        "peru": "es-MX-DaliaNeural",        # Use Mexican (neutral)
        "chile": "es-MX-DaliaNeural",       # Chilean accent not available
        "usa": "en-US-JennyNeural",
        "uk": "en-GB-SoniaNeural",
        "australia": "en-AU-NatashaNeural",
        "russia": "ru-RU-SvetlanaNeural",
        "brazil": "pt-BR-FranciscaNeural",
    }
    return country_voices.get(country_code.lower(), NEURAL_VOICES["es"])


def list_available_voices():
    """List all available neural voices (for debugging)"""
    return NEURAL_VOICES


def cleanup_audio_files(prefix: str = "neural_tts_"):
    """Clean up old audio files"""
    import glob
    for f in glob.glob(f"{prefix}*"):
        try:
            os.remove(f)
        except:
            pass


# =============================================================================
# QUICK TEST
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing Neural TTS...")
        
        # Test Spanish
        path = await generate_voice("Hola, ¿cómo estás hoy?", lang="es")
        print(f"Spanish: {path}")
        
        # Test English
        path = await generate_voice("Hello, how are you today?", lang="en")
        print(f"English: {path}")
        
        # Test conversation mode (faster)
        path = await generate_voice("¿Dónde está la farmacia?", lang="es", style="conversation")
        print(f"Conversation: {path}")
        
        print("Done!")
    
    asyncio.run(test())
