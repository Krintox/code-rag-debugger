from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client only if URL and KEY are provided
supabase: Client = None

def initialize_supabase():
    global supabase
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            # Validate URL format
            if not settings.SUPABASE_URL.startswith(('http://', 'https://')):
                logger.error(f"Invalid Supabase URL format: {settings.SUPABASE_URL}")
                return False
            
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            supabase = None
            return False
    else:
        logger.warning("Supabase URL or KEY not configured. Supabase functionality will be disabled.")
        return False

# Initialize on import
supabase_initialized = initialize_supabase()

def get_db():
    """
    Returns Supabase client for queries.
    """
    if supabase is None:
        raise Exception("Supabase client not initialized. Check your SUPABASE_URL and SUPABASE_KEY configuration.")
    return supabase