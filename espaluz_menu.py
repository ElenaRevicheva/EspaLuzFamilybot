"""
EspaLuz Enhanced Menu System
============================
Version: 1.0
Created: January 10, 2026

Comprehensive menu with all commands + new enhanced features.
Copy the MENU_TEXT to your /start and /help handlers.
Add the new command handlers to your main.py.
"""

# =============================================================================
# COMPLETE MENU TEXT (Copy to /start and /help)
# =============================================================================

MENU_TEXT = """
🌟 *EspaLuz — Your AI Bilingual Companion* 🇪🇸🇬🇧

Welcome! I'm your emotionally intelligent language tutor for expat families, travelers, and locals improving their English.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 *GETTING STARTED*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/start — Begin your journey
  ↳ Shows this welcome menu

/profile — Set up your learning profile
  ↳ Tell me your name, role (parent/child/traveler), and age
  ↳ Example: /family Sofia mother 38

/reset — Start fresh
  ↳ Clears conversation history

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 *HOW TO LEARN*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Just send me any message! I understand:
• 💬 *Text* — in English, Spanish, or Russian
• 🎤 *Voice* — speak naturally, I'll transcribe and help
• 📸 *Photos* — of menus, signs, documents — I'll translate!

*Examples to try:*
• "How do I say 'I need a doctor' in Spanish?"
• "Necesito ayuda con el banco" (I'll explain in English)
• "Как сказать 'спасибо' по-испански?" (Russian works too!)
• Send a photo of a restaurant menu 📷

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 *TRACK YOUR PROGRESS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/progress — See your learning stats
  ↳ Words learned, grammar points, sessions

/review — Practice words you've learned
  ↳ Spaced repetition to remember vocabulary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆘 *REAL-LIFE HELP (NEW!)*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/help_banking — How to say things at the bank
  ↳ Open account, transfer, ATM problems

/help_medical — Healthcare phrases
  ↳ Doctor, pharmacy, allergies, emergencies

/help_school — School-related vocabulary
  ↳ Enrollment, teacher meetings, homework

/help_shopping — Shopping and supermarket
  ↳ Prices, finding items, payment

/help_transport — Getting around
  ↳ Taxi, bus, directions, Uber

/help_emergency — 🚨 Urgent help phrases
  ↳ Police, ambulance, "I need help now"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌎 *COUNTRY & CULTURE (NEW!)*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/country — Set your country context
  ↳ Example: /country panama
  ↳ I'll use local vocabulary and phrases!

/slang — Learn local expressions
  ↳ Chuleta, vaina, pura vida, etc.

/culture — Cultural tips for your country
  ↳ Tipping, formality, time expectations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 *ORGANIZATIONS (For Pilots)*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/org CODE — Enter your organization code
  ↳ Example: /org AMCHAM_PANAMA
  ↳ Get extended trial and special features

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ *FEEDBACK & SUPPORT*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/feedback — Share your experience
  ↳ Help us improve (and collect testimonials!)

/refer — Get your referral link
  ↳ Give 1 month free, get 1 month free

/metrics — See community stats (admin)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 *SUBSCRIPTION & TRIAL*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/trial — Check your trial status
  ↳ 14-day free trial for new users

/pagar — Pay with PagueloFacil (Panama)
  ↳ $11 one-time → 30 days (Visa, MC, PagoCash)
  ↳ No extra step — access unlocks automatically after payment

/subscribe — View subscription options
  ↳ PayPal monthly or PagueloFacil /pagar

/link — Link PayPal subscription only (I-XXXX)
  ↳ Not for PagueloFacil — PF users just pay via /pagar

/connect CODE — Connect to web dashboard
  ↳ Sync your progress across devices

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎙️ *CONVERSATION MODE (NEW!)*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/convo on — Start real-time voice translation
  ↳ Like Google Translate conversation mode!

/convo off — Return to normal tutor mode
/convo es — Translate TO Spanish
/convo en — Translate TO English

*How it works:*
• 🇬🇧 Speak English → Spanish voice reply
• 🇪🇸 Speak Spanish → English voice reply
• 🇷🇺 Speak Russian → Spanish voice reply

Perfect for: pharmacy, doctor, shopping!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 *DEMO MODE (For Workshops)*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/demo — Toggle demo presentation mode
  ↳ Shows emotional intelligence in action

/scenarios — View demo scenarios
  ↳ Pre-written demos for presenters

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 *ALL COMMANDS QUICK REFERENCE*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Setup:* /start /profile /family /reset
*Learn:* Just chat! Voice & photos work too
*Progress:* /progress /review
*Help:* /help_banking /help_medical /help_school
        /help_shopping /help_transport /help_emergency
*Culture:* /country /slang /culture  
*Orgs:* /org /feedback /refer
*Account:* /trial /pagar /subscribe /link /connect
*Convo:* /convo on /convo off /convo es /convo en
*Demo:* /demo /scenarios

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 *PRO TIPS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. *Set your profile first* — I adapt to your role
2. *Use voice messages* — Great for pronunciation
3. *Send photos of text* — Menus, signs, documents
4. *Ask "how do I say..."* — I give natural phrases
5. *Type in any language* — I understand all three!

¡Empecemos! / Let's begin! 🚀
Just send me your first message...
"""

# =============================================================================
# SHORT WELCOME (for /start - first time users)
# =============================================================================

WELCOME_SHORT = """
👋 *¡Hola! Welcome to EspaLuz!*

I'm your AI bilingual tutor for expat families, travelers, and locals.

🎯 *Quick Start:*
1. Set your profile: /profile
2. Just send any message to learn!
3. Send voice or photos too!

💬 Try saying: "How do I say 'thank you' in Spanish?"

/help — See all commands
"""

# =============================================================================
# HELP TEXTS FOR SPECIFIC SITUATIONS
# =============================================================================

HELP_BANKING = """
🏦 *BANKING PHRASES / FRASES BANCARIAS*

*Opening an account:*
🇪🇸 "Quiero abrir una cuenta"
🇬🇧 "I want to open an account"

*Making a transfer:*
🇪🇸 "Necesito hacer una transferencia"
🇬🇧 "I need to make a transfer"

*ATM problems:*
🇪🇸 "El cajero se tragó mi tarjeta"
🇬🇧 "The ATM ate my card"

*Exchange rate:*
🇪🇸 "¿Cuál es la tasa de cambio?"
🇬🇧 "What's the exchange rate?"

*Bank statement:*
🇪🇸 "Necesito un estado de cuenta"
🇬🇧 "I need a bank statement"

💡 *Tip:* Bring your passport/cédula + proof of address!
"""

HELP_MEDICAL = """
🏥 *HEALTHCARE PHRASES / FRASES MÉDICAS*

*Emergency:*
🇪🇸 "¡Es una emergencia!"
🇬🇧 "It's an emergency!"
📞 Emergency: 911

*I'm allergic:*
🇪🇸 "Soy alérgico/a a..."
🇬🇧 "I'm allergic to..."

*It hurts here:*
🇪🇸 "Me duele aquí" (point)
🇬🇧 "It hurts here"

*I need a doctor:*
🇪🇸 "Necesito ver a un doctor"
🇬🇧 "I need to see a doctor"

*Pharmacy:*
🇪🇸 "¿Tienen esta medicina?"
🇬🇧 "Do you have this medicine?"

*Prescription:*
🇪🇸 "Necesito una receta"
🇬🇧 "I need a prescription"

💡 *Tip:* Keep your insurance card and ID handy!
"""

HELP_SCHOOL = """
🏫 *SCHOOL PHRASES / FRASES ESCOLARES*

*Enrollment:*
🇪🇸 "Quiero inscribir a mi hijo/a"
🇬🇧 "I want to enroll my child"

*Meeting with teacher:*
🇪🇸 "Tengo reunión con el/la maestro/a"
🇬🇧 "I have a meeting with the teacher"

*My child has homework:*
🇪🇸 "Mi hijo/a tiene tarea"
🇬🇧 "My child has homework"

*Where to buy uniform:*
🇪🇸 "¿Dónde compro el uniforme?"
🇬🇧 "Where do I buy the uniform?"

*Report card:*
🇪🇸 "¿Cuándo entregan las calificaciones?"
🇬🇧 "When do you give report cards?"

*My child is sick today:*
🇪🇸 "Mi hijo/a está enfermo/a hoy"
🇬🇧 "My child is sick today"

💡 *Tip:* Save your school's contact in your phone!
"""

HELP_SHOPPING = """
🛒 *SHOPPING PHRASES / FRASES DE COMPRAS*

*How much?:*
🇪🇸 "¿Cuánto cuesta esto?"
🇬🇧 "How much is this?"

*Where do I find...?:*
🇪🇸 "¿Dónde encuentro...?"
🇬🇧 "Where do I find...?"

*Do you have another size?:*
🇪🇸 "¿Tienen en otra talla?"
🇬🇧 "Do you have in another size?"

*Do you accept cards?:*
🇪🇸 "¿Aceptan tarjeta?"
🇬🇧 "Do you accept cards?"

*Do you have a discount?:*
🇪🇸 "¿Tienen descuento?"
🇬🇧 "Do you have a discount?"

*I'm just looking:*
🇪🇸 "Solo estoy mirando"
🇬🇧 "I'm just looking"

💡 *Tip:* "¿Me regala una bolsa?" = "Can you give me a bag?"
"""

HELP_TRANSPORT = """
🚗 *TRANSPORT PHRASES / FRASES DE TRANSPORTE*

*Taxi/Uber:*
🇪🇸 "¿Cuánto cuesta ir a...?"
🇬🇧 "How much to go to...?"

*Bus:*
🇪🇸 "¿Este bus va a...?"
🇬🇧 "Does this bus go to...?"

*Where is...?:*
🇪🇸 "¿Dónde está...?"
🇬🇧 "Where is...?"

*Stop here!:*
🇪🇸 "¡Pare aquí, por favor!"
🇬🇧 "Stop here, please!"

*I'm going to...:*
🇪🇸 "Voy a..."
🇬🇧 "I'm going to..."

*Keep the change:*
🇪🇸 "Quédese con el cambio"
🇬🇧 "Keep the change"

💡 *Tip:* Use inDriver or Uber for clear pricing!
"""

HELP_EMERGENCY = """
🚨 *EMERGENCY PHRASES / FRASES DE EMERGENCIA*

*HELP!:*
🇪🇸 "¡AYUDA!"
🇬🇧 "HELP!"

*Call the police!:*
🇪🇸 "¡Llame a la policía!"
🇬🇧 "Call the police!"
📞 Police: 911

*I need an ambulance:*
🇪🇸 "Necesito una ambulancia"
🇬🇧 "I need an ambulance"
📞 Emergency: 911

*There was an accident:*
🇪🇸 "Hubo un accidente"
🇬🇧 "There was an accident"

*I'm lost:*
🇪🇸 "Estoy perdido/a"
🇬🇧 "I'm lost"

*I don't understand:*
🇪🇸 "No entiendo"
🇬🇧 "I don't understand"

*Please speak slowly:*
🇪🇸 "Por favor, hable más despacio"
🇬🇧 "Please speak more slowly"

💡 *Remember:* 911 works in most Latin American countries!
"""

# =============================================================================
# TESTIMONIAL PROMPTS
# =============================================================================

TESTIMONIAL_7_DAY = """
💬 *Quick check-in!*

You've been using EspaLuz for a week now! 🎉

How's your experience so far? I'd love to hear:
• What's working well?
• What could be better?
• Any breakthrough moments?

Just reply naturally — your feedback helps me improve for all expat families!
"""

TESTIMONIAL_30_DAY = """
🌟 *Congratulations on 30 days with EspaLuz!*

You're making real progress! 📈

Would you be willing to share a quick testimonial about your experience? 

It helps other expat families discover EspaLuz.

Reply with:
• ⭐ Your rating (1-5)
• 💬 A short sentence about your experience
• ✅ "Yes, you can share" or "Keep anonymous"

Example:
"5 ⭐ EspaLuz helped my whole family adapt to Panama. Finally a tutor that understands expat stress! ✅ Share"

Thank you for being part of our community! 🙏
"""

# =============================================================================
# COUNTRY SLANG QUICK REFERENCES
# =============================================================================

SLANG_PANAMA = """
🇵🇦 *PANAMANIAN SPANISH SLANG*

*Greetings:*
• ¿Qué xopá? = What's up?
• Buenas = Hello (any time)
• ¿Qué es lo que hay? = What's going on?

*Expressions:*
• Chuleta = Darn! / Wow!
• Vaina = Thing / stuff (universal word)
• Juega vivo = Be smart / Don't get scammed
• Quedó pelao = Ran out of money
• Yeye = Trendy / fancy

*Useful:*
• ¿Me regalas...? = Can you give me...? (polite)
• Frío como hielo = Very cold (for drinks)
• Dame chance = Give me a moment

💡 Use "usted" with strangers, "tú" with friends!
"""

SLANG_MEXICO = """
🇲🇽 *MEXICAN SPANISH SLANG*

*Greetings:*
• ¿Qué onda? = What's up?
• ¿Mande? = Pardon? / What?
• Órale = Okay / Let's go / Wow

*Expressions:*
• Chido / Padre = Cool / great
• Neta = Really / truth
• Güey = Dude (informal)
• No manches = No way!
• Ahorita = Right now (but could be later!)

*Useful:*
• Chamba = Work / job
• Fresa = Preppy person
• Un chingo = A lot (vulgar)

💡 Mexicans use titles: Licenciado, Ingeniero, Doctor
"""

SLANG_COLOMBIA = """
🇨🇴 *COLOMBIAN SPANISH SLANG*

*Greetings:*
• ¿Quiubo? = What's up?
• Parcero/Parce = Buddy/friend

*Expressions:*
• Bacano = Cool/great
• Berraco = Awesome / tough person
• De una = Right away / Let's do it
• A la orden = At your service
• Sumercé = Formal "you" (Bogotá)

*Useful:*
• Tinto = Small black coffee
• Rumbear = To party
• Chimba = Cool (can be vulgar)

💡 Different regions have different accents:
Paisas (Medellín), Costeños (Coast), Rolos (Bogotá)
"""

SLANG_ARGENTINA = """
🇦🇷 *ARGENTINE SPANISH SLANG*

*Greetings:*
• ¿Qué onda? = What's up?
• Che = Hey (like "dude")

*IMPORTANT - Voseo:*
• tú eres → vos sos
• tú tienes → vos tenés
• tú puedes → vos podés

*Expressions:*
• Boludo = Dude/idiot (context matters!)
• Bárbaro = Great/awesome
• Laburo = Work
• Morfar = To eat
• Bondi = Bus
• Mango = Money

💡 Sharing mate is a social ritual — learn the etiquette!
💡 Dinner starts LATE (9-11 PM)
"""

SLANG_COSTA_RICA = """
🇨🇷 *COSTA RICAN SPANISH SLANG*

*The Essential:*
• Pura vida = Pure life (greeting, goodbye, everything!)

*Expressions:*
• Mae = Dude
• Tuanis = Cool
• Tico/Tica = Costa Rican person
• Chunche = Thing/stuff
• Brete = Work
• La vara = The thing/situation

💡 "Pura vida" is not just words — it's the laid-back lifestyle!
💡 Very eco-conscious country
"""

# =============================================================================
# REFERRAL SYSTEM
# =============================================================================

REFERRAL_MESSAGE = """
🔗 *Share EspaLuz with Friends!*

Your personal referral link:
👉 espaluz.bot.link/{user_id}

*How it works:*
1. Share your link with friends
2. When they subscribe, you BOTH get 1 month FREE
3. No limit on referrals!

*Your referral stats:*
• Friends referred: {referral_count}
• Free months earned: {free_months}

Thank you for spreading the word! 🙏
"""

# =============================================================================
# DEMO MODE (for workshops)
# =============================================================================

DEMO_MODE_INTRO = """
🎭 *DEMO MODE ACTIVATED*

Perfect for workshops and presentations!

In demo mode:
• Responses are formatted for display
• Key features are highlighted
• Emotional intelligence is explained

Type any message to see EspaLuz in action!

To exit: /demo_off
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_menu():
    """Return the full menu text."""
    return MENU_TEXT

def get_welcome():
    """Return short welcome for new users."""
    return WELCOME_SHORT

def get_help_text(category: str) -> str:
    """Get help text for a specific category."""
    help_texts = {
        "banking": HELP_BANKING,
        "medical": HELP_MEDICAL,
        "school": HELP_SCHOOL,
        "shopping": HELP_SHOPPING,
        "transport": HELP_TRANSPORT,
        "emergency": HELP_EMERGENCY
    }
    return help_texts.get(category, "Category not found. Try: banking, medical, school, shopping, transport, emergency")

def get_slang(country: str) -> str:
    """Get slang for a specific country."""
    slang_texts = {
        "panama": SLANG_PANAMA,
        "mexico": SLANG_MEXICO,
        "colombia": SLANG_COLOMBIA,
        "argentina": SLANG_ARGENTINA,
        "costa_rica": SLANG_COSTA_RICA,
        "costarica": SLANG_COSTA_RICA
    }
    return slang_texts.get(country.lower(), f"Slang not available for {country}. Try: panama, mexico, colombia, argentina, costa_rica")

def get_testimonial_prompt(days: int) -> str:
    """Get testimonial prompt based on days active."""
    if days == 7:
        return TESTIMONIAL_7_DAY
    elif days >= 30:
        return TESTIMONIAL_30_DAY
    return ""


# =============================================================================
# COMMAND HANDLERS TO ADD TO main.py
# =============================================================================

"""
Copy these handlers to your main.py:

# === NEW COMMAND HANDLERS (Add to main.py) ===

@bot.message_handler(commands=["help_banking"])
def handle_help_banking(message):
    from espaluz_menu import HELP_BANKING
    bot.reply_to(message, HELP_BANKING, parse_mode="Markdown")

@bot.message_handler(commands=["help_medical"])
def handle_help_medical(message):
    from espaluz_menu import HELP_MEDICAL
    bot.reply_to(message, HELP_MEDICAL, parse_mode="Markdown")

@bot.message_handler(commands=["help_school"])
def handle_help_school(message):
    from espaluz_menu import HELP_SCHOOL
    bot.reply_to(message, HELP_SCHOOL, parse_mode="Markdown")

@bot.message_handler(commands=["help_shopping"])
def handle_help_shopping(message):
    from espaluz_menu import HELP_SHOPPING
    bot.reply_to(message, HELP_SHOPPING, parse_mode="Markdown")

@bot.message_handler(commands=["help_transport"])
def handle_help_transport(message):
    from espaluz_menu import HELP_TRANSPORT
    bot.reply_to(message, HELP_TRANSPORT, parse_mode="Markdown")

@bot.message_handler(commands=["help_emergency"])
def handle_help_emergency(message):
    from espaluz_menu import HELP_EMERGENCY
    bot.reply_to(message, HELP_EMERGENCY, parse_mode="Markdown")

@bot.message_handler(commands=["slang"])
def handle_slang(message):
    from espaluz_menu import get_slang, SLANG_PANAMA
    parts = message.text.split()
    if len(parts) > 1:
        country = parts[1].lower()
        bot.reply_to(message, get_slang(country), parse_mode="Markdown")
    else:
        # Default to Panama
        bot.reply_to(message, SLANG_PANAMA + "\\n\\n💡 Try: /slang mexico, /slang colombia, /slang argentina", parse_mode="Markdown")

@bot.message_handler(commands=["org"])
def handle_org(message):
    from espaluz_emotional_brain import validate_org_code, track_activity
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /org YOUR_CODE\\n\\nExample: /org AMCHAM_PANAMA")
        return
    
    code = parts[1].upper()
    org = validate_org_code(code)
    
    if org:
        track_activity(str(message.from_user.id), code)
        bot.reply_to(message, f"✅ {org['welcome_message']}\\n\\n🏢 {org['name']}\\n📅 Trial: {org['trial_days']} days")
    else:
        bot.reply_to(message, "❌ Invalid code. Contact your organization.")

@bot.message_handler(commands=["feedback"])
def handle_feedback(message):
    bot.reply_to(message, "💬 We'd love your feedback!\\n\\nPlease reply with:\\n• ⭐ Rating (1-5)\\n• 💬 Your experience\\n\\nExample: 5 ⭐ EspaLuz helped my family adapt to Panama!")

@bot.message_handler(commands=["metrics"])
def handle_metrics(message):
    try:
        from espaluz_emotional_brain import get_analytics_metrics
        metrics = get_analytics_metrics()
        msg = f"📊 *EspaLuz Metrics*\\n\\n"
        msg += f"👥 Total Users: {metrics['total_users']}\\n"
        msg += f"📈 Weekly Active: {metrics['weekly_active_users']}\\n"
        msg += f"🔄 30-Day Retention: {metrics['retention_30_day']}\\n"
        msg += f"🏢 Organizations: {metrics['organizations_piloting']}\\n"
        msg += f"⭐ Testimonials: {metrics['testimonials_collected']}"
        bot.reply_to(message, msg, parse_mode="Markdown")
    except:
        bot.reply_to(message, "Metrics not available")
"""


if __name__ == "__main__":
    print("=" * 60)
    print("📋 EspaLuz Menu System")
    print("=" * 60)
    print("\nMenu length:", len(MENU_TEXT), "characters")
    print("\nAvailable help categories:")
    for cat in ["banking", "medical", "school", "shopping", "transport", "emergency"]:
        print(f"  • /help_{cat}")
    print("\nAvailable slang:")
    for country in ["panama", "mexico", "colombia", "argentina", "costa_rica"]:
        print(f"  • /slang {country}")
