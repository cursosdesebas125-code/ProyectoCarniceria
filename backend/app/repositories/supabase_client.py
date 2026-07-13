from supabase import create_client, Client
from app.config.settings import settings


class SupabaseClientManager:
    """
    Manages the lifecycle and initialization of the Supabase client.
    Ensures a single database connection client is shared or initialized properly.
    """
    def __init__(self):
        # Force environment variables cleaning to strip any outer quotes or trailing whitespaces
        url = settings.supabase_url.strip().strip("'").strip('"')
        if url.endswith("/rest/v1/"):
            url = url[:-9]
        elif url.endswith("/rest/v1"):
            url = url[:-8]
        key = settings.supabase_key.strip().strip("'").strip('"')

        self._client: Client = create_client(
            supabase_url=url,
            supabase_key=key
        )

    def get_client(self) -> Client:
        """
        Returns the active Supabase client instance.
        """
        return self._client


# Singleton manager instance
supabase_manager = SupabaseClientManager()


def get_supabase_client() -> Client:
    """
    Dependency or helper to access the Supabase client.
    """
    return supabase_manager.get_client()
