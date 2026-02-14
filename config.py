import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'SecretKey123456789'