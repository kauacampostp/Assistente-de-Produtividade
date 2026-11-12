import os
from pathlib import Path

import httpx2
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mcp import Client, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

GOOGLE_CALENDAR_URL = "https://calendarmcp.googleapis.com/mcp/v1"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "https://www.googleapis.com/auth/calendar.events.freebusy",
    "https://www.googleapis.com/auth/calendar.events.readonly",
]

# Caminho raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

TOKEN_FILE = PROJECT_ROOT / "mcp_servers" / "google_calendar" / "token.json"


# Configuração do servidor MCP de arquivos
def local_files_server():
    return StdioServerParameters(
        command="/usr/bin/python",
        args=[str(PROJECT_ROOT / "mcp_servers" / "local_files" / "server.py")],
        env=os.environ.copy(),
    )


# Configuração do servidor MCP do Todoist
def todoist_server():
    return StdioServerParameters(
        command="npx",
        args=["-y", "mcp-remote", "https://ai.todoist.net/mcp"],
        env=os.environ.copy(),
    )


# Lista as ferramentas disponíveis no servidor
async def list_mcp_tools(server):
    async with Client(server) as client:
        result = await client.list_tools()
        return result.tools


# Executa uma ferramenta do servidor
async def call_mcp_tool(server, tool_name: str, arguments: dict | None = None):
    async with Client(server) as client:
        result = await client.call_tool(tool_name, arguments or {})

        if getattr(result, "isError", False):
            raise RuntimeError(f"Erro ao executar ferramenta: {tool_name}")

        return result.content


def get_google_credentials():
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:3334/"],
            }
        }

        flow = InstalledAppFlow.from_client_config(
            client_config,
            scopes=SCOPES,
        )

        flow.run_local_server(
            host="localhost",
            port=3334,
            open_browser=True,
            access_type="offline",
            prompt="consent",
        )

        credentials = flow.credentials

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    TOKEN_FILE.write_text(credentials.to_json())

    return credentials


async def call_google_calendar_tool(
    tool_name: str,
    arguments: dict | None = None,
):
    credentials = get_google_credentials()

    async with httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(
            GOOGLE_CALENDAR_URL,
            http_client=http_client,
        )

        async with Client(transport) as client:
            result = await client.call_tool(
                tool_name,
                arguments or {},
            )

            if getattr(result, "isError", False):
                raise RuntimeError(f"Erro ao executar ferramenta: {tool_name}")

            return result.content


async def list_google_calendar_tools():
    credentials = get_google_credentials()

    async with httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {credentials.token}"},
        timeout=httpx2.Timeout(30.0, read=300.0),
    ) as http_client:
        transport = streamable_http_client(
            GOOGLE_CALENDAR_URL,
            http_client=http_client,
        )

        async with Client(transport) as client:
            result = await client.list_tools()
            return result.tools


def list_calendar_events(max_results=10):
    credentials = get_google_credentials()

    service = build("calendar", "v3", credentials=credentials)

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    return result.get("items", [])
