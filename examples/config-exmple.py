##############################
# For SECRET_KEY
# >> import secrets
# >> secrets.token_urlsafe(24)
# Copy output to SECRET_KEY
##############################

class Config(object):
  DEBUG = False
  TESTING = False
  SECRET_KEY = "Some_Secret_String_Here"

class ProductionConfig(Config):
  pass

class DevelopmentConfig(Config):
  DEBUG = True

class TestingConfig(Config):
  TESTING = True