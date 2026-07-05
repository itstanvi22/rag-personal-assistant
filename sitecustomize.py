import os
import sys

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if os.path.isdir(backend_dir) and backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
