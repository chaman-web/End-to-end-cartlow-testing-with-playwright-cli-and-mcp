import os

STAGING_URL = "https://stage.cartlow.com/uae/en"
PRODUCTION_URL = "https://cartlow.com/uae/en"

# Set ENV=production to run against production, defaults to staging
ENV = os.getenv("ENV", "staging")
BASE_URL = PRODUCTION_URL if ENV == "production" else STAGING_URL
