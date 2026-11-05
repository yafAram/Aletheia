from desktop_agent.config import get_agent_settings
from desktop_agent.service import app
import uvicorn

if __name__ == "__main__":
    settings = get_agent_settings()
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
