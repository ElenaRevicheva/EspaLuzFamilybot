"""
EspaLuz Enhanced Emotional Intelligence Brain
==============================================
Version: 2.0
Created: January 10, 2026

This module ADDS enhanced emotional intelligence to EspaLuz Telegram bot
WITHOUT modifying existing main.py functionality.

Features:
- 50+ emotional states (expat-specific, language learning, family dynamics)
- Real-life on-the-go scenarios (not just tourism)
- Bilingual Spanish↔English support
- Multi-country context awareness
- Family member detection and personalization

USAGE: Import this module in main.py and call its functions alongside existing code.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum


# =============================================================================
# EMOTIONAL STATES - 50+ expat-specific emotions
# =============================================================================

class EmotionalState(Enum):
    """50+ emotional states for expat families, travelers, and locals."""
    
    # === Basic Emotions ===
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    CALM = "calm"
    FRUSTRATED = "frustrated"
    CONTENT = "content"
    CURIOUS = "curious"
    
    # === Cultural Adaptation (Expat-specific) ===
    CULTURAL_SHOCK = "cultural_shock"
    HOMESICKNESS = "homesickness"
    INTEGRATION_ANXIETY = "integration_anxiety"
    CULTURAL_CONFUSION = "cultural_confusion"
    CULTURAL_APPRECIATION = "cultural_appreciation"
    CULTURAL_FATIGUE = "cultural_fatigue"
    BELONGING_STRUGGLE = "belonging_struggle"
    CULTURAL_BREAKTHROUGH = "cultural_breakthrough"
    
    # === Language Learning Emotions ===
    LANGUAGE_FRUSTRATION = "language_frustration"
    LANGUAGE_ANXIETY = "language_anxiety"
    LANGUAGE_EMBARRASSMENT = "language_embarrassment"
    LANGUAGE_BREAKTHROUGH = "language_breakthrough"
    LANGUAGE_CONFIDENCE = "language_confidence"
    COMMUNICATION_BARRIER = "communication_barrier"
    PRONUNCIATION_STRESS = "pronunciation_stress"
    GRAMMAR_OVERWHELM = "grammar_overwhelm"
    VOCABULARY_EXCITEMENT = "vocabulary_excitement"
    FLUENCY_PRIDE = "fluency_pride"
    
    # === Family-specific Emotions ===
    FAMILY_SEPARATION_GRIEF = "family_separation_grief"
    PARENTING_PRESSURE = "parenting_pressure"
    CHILD_ADAPTATION_WORRY = "child_adaptation_worry"
    FAMILY_UNITY_STRESS = "family_unity_stress"
    GENERATIONAL_CONFLICT = "generational_conflict"
    FAMILY_RESILIENCE = "family_resilience"
    PROTECTIVE_INSTINCT = "protective_instinct"
    FAMILY_PRIDE = "family_pride"
    
    # === Social Integration ===
    SOCIAL_ISOLATION = "social_isolation"
    FRIENDSHIP_LONGING = "friendship_longing"
    COMMUNITY_REJECTION = "community_rejection"
    SOCIAL_ACCEPTANCE = "social_acceptance"
    NETWORKING_ANXIETY = "networking_anxiety"
    SOCIAL_BREAKTHROUGH = "social_breakthrough"
    SOCIAL_CONFIDENCE = "social_confidence"
    
    # === Identity & Personal Growth ===
    IDENTITY_CRISIS = "identity_crisis"
    SELF_DOUBT = "self_doubt"
    ADAPTATION_FATIGUE = "adaptation_fatigue"
    RESILIENCE_BUILDING = "resilience_building"
    PERSONAL_GROWTH = "personal_growth"
    CONFIDENCE_BUILDING = "confidence_building"
    EMPOWERMENT = "empowerment"
    BREAKTHROUGH_MOMENT = "breakthrough_moment"
    
    # === On-the-Go Real Life Situations ===
    URGENCY_STRESS = "urgency_stress"  # Need help RIGHT NOW
    RELIEF = "relief"  # Problem solved
    OVERWHELMED = "overwhelmed"  # Too much at once
    DETERMINATION = "determination"  # Will figure it out
    GRATITUDE = "gratitude"  # Thankful for help


# =============================================================================
# EMOTIONAL CATEGORIES WITH DETAILED METADATA
# =============================================================================

EMOTIONAL_CATEGORIES = {
    "basic_emotions": {
        "description": "Universal basic emotional states",
        "emotions": ["neutral", "happy", "sad", "angry", "anxious", "excited", "frustrated", "content", "curious"],
        "support_level": "standard"
    },
    
    "cultural_adaptation": {
        "description": "Emotions related to adapting to a new culture (expat journey)",
        "emotions": ["cultural_shock", "homesickness", "integration_anxiety", "cultural_confusion", 
                    "cultural_appreciation", "cultural_fatigue", "belonging_struggle", "cultural_breakthrough"],
        "support_level": "high_empathy",
        "typical_triggers": ["first_weeks", "holidays", "family_events", "cultural_differences"]
    },
    
    "language_learning": {
        "description": "Emotions specific to learning Spanish/English",
        "emotions": ["language_frustration", "language_anxiety", "language_embarrassment", 
                    "language_breakthrough", "language_confidence", "communication_barrier",
                    "pronunciation_stress", "grammar_overwhelm", "vocabulary_excitement", "fluency_pride"],
        "support_level": "encouraging",
        "typical_triggers": ["misunderstandings", "public_speaking", "progress_moments"]
    },
    
    "family_dynamics": {
        "description": "Emotions related to family experiences during expat life",
        "emotions": ["family_separation_grief", "parenting_pressure", "child_adaptation_worry",
                    "family_unity_stress", "generational_conflict", "family_resilience",
                    "protective_instinct", "family_pride"],
        "support_level": "family_aware",
        "typical_triggers": ["school_issues", "health_concerns", "milestone_events"]
    },
    
    "social_integration": {
        "description": "Emotions related to building social connections",
        "emotions": ["social_isolation", "friendship_longing", "community_rejection",
                    "social_acceptance", "networking_anxiety", "social_breakthrough", "social_confidence"],
        "support_level": "community_building",
        "typical_triggers": ["events", "introductions", "rejections", "acceptances"]
    },
    
    "real_life_urgency": {
        "description": "Emotions during on-the-go real life situations",
        "emotions": ["urgency_stress", "relief", "overwhelmed", "determination", "gratitude"],
        "support_level": "immediate_help",
        "typical_triggers": ["emergency", "time_pressure", "unexpected_situations"]
    }
}


# =============================================================================
# EMOTION DETECTION KEYWORDS (Trilingual: English, Spanish, Russian)
# =============================================================================

EMOTION_KEYWORDS = {
    # === Cultural Adaptation ===
    "cultural_shock": {
        "en": ["culture shock", "so different", "nothing makes sense", "why do they", "back home we"],
        "es": ["choque cultural", "muy diferente", "no entiendo por qué", "en mi país"],
        "ru": ["культурный шок", "всё по-другому", "не понимаю почему", "у нас дома"]
    },
    "homesickness": {
        "en": ["miss home", "miss my family", "miss my country", "want to go back", "homesick"],
        "es": ["extraño mi país", "extraño mi familia", "quiero volver", "nostalgia"],
        "ru": ["скучаю по дому", "скучаю по семье", "хочу домой", "тоска по родине"]
    },
    
    # === Language Learning ===
    "language_frustration": {
        "en": ["don't understand", "can't say it", "too hard", "give up", "impossible"],
        "es": ["no entiendo", "no puedo decir", "muy difícil", "me rindo", "imposible"],
        "ru": ["не понимаю", "не могу сказать", "слишком сложно", "сдаюсь"]
    },
    "language_anxiety": {
        "en": ["afraid to speak", "nervous to talk", "scared of mistakes", "embarrassed"],
        "es": ["miedo de hablar", "nervioso", "tengo vergüenza", "me da pena"],
        "ru": ["боюсь говорить", "стесняюсь", "страшно ошибиться"]
    },
    "language_breakthrough": {
        "en": ["finally understood", "they understood me", "i did it", "getting better", "progress"],
        "es": ["por fin entendí", "me entendieron", "lo logré", "mejorando", "progreso"],
        "ru": ["наконец понял", "меня поняли", "получилось", "прогресс"]
    },
    
    # === Urgency/Real Life ===
    "urgency_stress": {
        "en": ["help now", "urgent", "emergency", "right now", "asap", "quickly", "hurry"],
        "es": ["ayuda ahora", "urgente", "emergencia", "ahora mismo", "rápido", "pronto"],
        "ru": ["помогите", "срочно", "сейчас", "быстро", "скорее"]
    },
    "relief": {
        "en": ["thank god", "finally", "phew", "what a relief", "solved", "figured out"],
        "es": ["gracias a dios", "por fin", "uf", "qué alivio", "resuelto"],
        "ru": ["слава богу", "наконец-то", "уф", "какое облегчение"]
    },
    
    # === Family ===
    "child_adaptation_worry": {
        "en": ["my child", "my kid", "worried about", "school problem", "doesn't fit in", "bullied"],
        "es": ["mi hijo", "mi hija", "preocupado por", "problema en la escuela", "no se adapta"],
        "ru": ["мой ребёнок", "беспокоюсь", "проблемы в школе", "не вписывается"]
    },
    "parenting_pressure": {
        "en": ["am i doing right", "good parent", "feeling guilty", "too much pressure"],
        "es": ["estoy haciendo bien", "buen padre", "me siento culpable", "mucha presión"],
        "ru": ["правильно ли я", "хороший родитель", "чувство вины", "давление"]
    },
    
    # === Social ===
    "social_isolation": {
        "en": ["lonely", "no friends", "alone", "nobody understands", "isolated"],
        "es": ["solo", "sin amigos", "nadie entiende", "aislado"],
        "ru": ["одиноко", "нет друзей", "никто не понимает", "изолирован"]
    },
    "social_breakthrough": {
        "en": ["made a friend", "invited me", "belong", "accepted", "part of"],
        "es": ["hice un amigo", "me invitaron", "pertenezco", "aceptado"],
        "ru": ["подружился", "пригласили", "принадлежу", "приняли"]
    },
    
    # === Basic emotions with trilingual support ===
    "happy": {
        "en": ["happy", "glad", "joy", "excited", "great", "wonderful", "amazing"],
        "es": ["feliz", "contento", "alegre", "emocionado", "genial", "maravilloso"],
        "ru": ["счастлив", "рад", "радость", "отлично", "замечательно", "класс"]
    },
    "sad": {
        "en": ["sad", "upset", "unhappy", "crying", "depressed", "down"],
        "es": ["triste", "deprimido", "llorando", "mal"],
        "ru": ["грустно", "печально", "плачу", "тоскливо"]
    },
    "frustrated": {
        "en": ["frustrated", "annoyed", "irritated", "fed up", "sick of"],
        "es": ["frustrado", "molesto", "irritado", "harto", "cansado de"],
        "ru": ["разочарован", "раздражён", "надоело", "достало"]
    },
    "confused": {
        "en": ["confused", "don't get it", "lost", "what", "huh"],
        "es": ["confundido", "no entiendo", "perdido", "qué"],
        "ru": ["запутался", "не понимаю", "потерялся", "что"]
    },
    "curious": {
        "en": ["curious", "wondering", "interested", "tell me", "how do"],
        "es": ["curioso", "interesado", "cuéntame", "cómo se"],
        "ru": ["любопытно", "интересно", "расскажи", "как"]
    }
}


# =============================================================================
# EMOTIONAL RESPONSE STRATEGIES
# =============================================================================

EMOTIONAL_RESPONSE_STRATEGIES = {
    "cultural_shock": {
        "tone": "validating_warm",
        "approach": "normalize_experience",
        "phrases_en": ["It's completely normal to feel this way", "Many expats experience this", "Take it one day at a time"],
        "phrases_es": ["Es completamente normal sentirse así", "Muchos expatriados pasan por esto", "Un día a la vez"],
        "teaching_style": "gentle_practical"
    },
    "homesickness": {
        "tone": "compassionate",
        "approach": "acknowledge_and_bridge",
        "phrases_en": ["I understand you miss home", "Those feelings are valid", "Let's stay connected to what matters"],
        "phrases_es": ["Entiendo que extrañas tu hogar", "Esos sentimientos son válidos"],
        "teaching_style": "comforting"
    },
    "language_frustration": {
        "tone": "encouraging_patient",
        "approach": "break_down_simplify",
        "phrases_en": ["Let's break this down", "One step at a time", "You're making progress"],
        "phrases_es": ["Vamos paso a paso", "Estás progresando"],
        "teaching_style": "simplified_supportive"
    },
    "language_anxiety": {
        "tone": "safe_supportive",
        "approach": "create_safety",
        "phrases_en": ["This is a safe space to practice", "Mistakes are how we learn", "I'm here to help, not judge"],
        "phrases_es": ["Aquí puedes practicar sin miedo", "Los errores nos enseñan"],
        "teaching_style": "low_pressure"
    },
    "language_breakthrough": {
        "tone": "celebratory",
        "approach": "reinforce_success",
        "phrases_en": ["Excellent! You did it!", "See? You're getting it!", "That was perfect!"],
        "phrases_es": ["¡Excelente!", "¿Ves? ¡Lo estás logrando!", "¡Perfecto!"],
        "teaching_style": "momentum_building"
    },
    "urgency_stress": {
        "tone": "calm_efficient",
        "approach": "immediate_help",
        "phrases_en": ["I'm here. Let's solve this.", "Quick answer:", "Here's exactly what to say:"],
        "phrases_es": ["Estoy aquí. Resolvamos esto.", "Respuesta rápida:", "Di exactamente esto:"],
        "teaching_style": "direct_actionable"
    },
    "social_isolation": {
        "tone": "warm_inclusive",
        "approach": "connection_building",
        "phrases_en": ["You're not alone in this", "Many expats feel this way", "Let's practice social phrases"],
        "phrases_es": ["No estás solo en esto", "Muchos expatriados sienten lo mismo"],
        "teaching_style": "social_skills_focus"
    },
    "child_adaptation_worry": {
        "tone": "reassuring_practical",
        "approach": "parent_support",
        "phrases_en": ["Children are resilient", "Here's what might help", "Let's practice phrases for school"],
        "phrases_es": ["Los niños son resilientes", "Esto podría ayudar"],
        "teaching_style": "family_focused"
    }
}


# =============================================================================
# ENHANCED EMOTION DETECTOR CLASS
# =============================================================================

class EnhancedEmotionDetector:
    """
    Advanced emotion detection that works alongside existing detect_emotion().
    Call this AFTER the existing detection for enhanced analysis.
    """
    
    def __init__(self):
        self.emotion_history: Dict[str, List[str]] = {}  # user_id -> list of emotions
        self.session_emotions: Dict[str, Dict] = {}  # user_id -> current session data
    
    def detect_enhanced_emotion(self, text: str, user_id: str, existing_emotion: str = None) -> Dict[str, Any]:
        """
        Enhanced emotion detection with expat-specific states.
        
        Args:
            text: User's message
            user_id: Telegram user ID
            existing_emotion: Result from existing detect_emotion() function
            
        Returns:
            Dict with enhanced emotional analysis
        """
        text_lower = text.lower()
        detected_emotions = {}
        
        # Check all emotion keywords
        for emotion, keywords_dict in EMOTION_KEYWORDS.items():
            score = 0.0
            matched_keywords = []
            
            for lang, keywords in keywords_dict.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        score += 0.3
                        matched_keywords.append(keyword)
            
            if score > 0:
                detected_emotions[emotion] = {
                    "score": min(score, 1.0),
                    "matched": matched_keywords
                }
        
        # Find dominant emotion
        if detected_emotions:
            dominant = max(detected_emotions.items(), key=lambda x: x[1]["score"])
            dominant_emotion = dominant[0]
            confidence = dominant[1]["score"]
        else:
            # Fall back to existing detection if available
            dominant_emotion = existing_emotion or "neutral"
            confidence = 0.5
        
        # Get emotional category
        category = self._get_emotion_category(dominant_emotion)
        
        # Get response strategy
        strategy = EMOTIONAL_RESPONSE_STRATEGIES.get(dominant_emotion, {
            "tone": "supportive",
            "approach": "standard",
            "teaching_style": "balanced"
        })
        
        # Track emotion history
        self._track_emotion(user_id, dominant_emotion)
        
        # Analyze progression
        progression = self._analyze_progression(user_id)
        
        return {
            "dominant_emotion": dominant_emotion,
            "confidence": confidence,
            "category": category,
            "all_detected": detected_emotions,
            "response_strategy": strategy,
            "progression": progression,
            "requires_high_empathy": category in ["cultural_adaptation", "family_dynamics", "social_integration"],
            "is_urgent": dominant_emotion == "urgency_stress"
        }
    
    def _get_emotion_category(self, emotion: str) -> str:
        """Get category for an emotion."""
        for category, data in EMOTIONAL_CATEGORIES.items():
            if emotion in data["emotions"]:
                return category
        return "basic_emotions"
    
    def _track_emotion(self, user_id: str, emotion: str):
        """Track emotion history for user."""
        if user_id not in self.emotion_history:
            self.emotion_history[user_id] = []
        
        self.emotion_history[user_id].append(emotion)
        
        # Keep only last 20 emotions
        if len(self.emotion_history[user_id]) > 20:
            self.emotion_history[user_id] = self.emotion_history[user_id][-20:]
    
    def _analyze_progression(self, user_id: str) -> str:
        """Analyze emotional progression over conversation."""
        if user_id not in self.emotion_history:
            return "new_user"
        
        history = self.emotion_history[user_id]
        if len(history) < 3:
            return "building_rapport"
        
        recent = history[-5:]
        
        positive = ["happy", "language_breakthrough", "social_breakthrough", 
                   "cultural_breakthrough", "relief", "fluency_pride", "social_confidence"]
        negative = ["language_frustration", "homesickness", "social_isolation",
                   "cultural_shock", "urgency_stress", "language_anxiety"]
        
        positive_count = sum(1 for e in recent if e in positive)
        negative_count = sum(1 for e in recent if e in negative)
        
        if positive_count > negative_count:
            return "improving"
        elif negative_count > positive_count:
            return "struggling"
        else:
            return "stable"
    
    def get_empathy_response(self, emotion: str, language: str = "en") -> str:
        """Get an empathetic response phrase for detected emotion."""
        strategy = EMOTIONAL_RESPONSE_STRATEGIES.get(emotion, {})
        
        if language == "es":
            phrases = strategy.get("phrases_es", ["Estoy aquí para ayudarte."])
        else:
            phrases = strategy.get("phrases_en", ["I'm here to help."])
        
        import random
        return random.choice(phrases) if phrases else "I'm here to help."
    
    def get_teaching_style(self, emotion: str) -> str:
        """Get recommended teaching style for emotion."""
        strategy = EMOTIONAL_RESPONSE_STRATEGIES.get(emotion, {})
        return strategy.get("teaching_style", "balanced")


# =============================================================================
# FAMILY MEMBER DETECTOR (Enhanced)
# =============================================================================

class FamilyMemberType(Enum):
    """Types of family members for personalized responses."""
    YOUNG_CHILD = "young_child"      # 3-7 years
    CHILD = "child"                  # 8-12 years
    TEENAGER = "teenager"            # 13-18 years
    YOUNG_ADULT = "young_adult"      # 19-30 years
    PARENT = "parent"                # 30-50 years
    GRANDPARENT = "grandparent"      # 50+ years
    SERVICE_PROVIDER = "service_provider"  # Locals improving English
    TRAVELER = "traveler"            # Short-term visitor
    DIGITAL_NOMAD = "digital_nomad"  # Remote worker
    UNKNOWN = "unknown"


FAMILY_MEMBER_CHARACTERISTICS = {
    FamilyMemberType.YOUNG_CHILD: {
        "language_level": "beginner",
        "attention_span": "short",
        "learning_style": "playful_visual",
        "vocabulary_focus": ["colors", "animals", "numbers", "family", "food", "greetings"],
        "response_style": "simple_fun_encouraging"
    },
    FamilyMemberType.CHILD: {
        "language_level": "elementary",
        "attention_span": "medium",
        "learning_style": "interactive_gamified",
        "vocabulary_focus": ["school", "friends", "sports", "games", "daily_activities"],
        "response_style": "encouraging_achievement_focused"
    },
    FamilyMemberType.TEENAGER: {
        "language_level": "intermediate",
        "attention_span": "variable",
        "learning_style": "relevant_practical",
        "vocabulary_focus": ["social_media", "music", "relationships", "future_plans", "slang"],
        "response_style": "respectful_not_patronizing"
    },
    FamilyMemberType.PARENT: {
        "language_level": "varied",
        "attention_span": "focused_but_busy",
        "learning_style": "practical_efficient",
        "vocabulary_focus": ["work", "parenting", "healthcare", "banking", "legal", "schools"],
        "response_style": "practical_supportive_time_efficient"
    },
    FamilyMemberType.GRANDPARENT: {
        "language_level": "beginner_to_intermediate",
        "attention_span": "patient",
        "learning_style": "traditional_thorough",
        "vocabulary_focus": ["health", "family", "culture", "daily_life", "cooking"],
        "response_style": "respectful_patient_thorough"
    },
    FamilyMemberType.SERVICE_PROVIDER: {
        "language_level": "practical_focused",
        "attention_span": "work_focused",
        "learning_style": "professional_practical",
        "vocabulary_focus": ["customer_service", "industry_specific", "small_talk", "problems"],
        "response_style": "professional_practical_quick"
    },
    FamilyMemberType.TRAVELER: {
        "language_level": "survival",
        "attention_span": "immediate_needs",
        "learning_style": "quick_practical",
        "vocabulary_focus": ["directions", "food", "transport", "emergency", "hotels"],
        "response_style": "quick_actionable"
    },
    FamilyMemberType.DIGITAL_NOMAD: {
        "language_level": "intermediate",
        "attention_span": "self_directed",
        "learning_style": "flexible_autonomous",
        "vocabulary_focus": ["coworking", "internet", "rentals", "cafes", "networking"],
        "response_style": "efficient_lifestyle_aware"
    }
}


class EnhancedFamilyDetector:
    """Detect and track family member types for personalization."""
    
    def __init__(self):
        self.user_profiles: Dict[str, FamilyMemberType] = {}
        self.user_contexts: Dict[str, Dict] = {}
    
    def detect_member_type(self, text: str, user_id: str = None) -> Dict[str, Any]:
        """Detect family member type from message patterns."""
        text_lower = text.lower()
        scores = {}
        
        # Young child indicators
        child_words = ["mama", "papa", "mommy", "daddy", "play", "toy", "cartoon", 
                      "mamá", "papá", "jugar", "juguete"]
        scores[FamilyMemberType.YOUNG_CHILD] = sum(1 for w in child_words if w in text_lower) * 0.3
        
        # Parent indicators
        parent_words = ["my child", "my kid", "my son", "my daughter", "school for", 
                       "mi hijo", "mi hija", "escuela para", "looking for schools",
                       "preschool", "kindergarten", "bilingual school"]
        scores[FamilyMemberType.PARENT] = sum(1 for w in parent_words if w in text_lower) * 0.4
        
        # Service provider indicators
        service_words = ["my customers", "my clients", "my restaurant", "my hotel",
                        "mis clientes", "mi restaurante", "better service",
                        "tourists", "expats come", "work in hospitality"]
        scores[FamilyMemberType.SERVICE_PROVIDER] = sum(1 for w in service_words if w in text_lower) * 0.4
        
        # Traveler indicators
        traveler_words = ["visiting", "on vacation", "tourist", "few days", "trip",
                         "de vacaciones", "turista", "viaje", "hotel", "airbnb"]
        scores[FamilyMemberType.TRAVELER] = sum(1 for w in traveler_words if w in text_lower) * 0.3
        
        # Digital nomad indicators
        nomad_words = ["remote work", "coworking", "wifi", "digital nomad", 
                      "trabajo remoto", "nómada digital", "coffee shop with wifi"]
        scores[FamilyMemberType.DIGITAL_NOMAD] = sum(1 for w in nomad_words if w in text_lower) * 0.4
        
        # Find best match
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1])
            if best_match[1] > 0.2:
                member_type = best_match[0]
            else:
                member_type = FamilyMemberType.UNKNOWN
        else:
            member_type = FamilyMemberType.UNKNOWN
        
        # Store if user_id provided
        if user_id:
            self.user_profiles[user_id] = member_type
        
        characteristics = FAMILY_MEMBER_CHARACTERISTICS.get(member_type, {})
        
        return {
            "detected_type": member_type,
            "characteristics": characteristics,
            "scores": {k.value: v for k, v in scores.items()},
            "response_style": characteristics.get("response_style", "balanced"),
            "vocabulary_focus": characteristics.get("vocabulary_focus", [])
        }
    
    def get_user_type(self, user_id: str) -> FamilyMemberType:
        """Get stored user type."""
        return self.user_profiles.get(user_id, FamilyMemberType.UNKNOWN)
    
    def set_user_type(self, user_id: str, member_type: FamilyMemberType):
        """Manually set user type."""
        self.user_profiles[user_id] = member_type


# =============================================================================
# USAGE ANALYTICS TRACKER
# =============================================================================

class UsageAnalytics:
    """Track usage analytics for Guille's metrics."""
    
    def __init__(self, data_file: str = "espaluz_analytics.json"):
        self.data_file = data_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load analytics data from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "users": {},
            "daily_active": {},
            "weekly_active": {},
            "organizations": {},
            "testimonials": [],
            "referrals": {}
        }
    
    def _save_data(self):
        """Save analytics data to file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving analytics: {e}")
    
    def track_user_activity(self, user_id: str, org_code: str = None):
        """Track user activity for retention metrics."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize user if new
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "first_seen": today,
                "last_seen": today,
                "total_messages": 0,
                "org_code": org_code,
                "days_active": []
            }
        
        # Update user
        user = self.data["users"][user_id]
        user["last_seen"] = today
        user["total_messages"] += 1
        if org_code:
            user["org_code"] = org_code
        if today not in user["days_active"]:
            user["days_active"].append(today)
        
        # Track daily active
        if today not in self.data["daily_active"]:
            self.data["daily_active"][today] = []
        if user_id not in self.data["daily_active"][today]:
            self.data["daily_active"][today].append(user_id)
        
        self._save_data()
    
    def get_metrics(self) -> Dict:
        """Get Guille's required metrics."""
        today = datetime.now()
        
        # Calculate 30-day retention
        thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        users_30_days = []
        for user_id, user_data in self.data["users"].items():
            if user_data["first_seen"] <= thirty_days_ago:
                # User was here 30+ days ago
                recent_activity = [d for d in user_data["days_active"] 
                                 if d >= thirty_days_ago]
                if len(recent_activity) > 0:
                    users_30_days.append(user_id)
        
        total_old_users = len([u for u, d in self.data["users"].items() 
                              if d["first_seen"] <= thirty_days_ago])
        retention_30 = (len(users_30_days) / total_old_users * 100) if total_old_users > 0 else 0
        
        # Weekly active users
        seven_days_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        weekly_active = set()
        for date, users in self.data["daily_active"].items():
            if date >= seven_days_ago:
                weekly_active.update(users)
        
        return {
            "total_users": len(self.data["users"]),
            "weekly_active_users": len(weekly_active),
            "retention_30_day": f"{retention_30:.1f}%",
            "organizations_piloting": len(set(u.get("org_code") for u in self.data["users"].values() if u.get("org_code"))),
            "testimonials_collected": len(self.data["testimonials"]),
            "referrals": len(self.data["referrals"])
        }
    
    def add_testimonial(self, user_id: str, text: str, rating: int = 5):
        """Add user testimonial."""
        self.data["testimonials"].append({
            "user_id": user_id,
            "text": text,
            "rating": rating,
            "date": datetime.now().isoformat()
        })
        self._save_data()
    
    def track_referral(self, referrer_id: str, referred_id: str):
        """Track referral."""
        if referrer_id not in self.data["referrals"]:
            self.data["referrals"][referrer_id] = []
        self.data["referrals"][referrer_id].append({
            "referred_id": referred_id,
            "date": datetime.now().isoformat()
        })
        self._save_data()


# =============================================================================
# ORGANIZATION CODES SYSTEM
# =============================================================================

ORGANIZATION_CODES = {
    # Panama Organizations
    "AMCHAM_PANAMA": {
        "name": "American Chamber of Commerce Panama",
        "trial_days": 60,
        "welcome_message": "Welcome, AmCham Panama member! Extended 60-day trial activated.",
        "country": "Panama"
    },
    "ISP_PARENTS": {
        "name": "International School of Panama PTA",
        "trial_days": 60,
        "welcome_message": "Welcome, ISP family! 60-day trial for your whole family.",
        "country": "Panama"
    },
    "ISD_MEMBERS": {
        "name": "Innovation Smart District Panama",
        "trial_days": 90,
        "welcome_message": "Welcome, ISD innovator! Special 90-day trial activated.",
        "country": "Panama"
    },
    "SELINA_NOMADS": {
        "name": "Selina Coworking Panama",
        "trial_days": 45,
        "welcome_message": "Welcome, digital nomad! 45-day trial for Selina members.",
        "country": "Panama"
    },
    "OXFORD_PARENTS": {
        "name": "Oxford International School Panama",
        "trial_days": 60,
        "welcome_message": "Welcome, Oxford family!",
        "country": "Panama"
    },
    "BALBOA_PARENTS": {
        "name": "Balboa Academy Panama",
        "trial_days": 60,
        "welcome_message": "Welcome, Balboa Academy family!",
        "country": "Panama"
    },
    # Demo/Test codes
    "DEMO_2026": {
        "name": "Demo/Workshop Access",
        "trial_days": 14,
        "welcome_message": "Demo mode activated!",
        "country": "Demo"
    }
}


def validate_org_code(code: str) -> Optional[Dict]:
    """Validate organization code and return org info."""
    code_upper = code.upper().strip()
    return ORGANIZATION_CODES.get(code_upper)


# =============================================================================
# SINGLETON INSTANCES (for easy import)
# =============================================================================

# Create singleton instances
emotion_detector = EnhancedEmotionDetector()
family_detector = EnhancedFamilyDetector()
analytics = UsageAnalytics()


# =============================================================================
# HELPER FUNCTIONS FOR INTEGRATION
# =============================================================================

def enhance_emotion_analysis(text: str, user_id: str, existing_emotion: str = None) -> Dict:
    """
    Main function to call from main.py for enhanced emotion analysis.
    
    Usage in main.py:
        from espaluz_emotional_brain import enhance_emotion_analysis
        
        # In your message handler:
        enhanced = enhance_emotion_analysis(user_message, user_id, basic_emotion)
    """
    return emotion_detector.detect_enhanced_emotion(text, user_id, existing_emotion)


def get_empathy_phrase(emotion: str, language: str = "en") -> str:
    """Get empathetic response phrase for emotion."""
    return emotion_detector.get_empathy_response(emotion, language)


def detect_user_type(text: str, user_id: str = None) -> Dict:
    """Detect family member type from message."""
    return family_detector.detect_member_type(text, user_id)


def track_activity(user_id: str, org_code: str = None):
    """Track user activity for analytics."""
    analytics.track_user_activity(user_id, org_code)


def get_analytics_metrics() -> Dict:
    """Get current analytics metrics."""
    return analytics.get_metrics()


# =============================================================================
# TEST FUNCTION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 EspaLuz Enhanced Emotional Brain - Test")
    print("=" * 60)
    
    # Test emotion detection
    test_messages = [
        ("I miss my family so much, being here alone is hard", "homesickness"),
        ("Help! I need to explain my allergy at a restaurant NOW", "urgency_stress"),
        ("My daughter is struggling at her new school", "child_adaptation_worry"),
        ("I finally understood the waiter! He said 'buen provecho'!", "language_breakthrough"),
        ("Nobody here understands me when I try to speak Spanish", "language_frustration")
    ]
    
    print("\n🔍 Testing Emotion Detection:")
    for message, expected in test_messages:
        result = enhance_emotion_analysis(message, "test_user")
        print(f"\nMessage: '{message[:50]}...'")
        print(f"  Expected: {expected}")
        print(f"  Detected: {result['dominant_emotion']} (confidence: {result['confidence']:.2f})")
        print(f"  Category: {result['category']}")
        print(f"  Empathy phrase: {get_empathy_phrase(result['dominant_emotion'])}")
    
    # Test family member detection
    print("\n\n👥 Testing Family Member Detection:")
    family_messages = [
        "I'm looking for good preschools for my 4-year-old",
        "My customers are mostly American tourists",
        "I work remotely and need good wifi for my coworking"
    ]
    
    for message in family_messages:
        result = detect_user_type(message)
        print(f"\nMessage: '{message}'")
        print(f"  Detected: {result['detected_type'].value}")
        print(f"  Response style: {result['response_style']}")
    
    # Test org codes
    print("\n\n🏢 Testing Organization Codes:")
    for code in ["AMCHAM_PANAMA", "ISD_MEMBERS", "INVALID_CODE"]:
        org = validate_org_code(code)
        if org:
            print(f"  {code}: ✅ {org['name']} ({org['trial_days']} days)")
        else:
            print(f"  {code}: ❌ Invalid")
    
    print("\n✅ All tests completed!")
