import os
import sys
import urllib.parse

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
            query_str = scope.get("query_string", b"").decode("utf-8")
            parsed_query = urllib.parse.parse_qs(query_str)

            # Check if __path was passed via vercel.json rewrite
            if "__path" in parsed_query and parsed_query["__path"]:
                sub = parsed_query["__path"][0].lstrip("/")
                scope["path"] = f"/api/{sub}"
            else:
                orig_path = (
                    headers.get(b"x-forwarded-uri", b"")
                    or headers.get(b"x-original-uri", b"")
                    or headers.get(b"x-matched-path", b"")
                    or headers.get(b"x-invoke-path", b"")
                    or headers.get(b"x-vercel-matched-path", b"")
                ).decode("utf-8").split("?")[0]
                if orig_path and not orig_path.endswith("index.py"):
                    scope["path"] = orig_path

        await self.asgi_app(scope, receive, send)

# Export for Vercel
app = FixVercelPathMiddleware(app)
