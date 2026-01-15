#!/usr/bin/env python3
"""
EspaLuz Telegram Admin Dashboard
Web-based admin interface for managing users, trials, and subscriptions
"""

from flask import Flask, render_template_string, request, jsonify, redirect
import json
import os
from datetime import datetime, timedelta
import logging

# Import our systems
try:
    from espaluz_paypal_system import paypal_system
except ImportError:
    paypal_system = None

# HTML Templates
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>EspaLuz Telegram Admin</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.05); 
            padding: 30px; 
            border-radius: 20px; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 { 
            color: #00d9ff; 
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        h2 { 
            color: #ffd700; 
            border-bottom: 2px solid rgba(255,215,0,0.3);
            padding-bottom: 10px;
            margin-top: 30px;
        }
        .subtitle { color: #888; margin-bottom: 30px; }
        
        /* Stats Grid */
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
            gap: 20px; 
            margin: 25px 0; 
        }
        .stat-card { 
            background: linear-gradient(145deg, rgba(0,217,255,0.1), rgba(0,217,255,0.05));
            padding: 20px; 
            border-radius: 15px; 
            text-align: center; 
            border: 1px solid rgba(0,217,255,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,217,255,0.2);
        }
        .stat-number { 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #00d9ff; 
        }
        .stat-label { 
            color: #888; 
            margin-top: 5px; 
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Tables */
        .users-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0; 
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            overflow: hidden;
        }
        .users-table th, .users-table td { 
            padding: 15px; 
            text-align: left; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
        }
        .users-table th { 
            background: rgba(0,217,255,0.1); 
            font-weight: bold; 
            color: #00d9ff;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }
        .users-table tr:hover {
            background: rgba(255,255,255,0.05);
        }
        
        /* Status badges */
        .status-active { 
            color: #00ff88; 
            font-weight: bold;
            padding: 5px 10px;
            background: rgba(0,255,136,0.1);
            border-radius: 20px;
        }
        .status-trial { 
            color: #ffd700; 
            font-weight: bold;
            padding: 5px 10px;
            background: rgba(255,215,0,0.1);
            border-radius: 20px;
        }
        .status-expired { 
            color: #ff4757; 
            font-weight: bold;
            padding: 5px 10px;
            background: rgba(255,71,87,0.1);
            border-radius: 20px;
        }
        
        /* Buttons */
        .btn { 
            padding: 10px 20px; 
            margin: 5px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            text-decoration: none; 
            display: inline-block;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn-primary { 
            background: linear-gradient(135deg, #00d9ff, #0099cc); 
            color: white; 
        }
        .btn-primary:hover { 
            background: linear-gradient(135deg, #00b8d4, #0077aa);
            transform: translateY(-2px);
        }
        .btn-success { 
            background: linear-gradient(135deg, #00ff88, #00cc6a); 
            color: #1a1a2e; 
        }
        .btn-warning { 
            background: linear-gradient(135deg, #ffd700, #ccac00); 
            color: #1a1a2e; 
        }
        .btn-danger { 
            background: linear-gradient(135deg, #ff4757, #cc3945); 
            color: white; 
        }
        .btn-sm { padding: 6px 12px; font-size: 0.85em; }
        
        /* Forms */
        .form-group { margin: 15px 0; }
        .form-group input, .form-group select { 
            padding: 12px 15px; 
            margin: 5px; 
            border: 1px solid rgba(255,255,255,0.2); 
            border-radius: 8px;
            background: rgba(0,0,0,0.3);
            color: #e0e0e0;
            font-size: 1em;
        }
        .form-group input:focus {
            outline: none;
            border-color: #00d9ff;
            box-shadow: 0 0 10px rgba(0,217,255,0.3);
        }
        
        /* Alerts */
        .alert { 
            padding: 20px; 
            margin: 20px 0; 
            border-radius: 10px;
            border-left: 4px solid;
        }
        .alert-info { 
            background: rgba(0,217,255,0.1); 
            border-color: #00d9ff;
            color: #00d9ff;
        }
        .alert-success {
            background: rgba(0,255,136,0.1);
            border-color: #00ff88;
            color: #00ff88;
        }
        
        /* User ID styling */
        .user-id { 
            font-family: 'Courier New', monospace; 
            background: rgba(0,0,0,0.3); 
            padding: 4px 8px; 
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        /* Actions bar */
        .actions { 
            margin: 20px 0; 
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
        
        /* Links */
        a { color: #00d9ff; }
        a:hover { color: #00b8d4; }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 EspaLuz Telegram Admin</h1>
        <p class="subtitle">Manage your AI Spanish tutor subscribers and trials</p>
        
        <div class="actions">
            <a href="/admin" class="btn btn-primary">🔄 Refresh</a>
            <a href="/admin/export" class="btn btn-warning">📤 Export Data</a>
        </div>

        <!-- Statistics -->
        <h2>📊 Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_users }}</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_trials }}</div>
                <div class="stat-label">Active Trials</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.expired_trials }}</div>
                <div class="stat-label">Expired Trials</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_subscriptions }}</div>
                <div class="stat-label">Paid Subscribers</div>
            </div>
        </div>

        <!-- Trial Users -->
        <h2>👥 Trial Users</h2>
        <table class="users-table">
            <thead>
                <tr>
                    <th>User ID</th>
                    <th>Status</th>
                    <th>Days Left</th>
                    <th>Messages</th>
                    <th>Trial End</th>
                    <th>Org Code</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for user in trials %}
                <tr>
                    <td><span class="user-id">{{ user.user_id[:15] }}{% if user.user_id|length > 15 %}...{% endif %}</span></td>
                    <td>
                        {% if user.is_active %}
                            <span class="status-trial">🟡 Trial</span>
                        {% else %}
                            <span class="status-expired">🔴 Expired</span>
                        {% endif %}
                    </td>
                    <td>{{ user.days_remaining }}</td>
                    <td>{{ user.messages_sent }}</td>
                    <td>{{ user.trial_end_formatted }}</td>
                    <td>{{ user.org_code or '-' }}</td>
                    <td>
                        <a href="/admin/extend/{{ user.user_id }}" class="btn btn-success btn-sm">➕ +7 days</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- Subscribers -->
        <h2>💳 Paid Subscribers</h2>
        <table class="users-table">
            <thead>
                <tr>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Telegram ID</th>
                    <th>Source</th>
                    <th>Last Updated</th>
                </tr>
            </thead>
            <tbody>
                {% for sub in subscribers %}
                <tr>
                    <td>{{ sub.email }}</td>
                    <td>
                        {% if sub.status == 'active' %}
                            <span class="status-active">🟢 Active</span>
                        {% else %}
                            <span class="status-expired">🔴 {{ sub.status }}</span>
                        {% endif %}
                    </td>
                    <td><span class="user-id">{{ sub.telegram_id or 'Not linked' }}</span></td>
                    <td>{{ sub.source }}</td>
                    <td>{{ sub.last_updated }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- Quick Actions -->
        <h2>⚡ Quick Actions</h2>
        <div class="form-group">
            <form action="/admin/extend-user" method="post" style="display: inline-block;">
                <input type="text" name="user_id" placeholder="Telegram User ID" required>
                <input type="number" name="days" placeholder="Days" value="7" min="1" max="30" required>
                <button type="submit" class="btn btn-success">Extend Trial</button>
            </form>
        </div>

        <div class="form-group">
            <form action="/admin/add-subscriber" method="post" style="display: inline-block;">
                <input type="email" name="email" placeholder="PayPal Email" required>
                <input type="text" name="subscription_id" placeholder="Subscription ID (optional)">
                <button type="submit" class="btn btn-primary">Add Subscriber</button>
            </form>
        </div>

        <!-- Subscription Links -->
        <h2>🔗 Subscription Links</h2>
        <div class="alert alert-info">
            <strong>PayPal:</strong> 
            <a href="https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-6GR95409C95293139NFSBJJY" target="_blank">
                https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-6GR95409C95293139NFSBJJY
            </a>
        </div>

        <div class="footer">
            <p>Last updated: {{ current_time }} | EspaLuz Admin v1.0</p>
        </div>
    </div>
</body>
</html>
'''

SUCCESS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Success - EspaLuz Admin</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #e0e0e0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .card {
            background: rgba(255,255,255,0.05);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            border: 1px solid rgba(0,255,136,0.3);
        }
        h1 { color: #00ff88; }
        a { 
            color: #00d9ff; 
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: rgba(0,217,255,0.1);
            border-radius: 8px;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>✅ {{ title }}</h1>
        <p>{{ message }}</p>
        <a href="/admin">← Back to Dashboard</a>
    </div>
</body>
</html>
'''


def create_admin_app():
    """Create Flask app with admin routes"""
    admin_app = Flask(__name__)
    
    @admin_app.route('/admin')
    def admin_dashboard():
        """Main admin dashboard"""
        try:
            if not paypal_system:
                return "PayPal system not initialized", 500
            
            # Get statistics
            stats = paypal_system.get_stats()
            
            # Get trial users
            trials_data = paypal_system.get_all_trials()
            trials = []
            now = datetime.now()
            
            for user_id, data in trials_data.items():
                trial_end = datetime.fromisoformat(data["trial_end"])
                days_remaining = max(0, (trial_end - now).days)
                is_active = now < trial_end and data.get("status") == "active"
                
                trials.append({
                    'user_id': user_id,
                    'is_active': is_active,
                    'days_remaining': days_remaining,
                    'messages_sent': data.get('messages_sent', 0),
                    'trial_end_formatted': trial_end.strftime('%Y-%m-%d %H:%M'),
                    'org_code': data.get('org_code')
                })
            
            # Sort by activity
            trials.sort(key=lambda x: (not x['is_active'], -x['days_remaining']))
            
            # Get subscribers
            subscribers_data = paypal_system.get_all_subscribers()
            subscribers = []
            
            for email, data in subscribers_data.items():
                subscribers.append({
                    'email': email,
                    'status': data.get('status', 'unknown'),
                    'telegram_id': data.get('telegram_id'),
                    'source': data.get('source', 'unknown'),
                    'last_updated': data.get('last_updated', 'unknown')[:10] if data.get('last_updated') else '-'
                })
            
            return render_template_string(
                ADMIN_TEMPLATE,
                stats=stats,
                trials=trials,
                subscribers=subscribers,
                current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except Exception as e:
            logging.error(f"Admin dashboard error: {e}")
            return f"Error loading dashboard: {e}", 500
    
    @admin_app.route('/admin/extend/<user_id>')
    def extend_trial_quick(user_id):
        """Quick extend trial by 7 days"""
        try:
            success = paypal_system.extend_trial(user_id, 7)
            if success:
                return render_template_string(
                    SUCCESS_TEMPLATE,
                    title="Trial Extended",
                    message=f"Extended trial for {user_id} by 7 days"
                )
            else:
                return render_template_string(
                    SUCCESS_TEMPLATE,
                    title="Extension Failed",
                    message=f"Could not extend trial for {user_id}. User may not exist."
                )
        except Exception as e:
            return f"Error: {e}", 500
    
    @admin_app.route('/admin/extend-user', methods=['POST'])
    def extend_trial_custom():
        """Extend trial with custom days"""
        try:
            user_id = request.form.get('user_id')
            days = int(request.form.get('days', 7))
            
            success = paypal_system.extend_trial(user_id, days)
            if success:
                return render_template_string(
                    SUCCESS_TEMPLATE,
                    title="Trial Extended",
                    message=f"Extended trial for {user_id} by {days} days"
                )
            else:
                return render_template_string(
                    SUCCESS_TEMPLATE,
                    title="Extension Failed",
                    message=f"Could not extend trial for {user_id}"
                )
        except Exception as e:
            return f"Error: {e}", 500
    
    @admin_app.route('/admin/add-subscriber', methods=['POST'])
    def add_subscriber():
        """Manually add a subscriber"""
        try:
            email = request.form.get('email')
            subscription_id = request.form.get('subscription_id')
            
            success = paypal_system.add_subscriber_manually(email, subscription_id)
            if success:
                return render_template_string(
                    SUCCESS_TEMPLATE,
                    title="Subscriber Added",
                    message=f"Added {email} as active subscriber"
                )
            else:
                return render_template_string(
                    SUCCESS_TEMPLATE,
                    title="Add Failed",
                    message=f"Could not add subscriber {email}"
                )
        except Exception as e:
            return f"Error: {e}", 500
    
    @admin_app.route('/admin/export')
    def export_data():
        """Export all data as JSON"""
        try:
            data = {
                "stats": paypal_system.get_stats(),
                "trials": paypal_system.get_all_trials(),
                "subscribers": paypal_system.get_all_subscribers(),
                "exported_at": datetime.now().isoformat()
            }
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @admin_app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "EspaLuz Telegram Admin",
            "timestamp": datetime.now().isoformat()
        })
    
    return admin_app


# Global admin app instance
admin_app = create_admin_app()


if __name__ == "__main__":
    # Run standalone for testing
    admin_app.run(debug=True, port=5003, host='0.0.0.0')
