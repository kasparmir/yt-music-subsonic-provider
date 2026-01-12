import hashlib
from flask import request
from config import USERS

def verify_auth():
    """Ověření autentizace pro OpenSubsonic API"""
    username = (request.args.get('u') or request.args.get('username') or 
                request.form.get('u') or request.form.get('username'))
    token = (request.args.get('t') or request.args.get('token') or 
             request.form.get('t') or request.form.get('token'))
    salt = (request.args.get('s') or request.args.get('salt') or 
            request.form.get('s') or request.form.get('salt'))
    password = (request.args.get('p') or request.args.get('password') or 
                request.form.get('p') or request.form.get('password'))
    
    if not username or username not in USERS:
        return False
    
    user = USERS[username]
    
    if token and salt:
        expected = hashlib.md5((user['password'] + salt).encode()).hexdigest()
        return token == expected
    
    if password:
        return password == user['password']
    
    return False
