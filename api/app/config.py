import os

WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")
GIT_SHA = os.getenv("RENDER_GIT_COMMIT", "dev")[:7]
