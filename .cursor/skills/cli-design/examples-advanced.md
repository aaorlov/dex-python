# Advanced Examples

## Agent Chat with LangGraph Orchestration

Complex agent with state machine, tool calls, and human-in-the-loop interrupts.

### Agent Core (platform-agnostic)

```python
# packages/agent-core/src/agent_core/graph.py
from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    status: str


model = ChatAnthropic(model="claude-sonnet-4-20250514")


async def call_model(state: AgentState) -> dict:
    response = await model.ainvoke(state["messages"])
    return {"messages": [response], "status": "responded"}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


async def execute_tools(state: AgentState) -> dict:
    return {"messages": [], "status": "tools_executed"}


def create_agent():
    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", execute_tools)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    return graph.compile()
```

### CLI Command wrapping LangGraph agent

```python
# packages/client-cli/src/client_cli/commands/agent_chat.py
import asyncio

import typer
from rich.console import Console
from rich.prompt import Prompt

from agent_core.graph import create_agent

app = typer.Typer(help="LangGraph agent chat")
console = Console()


async def _agent_loop():
    console.rule("[bold cyan]Agent Active[/]")
    agent = create_agent()
    messages = []

    while True:
        user_input = Prompt.ask("[bold]You[/]")
        if not user_input or user_input.strip() == "exit":
            break

        messages.append({"role": "user", "content": user_input})

        with console.status("Thinking..."):
            result = await agent.ainvoke({"messages": messages, "status": "pending"})

        last = result["messages"][-1]
        console.print(f"\n[cyan]  {last.content}[/]\n")
        messages = result["messages"]


@app.callback(invoke_without_command=True)
def agent_chat():
    asyncio.run(_agent_loop())
    console.print("[dim]Session closed.[/]")
```

---

## Streaming Chat with Textual TUI

Rich, dashboard-style terminal interface with real-time streaming.
Use `textual` when you need a stateful, component-driven terminal UI.

```python
# src/my_cli/ui/chat_app.py
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input, Static
from pydantic_ai import Agent


class MessageBubble(Static):
    def __init__(self, role: str, content: str) -> None:
        super().__init__(content)
        self.add_class(role)


class ChatApp(App):
    CSS = """
    .user {
        background: $primary-darken-2;
        color: $text;
        margin: 1 4 0 10;
        padding: 1 2;
    }
    .assistant {
        background: $surface;
        color: $text;
        margin: 1 10 0 4;
        padding: 1 2;
    }
    #chat-view {
        height: 1fr;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, model: str = "anthropic:claude-sonnet-4-20250514"):
        super().__init__()
        self.agent = Agent(model, system_prompt="You are a helpful assistant.")
        self.message_history: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="chat-view")
        yield Input(placeholder="Type a message... (Ctrl+C to quit)")
        yield Footer()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if not event.value.strip():
            return
        user_text = event.value
        event.input.clear()
        chat = self.query_one("#chat-view", VerticalScroll)
        chat.mount(MessageBubble("user", user_text))
        self._run_agent(user_text)

    @work(thread=True)
    async def _run_agent(self, user_text: str) -> None:
        result = await self.agent.run(
            user_text,
            message_history=self.message_history,
        )
        self.message_history = result.all_messages()
        chat = self.query_one("#chat-view", VerticalScroll)
        self.call_from_thread(
            chat.mount, MessageBubble("assistant", result.output)
        )


def start_chat(model: str) -> None:
    app = ChatApp(model=model)
    app.run()
```

### Registering Textual TUI from a Typer command

```python
# src/my_cli/commands/tui_chat.py
import typer

from my_cli.ui.chat_app import start_chat

app = typer.Typer(help="Rich terminal chat UI")


@app.callback(invoke_without_command=True)
def tui(
    model: str = typer.Option(
        "anthropic:claude-sonnet-4-20250514", "--model", "-m", help="Model ID"
    ),
):
    start_chat(model)
```

---

## pydantic-ai Agent with Structured Output and Tools

Type-safe agent returning Pydantic models with tool calling.

```python
# packages/agent-core/src/agent_core/analyst.py
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext


class AnalysisResult(BaseModel):
    summary: str
    confidence: float
    recommendations: list[str]


class AnalysisDeps(BaseModel):
    api_key: str
    database_url: str


agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    deps_type=AnalysisDeps,
    output_type=AnalysisResult,
    system_prompt="You are a data analyst. Provide structured analysis.",
)


@agent.tool
async def query_database(ctx: RunContext[AnalysisDeps], sql: str) -> str:
    """Execute a read-only SQL query against the analytics database."""
    from sqlmodel import Session, create_engine, text

    engine = create_engine(ctx.deps.database_url)
    with Session(engine) as session:
        rows = session.exec(text(sql)).all()
        return str([dict(r._mapping) for r in rows])


@agent.tool
async def fetch_external_data(ctx: RunContext[AnalysisDeps], endpoint: str) -> str:
    """Fetch data from an external API."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            endpoint, headers={"Authorization": f"Bearer {ctx.deps.api_key}"}
        )
        resp.raise_for_status()
        return resp.text
```

### Using the agent from CLI

```python
# packages/client-cli/src/client_cli/commands/analyze.py
import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent_core.analyst import AnalysisDeps, AnalysisResult, agent

app = typer.Typer(help="Data analysis commands")
console = Console()


async def _analyze(query: str, deps: AnalysisDeps) -> AnalysisResult:
    result = await agent.run(query, deps=deps)
    return result.output


@app.callback(invoke_without_command=True)
def analyze(
    query: str = typer.Argument(..., help="Analysis question"),
    api_key: str = typer.Option(..., envvar="API_KEY"),
    database_url: str = typer.Option(..., envvar="DATABASE_URL"),
):
    deps = AnalysisDeps(api_key=api_key, database_url=database_url)

    with console.status("Analyzing..."):
        result = asyncio.run(_analyze(query, deps))

    console.print(Panel(result.summary, title="Summary", border_style="cyan"))
    console.print(f"\n[bold]Confidence:[/] {result.confidence:.0%}\n")

    table = Table(title="Recommendations")
    table.add_column("#", style="dim")
    table.add_column("Recommendation")
    for i, rec in enumerate(result.recommendations, 1):
        table.add_row(str(i), rec)
    console.print(table)
```
