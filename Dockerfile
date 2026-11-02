FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AGENT_REACH_DISCOVERY_DB=/data/discovery.db

RUN useradd --create-home --uid 10001 reach && mkdir /data && chown reach /data
WORKDIR /app
COPY pyproject.toml README.md constraints.txt ./
COPY agent_reach ./agent_reach
COPY skills ./skills
RUN pip install --no-cache-dir . 

USER reach
VOLUME ["/data"]
# The MCP server speaks stdio. Run it with: docker run -i --rm -v reach-data:/data IMAGE
ENTRYPOINT ["agent-reach"]
CMD ["mcp"]
