#!/usr/bin/env python3
"""
UPGRADE: Deep country contexts for TOP expat destinations
Focus on: Ecuador (Cuenca), Argentina (Buenos Aires), Dominican Republic
"""

with open('espaluz_country_contexts.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Ecuador's basic context with deep practical info
old_ecuador = '''    Country.ECUADOR: {
        "name": "Ecuador",
        "flag": "🇪🇨",
        "currency": "USD (dollarized since 2000)",
        "timezone": "ECT (UTC-5)",
        "spanish_variant": "ecuadorian",
        
        "local_vocabulary": {
            "expressions": {
                "chuta": "Darn! (exclamation)",
                "chévere": "Cool",
                "ñaño/ñaña": "Brother/sister (friend)",
                "man": "Dude (borrowed from English)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Pichincha", "Banco Guayaquil", "Produbanco"]
            },
            "immigration": {
                "tips": "Several visa options, relatively expat-friendly"
            }
        },
        
        "cultural_notes": {
            "regions": "Costa (coast), Sierra (highlands), Oriente (Amazon) - different cultures",
            "usd": "Prices often seem cheap to Americans due to USD"
        }
    },'''

new_ecuador = '''    Country.ECUADOR: {
        "name": "Ecuador",
        "flag": "🇪🇨",
        "currency": "USD (dollarized since 2000)",
        "timezone": "ECT (UTC-5)",
        "spanish_variant": "ecuadorian",
        
        "expat_hotspots": ["Cuenca (retirement capital)", "Quito (capital)", "Manta (beach)", "Vilcabamba (valley)"],
        
        "local_vocabulary": {
            "greetings": {
                "¿Qué fue?": "What's up?",
                "Cómo le va": "How's it going (formal)"
            },
            "expressions": {
                "chuta": "Darn! (mild exclamation)",
                "chévere": "Cool/great",
                "ñaño/ñaña": "Brother/sister (friend)",
                "man": "Dude",
                "achachay": "It's cold!",
                "arrarray": "It's hot!",
                "chucha": "Damn (vulgar)",
                "de ley": "For sure/definitely",
                "simón": "Yes (informal)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Pichincha (largest)", "Banco Guayaquil", "Produbanco", "Banco del Pacífico"],
                "phrases": {
                    "opening_account": "Quisiera abrir una cuenta de ahorros",
                    "exchange": "No exchange needed - USD is local currency!"
                },
                "tips": "Cédula de identidad (foreign ID) needed. Process faster in Cuenca than Quito."
            },
            "immigration": {
                "office": "Ministerio de Relaciones Exteriores y Movilidad Humana",
                "visa_types": ["Tourist (90 days)", "Professional", "Investor", "Retirement (Jubilado)", "RIMPE (investor)"],
                "tips": "Pensionado visa popular with retirees - requires $1,400/month income proof. Cuenca has efficient processing."
            },
            "healthcare": {
                "emergency": "911",
                "public_system": "IESS (Seguro Social) - decent quality, low cost",
                "private": ["Hospital Monte Sinaí (Cuenca)", "Hospital del Río", "Clínica Santa Inés"],
                "pharmacies": ["Fybeca", "Pharmacys", "Cruz Azul"],
                "tips": "Private healthcare very affordable. Cuenca known for medical tourism."
            },
            "housing": {
                "cuenca_neighborhoods": ["El Centro Histórico", "Gringolandia (popular expat area)", "Puertas del Sol"],
                "average_rent": "$400-800/month for nice apartment in Cuenca",
                "tips": "Many furnished rentals available. Check Cuenca High Life Facebook group."
            },
            "transportation": {
                "buses": "Very cheap ($0.25-0.35 in cities)",
                "taxis": "Use taxímetro (meter) - very affordable",
                "intercity": "Comfortable buses to Quito (~$15, 8-10 hours from Cuenca)"
            }
        },
        
        "cultural_notes": {
            "regions": "Costa (coast), Sierra (highlands), Oriente (Amazon) - very different cultures and climates",
            "cuenca_culture": "Colonial charm, UNESCO heritage, arts scene, known as most polite city",
            "food": "Try cuy (guinea pig), locro de papa, encebollado (coast)",
            "siesta": "Some shops close 1-3 PM",
            "altitude": "Cuenca is 2,500m - take it easy first days",
            "weather": "Cuenca has 'eternal spring' - sweater weather year-round"
        }
    },'''

if old_ecuador in content:
    content = content.replace(old_ecuador, new_ecuador)
    changes = 1
    print("✓ Ecuador upgraded with Cuenca-focused deep context")
else:
    changes = 0
    print("Ecuador pattern not found")

# Now upgrade Argentina
old_argentina = '''    Country.ARGENTINA: {
        "name": "Argentina",
        "flag": "🇦🇷",
        "currency": "Argentine Peso (ARS)",
        "timezone": "ART (UTC-3)",
        "spanish_variant": "rioplatense",
        
        "local_vocabulary": {
            "expressions": {
                "che": "Hey (iconic Argentine word)",
                "boludo": "Dude (can be friendly or offensive)",
                "quilombo": "Mess/chaos",
                "mina": "Girl/woman",
                "guita": "Money",
                "laburo": "Work",
                "morfar": "To eat"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "tips": "Complex due to currency controls. Blue dollar vs official rate."
            },
            "inflation": "VERY HIGH - prices change frequently, use cash wisely"
        },
        
        "cultural_notes": {
            "voseo": "Uses 'vos' instead of 'tú' - different verb conjugations",
            "mate": "Sharing mate is social ritual",
            "asado": "Sunday asado is sacred family time"
        }
    },'''

new_argentina = '''    Country.ARGENTINA: {
        "name": "Argentina",
        "flag": "🇦🇷",
        "currency": "Argentine Peso (ARS) - MAJOR inflation",
        "timezone": "ART (UTC-3)",
        "spanish_variant": "rioplatense",
        
        "expat_hotspots": ["Buenos Aires (Palermo, Recoleta, Belgrano)", "Mendoza (wine country)", "Córdoba"],
        
        "local_vocabulary": {
            "greetings": {
                "¿Todo bien?": "Everything good?",
                "¿Cómo andás?": "How are you? (vos form)"
            },
            "expressions": {
                "che": "Hey (iconic - like 'dude')",
                "boludo/boluda": "Dude/friend (context-dependent!)",
                "quilombo": "Mess/chaos/problem",
                "mina": "Girl/woman",
                "chabón": "Guy/dude",
                "guita": "Money",
                "laburo": "Work/job",
                "morfar": "To eat",
                "fiaca": "Laziness",
                "afanar": "To steal/rip off",
                "re": "Very (re bueno = really good)",
                "flashear": "To trip out/imagine",
                "garpar": "To pay"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Nación", "Banco Galicia", "Santander", "BBVA"],
                "phrases": {
                    "exchange": "¿Cuál es el cambio hoy?",
                    "withdrawal": "Quiero retirar efectivo"
                },
                "tips": "COMPLEX! Blue dollar (informal rate) vs official rate. Many expats use Western Union or crypto. Withdraw USD abroad if possible."
            },
            "immigration": {
                "office": "Dirección Nacional de Migraciones",
                "visa_types": ["Tourist (90 days)", "Rentista (passive income)", "Digital Nomad (new!)"],
                "tips": "Residency relatively easy. DNI (document) takes time but unlocks everything."
            },
            "healthcare": {
                "emergency": "107 (SAME ambulance)",
                "public_system": "Hospital público - free but can be crowded",
                "private": ["OSDE", "Swiss Medical", "Galeno"],
                "tips": "Prepagas (private insurance) affordable by US standards - $100-200/month"
            },
            "transportation": {
                "SUBE_card": "Essential! Load credit for subte (metro), buses, trains",
                "taxis": "Use Uber or Cabify (cheaper than street taxis)",
                "phrases": {
                    "taxi": "¿Me llevás a [address]?",
                    "SUBE": "¿Dónde cargo la SUBE?"
                }
            },
            "money_tips": {
                "inflation_warning": "Prices can change 10%+ per month!",
                "blue_dollar": "Informal exchange rate - significantly higher than official",
                "cash": "Carry cash, many places don't accept foreign cards well",
                "western_union": "Many expats receive USD via WU at blue rate"
            }
        },
        
        "cultural_notes": {
            "voseo": "Uses 'vos' instead of 'tú' - '¿Cómo estás?' becomes '¿Cómo estás?' same but conjugation differs",
            "mate": "Sharing mate is SACRED. Never say no without good reason.",
            "asado": "Sunday asado with family - don't schedule conflicts",
            "dinner_time": "Dinner starts 9-10 PM, dinner invitations mean 10 PM",
            "besos": "Greet with one kiss on cheek (even men to men among friends)",
            "therapy": "Buenos Aires has most psychologists per capita - therapy is normal"
        }
    },'''

if old_argentina in content:
    content = content.replace(old_argentina, new_argentina)
    changes += 1
    print("✓ Argentina upgraded with Buenos Aires deep context")
else:
    print("Argentina pattern not found")

if changes > 0:
    with open('espaluz_country_contexts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\\nSUCCESS: Upgraded {changes} country contexts!")
else:
    print("\\nNo changes made")
