#!/usr/bin/env python3
"""Test the EspaLuz unified memory system"""
import os
import sys

# Set environment variable for database
os.environ['ESPALUZ_UNIFIED_DB_URL'] = 'postgresql://espaluz:EspaLuz2026!@localhost:5432/espaluz_unified'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from espaluz_memory import EspaLuzMemory, get_memory_for_whatsapp, get_memory_for_telegram, LANGCHAIN_AVAILABLE

print("=" * 50)
print("EspaLuz Unified Memory System Test")
print("=" * 50)

print(f"\n✓ LangChain available: {LANGCHAIN_AVAILABLE}")

# Test WhatsApp memory
print("\n--- Testing WhatsApp Memory ---")
try:
    wa_memory = get_memory_for_whatsapp()
    print(f"✅ WhatsApp memory initialized (platform: {wa_memory.platform})")
    
    # Test getting existing user
    user = wa_memory.get_or_create_user(whatsapp_id='+50761666716')
    print(f"✅ Got user: id={user.id}, whatsapp_id={user.whatsapp_id}, messages={user.total_messages}")
    
    # Test storing memory
    wa_memory.store_user_memory(user.id, 'test', 'Test memory from unified system')
    print(f"✅ Stored test memory")
    
    # Test getting context
    context = wa_memory.get_context_for_prompt(user.id)
    print(f"✅ Got context: {len(context)} characters")
    
    # Test adding to chat history
    wa_memory.add_message_to_history(user.id, 'user', 'Test message from unified system')
    wa_memory.add_message_to_history(user.id, 'assistant', 'Test response from unified system')
    print(f"✅ Added messages to chat history")
    
    # Test getting recent messages
    messages = wa_memory.get_recent_messages(user.id, limit=5)
    print(f"✅ Got {len(messages)} recent messages")
    
except Exception as e:
    print(f"❌ WhatsApp memory test failed: {e}")
    import traceback
    traceback.print_exc()

# Test Telegram memory
print("\n--- Testing Telegram Memory ---")
try:
    tg_memory = get_memory_for_telegram()
    print(f"✅ Telegram memory initialized (platform: {tg_memory.platform})")
    
    # Test getting existing user
    user = tg_memory.get_or_create_user(telegram_id='5481526862')
    print(f"✅ Got user: id={user.id}, telegram_id={user.telegram_id}, name={user.display_name}")
    
except Exception as e:
    print(f"❌ Telegram memory test failed: {e}")
    import traceback
    traceback.print_exc()

# Test LangChain memory if available
print("\n--- Testing LangChain Integration ---")
print(f"  LANGCHAIN_AVAILABLE: {LANGCHAIN_AVAILABLE}")
if LANGCHAIN_AVAILABLE:
    try:
        memory = get_memory_for_whatsapp()
        user = memory.get_or_create_user(whatsapp_id='+50761666716')
        conv_memory = memory.get_conversation_memory(user.id)
        print(f"✅ LangChain conversation memory: {type(conv_memory).__name__}")
        
        # Test adding messages via LangChain
        if hasattr(conv_memory, 'add_user_message'):
            conv_memory.add_user_message("Test via LangChain")
            conv_memory.add_ai_message("Response via LangChain")
            print(f"✅ Added messages via LangChain API")
        elif hasattr(conv_memory, 'add_message'):
            print(f"✅ Has add_message method (raw chat history)")
            
    except Exception as e:
        print(f"❌ LangChain test failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️ LangChain not available - basic mode only")

print("\n" + "=" * 50)
print("Test Complete!")
print("=" * 50)
