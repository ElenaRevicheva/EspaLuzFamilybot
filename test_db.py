import espaluz_database as db
print('Database available:', db.db.use_database)
print('Database URL:', db.db.database_url[:50] if db.db.database_url else 'None')
result = db.track_user('TEST_USER_123', username='test_user', first_name='Test')
print('Track user result:', result)
