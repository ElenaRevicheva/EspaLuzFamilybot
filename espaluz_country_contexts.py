"""
EspaLuz Country Contexts - 21 Spanish-Speaking Countries
=========================================================
Version: 1.0
Created: January 10, 2026

Real-life practicalities for expats, travelers, and locals.
NOT just tourism - actual life situations: banking, healthcare, schools,
immigration, daily errands, emergencies.

USAGE: Import and use alongside existing main.py functionality.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# ALL 21 SPANISH-SPEAKING COUNTRIES
# =============================================================================

class Country(Enum):
    """All Spanish-speaking countries."""
    PANAMA = "panama"
    MEXICO = "mexico"
    COLOMBIA = "colombia"
    ARGENTINA = "argentina"
    SPAIN = "spain"
    PERU = "peru"
    CHILE = "chile"
    ECUADOR = "ecuador"
    GUATEMALA = "guatemala"
    COSTA_RICA = "costa_rica"
    CUBA = "cuba"
    BOLIVIA = "bolivia"
    DOMINICAN_REPUBLIC = "dominican_republic"
    HONDURAS = "honduras"
    PARAGUAY = "paraguay"
    NICARAGUA = "nicaragua"
    EL_SALVADOR = "el_salvador"
    URUGUAY = "uruguay"
    PUERTO_RICO = "puerto_rico"
    VENEZUELA = "venezuela"
    EQUATORIAL_GUINEA = "equatorial_guinea"


# =============================================================================
# COUNTRY-SPECIFIC CONTEXTS
# =============================================================================

COUNTRY_CONTEXTS = {
    # =========================================================================
    # PANAMA (Primary - Most Detailed)
    # =========================================================================
    Country.PANAMA: {
        "name": "Panamá",
        "flag": "🇵🇦",
        "currency": "USD (Balboa for coins)",
        "timezone": "EST (UTC-5)",
        "spanish_variant": "panamanian",
        
        # Local vocabulary
        "local_vocabulary": {
            "greetings": {
                "¿Qué xopá?": "What's up? (very informal)",
                "¿Qué es lo que hay?": "What's going on?",
                "Buenas": "Short greeting (any time of day)"
            },
            "expressions": {
                "chuleta": "Darn! / Wow! (exclamation)",
                "vaina": "Thing / stuff (universal word)",
                "juega vivo": "Be smart / Don't get scammed",
                "pelaíto": "Kid / young person",
                "chombo": "Person of Afro-Caribbean descent",
                "rabiblancos": "Upper class (old money)",
                "yeye": "Trendy / fancy",
                "quedó pelao": "Ran out of money",
                "frío como hielo": "Very cold (drinks)",
                "¿Me regalas?": "Can you give me? (polite request)"
            },
            "food": {
                "patacones": "Fried plantains (must-try)",
                "sancocho": "Traditional chicken soup",
                "arroz con pollo": "Rice with chicken",
                "ceviche": "Raw fish marinated in lime",
                "ropa vieja": "Shredded beef dish",
                "empanadas": "Stuffed pastries",
                "chicha": "Corn-based drink",
                "raspao": "Shaved ice with syrup"
            }
        },
        
        # Real-life scenarios (NOT tourism)
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco General", "Banistmo", "BAC", "Global Bank", "Multibank"],
                "phrases": {
                    "opening_account": "Quiero abrir una cuenta / I want to open an account",
                    "wire_transfer": "Necesito hacer una transferencia / I need to make a transfer",
                    "atm_problem": "El cajero se tragó mi tarjeta / The ATM ate my card",
                    "exchange_rate": "¿Cuál es la tasa de cambio? / What's the exchange rate?"
                },
                "tips": "Bring cédula or passport + utility bill for address proof"
            },
            "immigration": {
                "office": "Migración Panama - Av. Cuba, Casco Viejo",
                "phrases": {
                    "visa_extension": "Necesito extender mi visa / I need to extend my visa",
                    "residency": "Quiero aplicar para residencia / I want to apply for residency",
                    "status_check": "¿Cuál es el estado de mi solicitud? / What's my application status?"
                },
                "visa_types": ["Friendly Nations", "Pensionado", "SIRE", "Investor", "Student"],
                "tips": "Arrive early, bring ALL documents, expect to wait"
            },
            "healthcare": {
                "emergency": "911",
                "hospitals": ["Hospital Punta Pacífica", "Hospital Nacional", "Centro Médico Paitilla"],
                "public_system": "CSS (Caja de Seguro Social)",
                "phrases": {
                    "emergency": "Es una emergencia / It's an emergency",
                    "allergy": "Soy alérgico a... / I'm allergic to...",
                    "pharmacy": "¿Tienen esta medicina? / Do you have this medicine?",
                    "prescription": "Necesito una receta / I need a prescription"
                }
            },
            "schools": {
                "international": ["ISP", "Balboa Academy", "Oxford", "King's College", "Metropolitan"],
                "bilingual": ["Boston School", "Episcopal", "Alberto Einstein"],
                "phrases": {
                    "enrollment": "Quiero inscribir a mi hijo / I want to enroll my child",
                    "meeting": "Tengo una cita con el maestro / I have a meeting with the teacher",
                    "uniform": "¿Dónde compro el uniforme? / Where do I buy the uniform?"
                }
            },
            "transportation": {
                "taxi_apps": ["inDriver", "Uber", "Cabify"],
                "phrases": {
                    "taxi": "¿Cuánto cuesta ir a...? / How much to go to...?",
                    "metro": "¿Cuál línea va a...? / Which line goes to...?",
                    "bus": "¿Este bus pasa por...? / Does this bus go by...?"
                },
                "license": "Autoridad del Tránsito y Transporte Terrestre (ATTT)",
                "sertracen": "For license renewals and vehicle registration"
            },
            "utilities": {
                "electricity": "ENSA / Edemet Edechi / Naturgy",
                "water": "IDAAN",
                "internet": ["Cable & Wireless", "Tigo", "Claro", "Digicel"],
                "phrases": {
                    "bill": "Quiero pagar mi recibo / I want to pay my bill",
                    "outage": "No hay luz/agua / There's no power/water",
                    "installation": "Necesito instalación de internet / I need internet installation"
                }
            },
            "shopping": {
                "supermarkets": ["Riba Smith", "Super 99", "El Rey", "PriceSmart", "Machetazo"],
                "hardware": ["Do It Center", "Novey", "Cochez"],
                "phrases": {
                    "find_item": "¿Dónde encuentro...? / Where do I find...?",
                    "price": "¿Cuánto cuesta esto? / How much is this?",
                    "discount": "¿Tienen descuento? / Do you have a discount?"
                }
            },
            "housing": {
                "phrases": {
                    "rent": "Busco apartamento para alquilar / I'm looking for an apartment to rent",
                    "deposit": "¿Cuánto es el depósito? / How much is the deposit?",
                    "utilities_included": "¿Los servicios están incluidos? / Are utilities included?",
                    "maintenance": "Necesito un plomero/electricista / I need a plumber/electrician"
                },
                "portero": "Building doorman/security - very common",
                "tips": "Negotiate rent, check water pressure, ask about A/C maintenance"
            }
        },
        
        # Cultural notes
        "cultural_notes": {
            "formality": "Use 'usted' with strangers, switch to 'tú' when invited",
            "time": "Hora panameña - expect delays, build in buffer time",
            "tips": "10% restaurant tip is standard, not mandatory",
            "holidays": ["Carnaval (Feb)", "Semana Santa", "Nov 3-28 (many national days)"]
        }
    },
    
    # =========================================================================
    # MEXICO
    # =========================================================================
    Country.MEXICO: {
        "name": "México",
        "flag": "🇲🇽",
        "currency": "Mexican Peso (MXN)",
        "timezone": "Multiple (Central, Pacific, Mountain)",
        "spanish_variant": "mexican",
        
        "local_vocabulary": {
            "greetings": {
                "¿Qué onda?": "What's up?",
                "¿Mande?": "Pardon? / What did you say?",
                "Órale": "Okay / Let's go / Wow"
            },
            "expressions": {
                "chido/padre": "Cool / great",
                "neta": "Really / truth",
                "güey": "Dude (informal)",
                "no manches": "No way! / You're kidding",
                "chamba": "Work / job",
                "fresa": "Preppy / snobby person",
                "ahorita": "Right now (but could mean later)",
                "un chingo": "A lot (vulgar)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["BBVA", "Santander", "Banorte", "Citibanamex", "HSBC"],
                "phrases": {
                    "opening_account": "Quiero abrir una cuenta",
                    "foreign_account": "Soy extranjero, ¿qué necesito?"
                }
            },
            "immigration": {
                "office": "INM (Instituto Nacional de Migración)",
                "visa_types": ["Residente Temporal", "Residente Permanente", "FMM (tourist)"],
                "tips": "CURP is essential - get it early"
            },
            "healthcare": {
                "emergency": "911",
                "public_system": "IMSS (employees), ISSSTE (government)",
                "private": ["ABC", "Médica Sur", "Hospital Español"],
                "pharmacies": ["Farmacia del Ahorro", "Farmacias Similares", "San Pablo"]
            }
        },
        
        "cultural_notes": {
            "formality": "Mexicans are formal, use titles (Licenciado, Ingeniero)",
            "food_times": "Comida (lunch) is main meal, 2-4 PM",
            "tips": "10-15% at restaurants, tip bag carriers at grocery stores"
        }
    },
    
    # =========================================================================
    # COLOMBIA
    # =========================================================================
    Country.COLOMBIA: {
        "name": "Colombia",
        "flag": "🇨🇴",
        "currency": "Colombian Peso (COP)",
        "timezone": "COT (UTC-5)",
        "spanish_variant": "colombian",
        
        "local_vocabulary": {
            "greetings": {
                "¿Quiubo?": "What's up? (Qué hubo)",
                "Parcero/Parce": "Buddy/friend (Medellín)",
                "Bacano": "Cool/great"
            },
            "expressions": {
                "chimba": "Cool/great (can be vulgar)",
                "berraco": "Awesome / tough person",
                "sumercé": "Formal 'you' (Bogotá)",
                "a la orden": "At your service / You're welcome",
                "de una": "Right away / Let's do it",
                "marica": "Dude (between friends, careful usage)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Bancolombia", "Davivienda", "Banco de Bogotá", "BBVA"],
                "tips": "Cédula de extranjería needed for most banking"
            },
            "immigration": {
                "office": "Migración Colombia",
                "visa_types": ["M (Migrant)", "V (Visitor)", "R (Resident)"],
                "tips": "Digital nomad visa available since 2022"
            },
            "safety": {
                "emergency": "123",
                "tips": "Use official taxis or apps, don't flash valuables"
            }
        },
        
        "cultural_notes": {
            "regions": "Paisas (Medellín), Costeños (Coast), Rolos (Bogotá) - different accents",
            "coffee": "Tinto = small black coffee, available everywhere"
        }
    },
    
    # =========================================================================
    # ARGENTINA
    # =========================================================================
    Country.ARGENTINA: {
        "name": "Argentina",
        "flag": "🇦🇷",
        "currency": "Argentine Peso (ARS) - watch exchange rates!",
        "timezone": "ART (UTC-3)",
        "spanish_variant": "rioplatense",
        
        "local_vocabulary": {
            "greetings": {
                "¿Qué onda?": "What's up?",
                "Che": "Hey (like 'dude')"
            },
            "expressions": {
                "boludo": "Dude/idiot (depends on context)",
                "bárbaro": "Great/awesome",
                "laburo": "Work",
                "mango": "Money (1 peso)",
                "afanar": "To steal/to work hard",
                "morfar": "To eat",
                "bondi": "Bus"
            },
            "voseo": {
                "note": "Argentina uses 'vos' instead of 'tú'",
                "examples": {
                    "tú eres → vos sos": "You are",
                    "tú tienes → vos tenés": "You have",
                    "tú puedes → vos podés": "You can"
                }
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Nación", "Santander", "BBVA", "Galicia"],
                "tips": "Blue dollar vs official rate - research before exchanging"
            },
            "immigration": {
                "office": "Dirección Nacional de Migraciones",
                "tips": "DNI (ID) takes time to get, but essential"
            }
        },
        
        "cultural_notes": {
            "mate": "Sharing mate is social ritual - learn the etiquette",
            "dinner": "Argentines eat dinner late (9-11 PM)",
            "kiss": "One kiss on cheek for greeting"
        }
    },
    
    # =========================================================================
    # SPAIN
    # =========================================================================
    Country.SPAIN: {
        "name": "España",
        "flag": "🇪🇸",
        "currency": "Euro (EUR)",
        "timezone": "CET (UTC+1)",
        "spanish_variant": "castilian",
        
        "local_vocabulary": {
            "greetings": {
                "¿Qué tal?": "How are you?",
                "Buenas": "Short greeting"
            },
            "expressions": {
                "vale": "Okay (very common)",
                "mola": "Cool",
                "tío/tía": "Dude (uncle/aunt literally)",
                "currar": "To work",
                "guay": "Cool",
                "flipar": "To freak out/be amazed"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Santander", "BBVA", "CaixaBank", "Sabadell"],
                "tips": "NIE required for almost everything"
            },
            "immigration": {
                "office": "Oficina de Extranjería",
                "tips": "Empadronamiento (registration) is first step for everything"
            },
            "healthcare": {
                "public": "Sistema Nacional de Salud - free with contributions",
                "tips": "Tarjeta sanitaria from your region"
            }
        },
        
        "cultural_notes": {
            "siesta": "Many shops close 2-5 PM",
            "dinner": "Dinner starts 9-10 PM",
            "regions": "Cataluña, País Vasco, Galicia have their own languages"
        }
    },
    
    # =========================================================================
    # COSTA RICA
    # =========================================================================
    Country.COSTA_RICA: {
        "name": "Costa Rica",
        "flag": "🇨🇷",
        "currency": "Colón (CRC) + USD widely accepted",
        "timezone": "CST (UTC-6)",
        "spanish_variant": "costa_rican",
        
        "local_vocabulary": {
            "expressions": {
                "pura vida": "Pure life - greeting, goodbye, and philosophy",
                "mae": "Dude",
                "tuanis": "Cool",
                "tico/tica": "Costa Rican person",
                "chunche": "Thing/stuff",
                "brete": "Work",
                "la vara": "The thing/situation"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["BAC", "Banco Nacional", "BCR", "Scotiabank"],
                "tips": "DIMEX card needed for foreigners"
            },
            "immigration": {
                "office": "Dirección General de Migración y Extranjería",
                "tips": "90-day visa run is common but increasingly scrutinized"
            },
            "healthcare": {
                "public": "CCSS (Caja) - good quality",
                "tips": "Monthly contribution based on income"
            }
        },
        
        "cultural_notes": {
            "pura_vida": "Not just words - it's the laid-back lifestyle",
            "environment": "Very eco-conscious country"
        }
    },
    
    # =========================================================================
    # CHILE
    # =========================================================================
    Country.CHILE: {
        "name": "Chile",
        "flag": "🇨🇱",
        "currency": "Chilean Peso (CLP)",
        "timezone": "CLT (UTC-3/-4)",
        "spanish_variant": "chilean",
        
        "local_vocabulary": {
            "expressions": {
                "cachai": "You know? / Do you get it?",
                "po": "Added to everything (sí po = yes)",
                "bacán": "Cool",
                "al tiro": "Right away",
                "pololo/polola": "Boyfriend/girlfriend",
                "fome": "Boring"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco de Chile", "Santander", "BCI", "Itaú"],
                "tips": "RUT (tax ID) essential for everything"
            }
        },
        
        "cultural_notes": {
            "chilean_spanish": "Known for being difficult - fast, lots of slang",
            "class_conscious": "Society can be quite stratified"
        }
    },
    
    # =========================================================================
    # PERU
    # =========================================================================
    Country.PERU: {
        "name": "Perú",
        "flag": "🇵🇪",
        "currency": "Sol (PEN)",
        "timezone": "PET (UTC-5)",
        "spanish_variant": "peruvian",
        
        "local_vocabulary": {
            "expressions": {
                "chévere": "Cool",
                "pata": "Friend/buddy",
                "jato": "House",
                "chamba": "Work",
                "causa": "Friend (also a dish)",
                "ya": "Okay/already (very versatile)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["BCP", "Interbank", "BBVA", "Scotiabank"]
            },
            "immigration": {
                "office": "Migraciones",
                "tips": "Carné de extranjería needed for most things"
            }
        },
        
        "cultural_notes": {
            "food": "Peruvian cuisine is world-famous - ceviche, lomo saltado",
            "punctuality": "Hora peruana - expect lateness"
        }
    },
    
    # =========================================================================
    # ECUADOR
    # =========================================================================
    Country.ECUADOR: {
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
    },
    
    # =========================================================================
    # DOMINICAN REPUBLIC
    # =========================================================================
    Country.DOMINICAN_REPUBLIC: {
        "name": "República Dominicana",
        "flag": "🇩🇴",
        "currency": "Dominican Peso (DOP)",
        "timezone": "AST (UTC-4)",
        "spanish_variant": "dominican",
        
        "local_vocabulary": {
            "expressions": {
                "tato": "Okay/alright",
                "dime a ver": "Tell me",
                "vaina": "Thing (like Panama)",
                "jevi": "Cool (from 'heavy')",
                "un chin": "A little bit"
            }
        },
        
        "cultural_notes": {
            "music": "Bachata and merengue everywhere",
            "baseball": "National passion"
        }
    },
    
    # =========================================================================
    # URUGUAY
    # =========================================================================
    Country.URUGUAY: {
        "name": "Uruguay",
        "flag": "🇺🇾",
        "currency": "Uruguayan Peso (UYU)",
        "timezone": "UYT (UTC-3)",
        "spanish_variant": "rioplatense",
        
        "local_vocabulary": {
            "expressions": {
                "bo": "Hey (like 'che' in Argentina)",
                "ta": "Okay (very common)",
                "bárbaro": "Great"
            },
            "note": "Uses 'vos' like Argentina"
        },
        
        "cultural_notes": {
            "mate": "Even more mate culture than Argentina",
            "progressive": "Very progressive country, LGBTQ+ friendly"
        }
    },
    
    # =========================================================================
    # UPGRADED COUNTRIES (Enhanced with real-life practicalities)
    # =========================================================================
    Country.GUATEMALA: {
        "name": "Guatemala",
        "flag": "🇬🇹",
        "currency": "Quetzal (GTQ)",
        "timezone": "CST (UTC-6)",
        "spanish_variant": "guatemalan",
        
        "local_vocabulary": {
            "expressions": {
                "chapín/chapina": "Guatemalan person",
                "cabal": "Exactly right / Precisely",
                "pisto": "Money",
                "canche": "Blonde person",
                "patojo/patoja": "Kid/young person",
                "chilero": "Cool/nice",
                "a huevo": "Of course / Yes",
                "aguas": "Watch out! Be careful!"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banrural", "Banco Industrial", "BAM", "G&T Continental"],
                "tips": "DPI (ID card) required for everything. USD accepted in tourist areas."
            },
            "immigration": {
                "office": "Instituto Guatemalteco de Migración",
                "tips": "90-day visa for most nationalities. Extend at Migración."
            },
            "healthcare": {
                "emergency": "911 or 122",
                "hospitals": ["Hospital Herrera Llerandi", "Centro Médico"],
                "tips": "Private healthcare recommended for expats"
            },
            "schools": {
                "international": ["American School of Guatemala", "Colegio Interamericano"],
                "tips": "Many bilingual options in Guatemala City and Antigua"
            }
        },
        
        "cultural_notes": {
            "mayan_influence": "Strong indigenous culture, many Mayan languages spoken",
            "antigua": "Colonial city, UNESCO World Heritage, popular with expats"
        }
    },
    
    Country.HONDURAS: {
        "name": "Honduras",
        "flag": "🇭🇳",
        "currency": "Lempira (HNL)",
        "timezone": "CST (UTC-6)",
        "spanish_variant": "honduran",
        
        "local_vocabulary": {
            "expressions": {
                "catracho/catracha": "Honduran person",
                "maje": "Dude/guy",
                "cipote/cipota": "Kid",
                "púchica": "Wow! (exclamation)",
                "cheque": "Okay/Alright",
                "cabal": "Exactly"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["BAC Credomatic", "Banco Atlántida", "Ficohsa"],
                "tips": "USD widely accepted. ATMs in major cities."
            },
            "healthcare": {
                "emergency": "911",
                "tips": "Private healthcare recommended. Medical tourism for dental."
            }
        },
        
        "cultural_notes": {
            "roatan": "Bay Islands popular for diving and expat retirement",
            "safety": "Stay in tourist areas, use registered taxis"
        }
    },
    
    Country.EL_SALVADOR: {
        "name": "El Salvador",
        "flag": "🇸🇻",
        "currency": "USD (Bitcoin is legal tender!)",
        "timezone": "CST (UTC-6)",
        "spanish_variant": "salvadoran",
        
        "local_vocabulary": {
            "expressions": {
                "chero/chera": "Friend/buddy",
                "cipote/cipota": "Kid",
                "vaya pues": "Okay then",
                "púchica": "Wow! (exclamation)",
                "bayunco": "Silly/dumb",
                "chucho": "Dog"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Agrícola", "Davivienda", "Banco Cuscatlán"],
                "tips": "Bitcoin accepted at many businesses! Chivo wallet for Bitcoin."
            },
            "immigration": {
                "tips": "Very crypto-friendly. Special visas for Bitcoin investors."
            },
            "healthcare": {
                "emergency": "911",
                "tips": "Private hospitals good quality in San Salvador"
            }
        },
        
        "cultural_notes": {
            "bitcoin": "First country to make Bitcoin legal tender (2021)",
            "pupusas": "National dish - must try!",
            "surf": "Great surf beaches on the Pacific coast"
        }
    },
    
    Country.NICARAGUA: {
        "name": "Nicaragua",
        "flag": "🇳🇮",
        "currency": "Córdoba (NIO)",
        "timezone": "CST (UTC-6)",
        "spanish_variant": "nicaraguan",
        
        "local_vocabulary": {
            "expressions": {
                "nica": "Nicaraguan",
                "chunche": "Thing/stuff",
                "tuani": "Cool",
                "dale pues": "Okay then",
                "chele/chela": "White person/foreigner",
                "pinolero": "Nicaraguan (from pinol drink)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banpro", "BAC", "Lafise"],
                "tips": "USD accepted in tourist areas. Cash preferred."
            },
            "healthcare": {
                "emergency": "118",
                "tips": "Private healthcare in Managua recommended"
            }
        },
        
        "cultural_notes": {
            "affordable": "One of the most affordable countries in Central America",
            "granada_leon": "Colonial cities popular with expats"
        }
    },
    
    Country.CUBA: {
        "name": "Cuba",
        "flag": "🇨🇺",
        "currency": "Cuban Peso (CUP), also MLC for foreigners",
        "timezone": "EST (UTC-5)",
        "spanish_variant": "cuban",
        
        "local_vocabulary": {
            "expressions": {
                "asere": "Friend/buddy",
                "socio": "Buddy/pal",
                "¿qué bolá?": "What's up?",
                "chévere": "Cool/great",
                "guagua": "Bus",
                "yuma": "Foreigner (especially American)",
                "resolver": "To figure out/solve (very Cuban concept)",
                "no es fácil": "It's not easy (common expression)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "tips": "Very limited banking. Bring cash. No US credit cards."
            },
            "healthcare": {
                "tips": "Famous for good healthcare. International clinics for foreigners."
            }
        },
        
        "cultural_notes": {
            "resolver": "Cubans are experts at 'resolver' - finding creative solutions",
            "music": "Salsa, son, and reggaeton everywhere",
            "internet": "Limited but improving. WiFi hotspots in parks."
        }
    },
    
    Country.BOLIVIA: {
        "name": "Bolivia",
        "flag": "🇧🇴",
        "currency": "Boliviano (BOB)",
        "timezone": "BOT (UTC-4)",
        "spanish_variant": "bolivian",
        
        "local_vocabulary": {
            "expressions": {
                "yapa": "A little extra for free",
                "cholita": "Indigenous woman in traditional dress",
                "imilla": "Girl (Aymara origin)",
                "ñato/ñata": "Friend",
                "che": "Hey (to get attention)"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Mercantil", "BNB", "Banco Unión"],
                "tips": "Cash is king. Limited ATMs outside major cities."
            },
            "healthcare": {
                "tips": "Private clinics in La Paz and Santa Cruz recommended"
            }
        },
        
        "cultural_notes": {
            "altitude": "La Paz is 3,640m - prepare for altitude sickness",
            "indigenous": "Strong indigenous culture, Aymara and Quechua languages"
        }
    },
    
    Country.PARAGUAY: {
        "name": "Paraguay",
        "flag": "🇵🇾",
        "currency": "Guaraní (PYG)",
        "timezone": "PYT (UTC-4/-3)",
        "spanish_variant": "paraguayan",
        
        "local_vocabulary": {
            "expressions": {
                "nde": "You (Guaraní, very common)",
                "chake": "Watch out",
                "mbore": "A lot",
                "kóga": "How are you? (Guaraní)"
            },
            "note": "Guaraní is co-official - many mix Spanish and Guaraní (Jopara)"
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Itaú", "Banco Continental", "BBVA"],
                "tips": "Low taxes attract businesses. USD accepted."
            },
            "healthcare": {
                "tips": "Private healthcare affordable in Asunción"
            }
        },
        
        "cultural_notes": {
            "tereré": "National drink - cold yerba mate, essential in hot weather",
            "bilingual": "Only truly bilingual country in Latin America"
        }
    },
    
    Country.VENEZUELA: {
        "name": "Venezuela",
        "flag": "🇻🇪",
        "currency": "Bolívar (VES) - USD widely used due to hyperinflation",
        "timezone": "VET (UTC-4)",
        "spanish_variant": "venezuelan",
        
        "local_vocabulary": {
            "expressions": {
                "chamo/chama": "Dude/girl",
                "chévere": "Cool/great",
                "pana": "Friend",
                "burda": "A lot/very",
                "¿qué más?": "What's up?",
                "arrecho": "Angry (or great, depending on context)",
                "marico": "Dude (can be offensive, use carefully)",
                "fino": "Fine/cool"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "tips": "USD and crypto essential. Zelle popular for transfers."
            },
            "healthcare": {
                "tips": "Private healthcare for expats. Bring medicines from abroad."
            }
        },
        
        "cultural_notes": {
            "dollarized": "Effective dollarization - prices often in USD",
            "arepas": "National food - must try",
            "diaspora": "Many Venezuelans abroad - strong community"
        }
    },
    
    Country.PUERTO_RICO: {
        "name": "Puerto Rico",
        "flag": "🇵🇷",
        "currency": "USD",
        "timezone": "AST (UTC-4)",
        "spanish_variant": "puerto_rican",
        
        "local_vocabulary": {
            "expressions": {
                "boricua": "Puerto Rican",
                "wepa": "Awesome!/Let's go!",
                "brutal": "Awesome/amazing",
                "chacho": "Dude (shortened from 'muchacho')",
                "nene/nena": "Boy/girl (or term of endearment)",
                "mira": "Look (used constantly)",
                "¿qué es la que hay?": "What's up?"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Popular", "FirstBank", "Oriental Bank"],
                "tips": "US banking system. All major US banks work."
            },
            "healthcare": {
                "tips": "US healthcare system applies. Insurance important."
            },
            "immigration": {
                "tips": "US territory - no visa needed for US citizens"
            }
        },
        
        "cultural_notes": {
            "spanglish": "Very common - code-switching between Spanish and English",
            "tax_benefits": "Act 60 tax incentives for businesses and investors",
            "hurricanes": "Hurricane season June-November - be prepared"
        }
    },
    
    Country.DOMINICAN_REPUBLIC: {
        "name": "República Dominicana",
        "flag": "🇩🇴",
        "currency": "Dominican Peso (DOP)",
        "timezone": "AST (UTC-4)",
        "spanish_variant": "dominican",
        
        "local_vocabulary": {
            "expressions": {
                "tato": "Okay/alright",
                "dime a ver": "Tell me",
                "vaina": "Thing (like Panama)",
                "jevi": "Cool (from 'heavy')",
                "un chin": "A little bit",
                "klk/qué lo qué": "What's up? (very informal)",
                "manito/manita": "Bro/sis",
                "tigueraje": "Street smarts"
            }
        },
        
        "real_life_scenarios": {
            "banking": {
                "main_banks": ["Banco Popular", "Banreservas", "Scotiabank"],
                "tips": "USD accepted in tourist areas. ATMs everywhere."
            },
            "immigration": {
                "tips": "Residency relatively easy. Many visa options."
            },
            "healthcare": {
                "emergency": "911",
                "tips": "Good private healthcare in Santo Domingo and Punta Cana"
            },
            "schools": {
                "international": ["Carol Morgan School", "AISK"],
                "tips": "American and international curriculum options"
            }
        },
        
        "cultural_notes": {
            "music": "Bachata and merengue - national pride",
            "baseball": "National passion - MLB players everywhere",
            "zona_colonial": "Historic district in Santo Domingo, UNESCO site"
        }
    },
    
    Country.EQUATORIAL_GUINEA: {
        "name": "Guinea Ecuatorial",
        "flag": "🇬🇶",
        "currency": "CFA Franc (XAF)",
        "timezone": "WAT (UTC+1)",
        "spanish_variant": "equatorial_guinean",
        
        "local_vocabulary": {
            "note": "Spanish is official but French and Portuguese also spoken"
        },
        
        "real_life_scenarios": {
            "tips": "Oil-rich nation. Limited infrastructure for expats."
        },
        
        "cultural_notes": {
            "unique": "Only Spanish-speaking country in Africa",
            "oil": "Oil industry attracts some expats"
        }
    }
}


# =============================================================================
# REAL-LIFE SITUATION CATEGORIES
# =============================================================================

REAL_LIFE_SITUATIONS = {
    "emergency": {
        "icon": "🚨",
        "phrases": {
            "help": {
                "es": "¡Ayuda!",
                "en": "Help!"
            },
            "call_police": {
                "es": "¡Llame a la policía!",
                "en": "Call the police!"
            },
            "hospital": {
                "es": "Necesito ir al hospital",
                "en": "I need to go to the hospital"
            },
            "accident": {
                "es": "Hubo un accidente",
                "en": "There was an accident"
            }
        }
    },
    
    "healthcare": {
        "icon": "🏥",
        "phrases": {
            "appointment": {
                "es": "Necesito una cita con el doctor",
                "en": "I need an appointment with the doctor"
            },
            "allergy": {
                "es": "Soy alérgico/a a...",
                "en": "I'm allergic to..."
            },
            "prescription": {
                "es": "Necesito esta medicina",
                "en": "I need this medicine"
            },
            "pain": {
                "es": "Me duele aquí",
                "en": "It hurts here"
            },
            "pharmacy": {
                "es": "¿Tienen [medicine]?",
                "en": "Do you have [medicine]?"
            }
        }
    },
    
    "banking": {
        "icon": "🏦",
        "phrases": {
            "account": {
                "es": "Quiero abrir una cuenta",
                "en": "I want to open an account"
            },
            "transfer": {
                "es": "Necesito hacer una transferencia",
                "en": "I need to make a transfer"
            },
            "card_problem": {
                "es": "Mi tarjeta no funciona",
                "en": "My card doesn't work"
            },
            "statement": {
                "es": "Necesito un estado de cuenta",
                "en": "I need a bank statement"
            }
        }
    },
    
    "immigration": {
        "icon": "🛂",
        "phrases": {
            "visa": {
                "es": "Necesito información sobre visas",
                "en": "I need information about visas"
            },
            "extend": {
                "es": "Quiero extender mi estadía",
                "en": "I want to extend my stay"
            },
            "residency": {
                "es": "Quiero solicitar residencia",
                "en": "I want to apply for residency"
            },
            "documents": {
                "es": "¿Qué documentos necesito?",
                "en": "What documents do I need?"
            }
        }
    },
    
    "school": {
        "icon": "🏫",
        "phrases": {
            "enroll": {
                "es": "Quiero inscribir a mi hijo/a",
                "en": "I want to enroll my child"
            },
            "meeting": {
                "es": "Tengo reunión con el maestro/a",
                "en": "I have a meeting with the teacher"
            },
            "homework": {
                "es": "Mi hijo tiene tarea",
                "en": "My child has homework"
            },
            "problem": {
                "es": "Mi hijo tiene problemas en la escuela",
                "en": "My child is having problems at school"
            }
        }
    },
    
    "restaurant": {
        "icon": "🍽️",
        "phrases": {
            "table": {
                "es": "Una mesa para [number] personas",
                "en": "A table for [number] people"
            },
            "menu": {
                "es": "¿Tienen menú en inglés?",
                "en": "Do you have a menu in English?"
            },
            "allergy": {
                "es": "No puedo comer [food], soy alérgico/a",
                "en": "I can't eat [food], I'm allergic"
            },
            "bill": {
                "es": "La cuenta, por favor",
                "en": "The bill, please"
            },
            "tip": {
                "es": "¿El servicio está incluido?",
                "en": "Is service included?"
            }
        }
    },
    
    "transportation": {
        "icon": "🚗",
        "phrases": {
            "taxi": {
                "es": "¿Cuánto cuesta ir a...?",
                "en": "How much to go to...?"
            },
            "bus": {
                "es": "¿Este bus va a...?",
                "en": "Does this bus go to...?"
            },
            "directions": {
                "es": "¿Dónde está...?",
                "en": "Where is...?"
            },
            "stop": {
                "es": "¡Pare aquí, por favor!",
                "en": "Stop here, please!"
            }
        }
    },
    
    "shopping": {
        "icon": "🛒",
        "phrases": {
            "price": {
                "es": "¿Cuánto cuesta?",
                "en": "How much is it?"
            },
            "find": {
                "es": "¿Dónde encuentro...?",
                "en": "Where do I find...?"
            },
            "size": {
                "es": "¿Tienen en otra talla/tamaño?",
                "en": "Do you have in another size?"
            },
            "pay": {
                "es": "¿Aceptan tarjeta?",
                "en": "Do you accept cards?"
            }
        }
    },
    
    "housing": {
        "icon": "🏠",
        "phrases": {
            "rent": {
                "es": "Busco apartamento para alquilar",
                "en": "I'm looking for an apartment to rent"
            },
            "broken": {
                "es": "Se dañó [thing], necesito reparación",
                "en": "[Thing] broke, I need repair"
            },
            "plumber": {
                "es": "Necesito un plomero",
                "en": "I need a plumber"
            },
            "electrician": {
                "es": "Necesito un electricista",
                "en": "I need an electrician"
            }
        }
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_country_context(country: Country) -> Dict:
    """Get full context for a country."""
    return COUNTRY_CONTEXTS.get(country, {})


def get_country_vocabulary(country: Country) -> Dict:
    """Get local vocabulary for a country."""
    context = COUNTRY_CONTEXTS.get(country, {})
    return context.get("local_vocabulary", {})


def get_country_scenarios(country: Country, category: str = None) -> Dict:
    """Get real-life scenarios for a country."""
    context = COUNTRY_CONTEXTS.get(country, {})
    scenarios = context.get("real_life_scenarios", {})
    
    if category:
        return scenarios.get(category, {})
    return scenarios


def get_situation_phrases(situation: str, language: str = "both") -> Dict:
    """Get phrases for a real-life situation."""
    situation_data = REAL_LIFE_SITUATIONS.get(situation, {})
    phrases = situation_data.get("phrases", {})
    
    if language == "both":
        return phrases
    elif language in ["es", "en"]:
        return {key: val.get(language) for key, val in phrases.items()}
    return phrases


def detect_country_from_context(text: str) -> Optional[Country]:
    """Detect which country user might be referring to."""
    text_lower = text.lower()
    
    country_keywords = {
        Country.PANAMA: ["panama", "panamá", "panama city", "casco viejo", "balboa"],
        Country.MEXICO: ["mexico", "méxico", "cdmx", "ciudad de mexico"],
        Country.COLOMBIA: ["colombia", "bogota", "bogotá", "medellin", "medellín"],
        Country.ARGENTINA: ["argentina", "buenos aires", "argentina peso"],
        Country.SPAIN: ["españa", "spain", "madrid", "barcelona"],
        Country.COSTA_RICA: ["costa rica", "san jose", "san josé", "pura vida"],
        Country.PERU: ["peru", "perú", "lima"],
        Country.CHILE: ["chile", "santiago"],
        Country.ECUADOR: ["ecuador", "quito", "guayaquil"]
    }
    
    for country, keywords in country_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return country
    
    return None


def get_urgent_phrases(situation: str, country: Country = None) -> Dict:
    """Get urgent/emergency phrases for immediate help."""
    base_phrases = REAL_LIFE_SITUATIONS.get(situation, {}).get("phrases", {})
    
    result = {
        "phrases": base_phrases,
        "emergency_numbers": {}
    }
    
    if country:
        context = COUNTRY_CONTEXTS.get(country, {})
        if "real_life_scenarios" in context and "healthcare" in context["real_life_scenarios"]:
            result["emergency_numbers"]["emergency"] = context["real_life_scenarios"]["healthcare"].get("emergency", "911")
    
    return result


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🌎 EspaLuz Country Contexts - Test")
    print("=" * 60)
    
    # Test Panama context
    print("\n🇵🇦 Panama Context:")
    panama = get_country_context(Country.PANAMA)
    print(f"  Currency: {panama['currency']}")
    print(f"  Banking phrases: {list(panama['real_life_scenarios']['banking']['phrases'].keys())}")
    
    # Test vocabulary
    print("\n📚 Panama Local Vocabulary:")
    vocab = get_country_vocabulary(Country.PANAMA)
    for word, meaning in list(vocab.get("expressions", {}).items())[:3]:
        print(f"  {word}: {meaning}")
    
    # Test situation phrases
    print("\n🏥 Healthcare Phrases:")
    phrases = get_situation_phrases("healthcare")
    for key, translations in list(phrases.items())[:2]:
        print(f"  {translations['en']} = {translations['es']}")
    
    # Test country detection
    print("\n🔍 Country Detection:")
    tests = ["I'm moving to Panama City", "Vivo en Colombia", "Buenos Aires es hermosa"]
    for test in tests:
        detected = detect_country_from_context(test)
        print(f"  '{test}' → {detected.value if detected else 'None'}")
    
    print("\n✅ All tests completed!")
