# EspaLuz Enhanced Brain - Integration Guide

**Version:** 1.0  
**Created:** January 10, 2026  
**Purpose:** How to integrate new modules WITHOUT modifying existing main.py

---

## 📦 New Modules Added

| Module | Purpose | Size |
|--------|---------|------|
| `espaluz_emotional_brain.py` | 50+ emotional states, expat-specific detection | ~800 lines |
| `espaluz_country_contexts.py` | 21 countries, real-life scenarios, local vocabulary | ~900 lines |

---

## ⚡ Quick Integration (Minimal Changes)

### Step 1: Add imports at TOP of main.py

```python
# === ENHANCED EMOTIONAL INTELLIGENCE (ADD THIS) ===
try:
    from espaluz_emotional_brain import (
        enhance_emotion_analysis,
        get_empathy_phrase,
        detect_user_type,
        track_activity,
        get_analytics_metrics,
        validate_org_code
    )
    from espaluz_country_contexts import (
        get_country_context,
        get_situation_phrases,
        detect_country_from_context,
        Country
    )
    ENHANCED_BRAIN_AVAILABLE = True
    print("✅ Enhanced emotional brain loaded!")
except ImportError as e:
    ENHANCED_BRAIN_AVAILABLE = False
    print(f"⚠️ Enhanced brain not available: {e}")
```

### Step 2: Enhance emotion detection in your message handler

Find your existing `detect_emotion()` call and ADD enhancement:

```python
# EXISTING CODE (keep it):
base_emotion, emotion_data = detect_emotion(user_message)

# ADD THIS after:
if ENHANCED_BRAIN_AVAILABLE:
    enhanced = enhance_emotion_analysis(user_message, str(user_id), base_emotion)
    
    # Use enhanced emotion if confidence is higher
    if enhanced['confidence'] > 0.5:
        dominant_emotion = enhanced['dominant_emotion']
        empathy_phrase = get_empathy_phrase(dominant_emotion, "en")
        
        # Add empathy to response if user is struggling
        if enhanced['requires_high_empathy']:
            # Prepend empathy phrase to AI response
            session['context']['empathy_prefix'] = empathy_phrase
    
    # Track activity for analytics
    track_activity(str(user_id))
```

### Step 3: Add country context to AI prompts

In your `generate_ai_response()` function or system prompt:

```python
if ENHANCED_BRAIN_AVAILABLE:
    # Detect country from conversation
    country = detect_country_from_context(user_message)
    if country:
        country_context = get_country_context(country)
        
        # Add to system prompt
        country_info = f"""
        User appears to be in/about: {country_context.get('name', '')}
        Local vocabulary to use: {country_context.get('local_vocabulary', {}).get('expressions', {})}
        """
        # Append to your system prompt
```

---

## 🎯 Organization Codes (For Pilots)

### Add /org command handler:

```python
@bot.message_handler(commands=['org'])
def handle_org_code(message):
    """Handle organization code entry."""
    if not ENHANCED_BRAIN_AVAILABLE:
        bot.reply_to(message, "Organization codes not available")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /org YOUR_CODE\n\nExample: /org AMCHAM_PANAMA")
        return
    
    code = parts[1].upper()
    org = validate_org_code(code)
    
    if org:
        user_id = str(message.from_user.id)
        track_activity(user_id, code)
        
        bot.reply_to(message, f"""
✅ {org['welcome_message']}

🏢 Organization: {org['name']}
📅 Trial: {org['trial_days']} days
🌎 Country: {org['country']}

Start chatting to begin learning!
        """)
    else:
        bot.reply_to(message, "❌ Invalid code. Contact your organization for the correct code.")
```

---

## 📊 Analytics Dashboard (For Guille's Metrics)

### Add /metrics command:

```python
@bot.message_handler(commands=['metrics'])
def handle_metrics(message):
    """Show analytics metrics (admin only)."""
    if not ENHANCED_BRAIN_AVAILABLE:
        return
    
    # Optional: Check if admin
    # if message.from_user.id not in ADMIN_IDS:
    #     return
    
    metrics = get_analytics_metrics()
    
    bot.reply_to(message, f"""
📊 EspaLuz Metrics

👥 Total Users: {metrics['total_users']}
📈 Weekly Active: {metrics['weekly_active_users']}
🔄 30-Day Retention: {metrics['retention_30_day']}
🏢 Organizations: {metrics['organizations_piloting']}
⭐ Testimonials: {metrics['testimonials_collected']}
🔗 Referrals: {metrics['referrals']}
    """)
```

---

## 🆘 Urgent Help Detection

The enhanced brain detects `urgency_stress` emotion. Handle it:

```python
if ENHANCED_BRAIN_AVAILABLE:
    enhanced = enhance_emotion_analysis(user_message, str(user_id))
    
    if enhanced['is_urgent']:
        # Fast-track response, skip pleasantries
        session['context']['urgent_mode'] = True
        
        # Get quick situation phrases
        situation = detect_situation(user_message)  # Your logic
        if situation:
            phrases = get_situation_phrases(situation)
            # Include in response
```

---

## 🧪 Testing the Integration

Run this to test modules work:

```bash
python espaluz_emotional_brain.py
python espaluz_country_contexts.py
```

Both should print test results without errors.

---

## 📁 File Structure After Integration

```
EspaLuzFamilybot/
├── main.py                      # YOUR EXISTING CODE (minimal changes)
├── espaluz_emotional_brain.py   # NEW: 50+ emotions, analytics
├── espaluz_country_contexts.py  # NEW: 21 countries, scenarios
├── docs/
│   ├── INTEGRATION_GUIDE.md     # This file
│   └── SWOT_ANALYSIS.md         # Strategic analysis
└── espaluz_analytics.json       # Auto-created: usage data
```

---

## ⚠️ Important Notes

1. **NO changes required to existing main.py logic** - only ADD new imports and optional enhancements
2. **Graceful fallback** - if modules fail to load, bot works as before
3. **Backward compatible** - existing features untouched
4. **Analytics auto-save** - data persists in JSON file

---

## 🚀 Next Steps

1. Test modules standalone
2. Add imports to main.py
3. Run bot and verify no errors
4. Test with real users
5. Check `/metrics` for Guille's data

---

*Created by CTO AIPA for EspaLuz upgrade*
