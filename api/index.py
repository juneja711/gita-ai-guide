import os
import sys

# Ensure root directory is added to sys.path for Vercel serverless environment
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel ASGI path restoration middleware
class FixVercelPathMiddleware:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            # Vercel provides original requested path in x-matched-path or x-invoke-path
            orig_path = (
                headers.get(b"x-matched-path", b"")
                or headers.get(b"x-invoke-path", b"")
                or headers.get(b"x-vercel-matched-path", b"")
            ).decode("utf-8")
            if orig_path:
                scope["path"] = orig_path
        await self.asgi_app(scope, receive, send)

# Export for Vercel
app = FixVercelPathMiddleware(app)
