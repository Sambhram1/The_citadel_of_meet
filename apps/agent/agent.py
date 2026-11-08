"""Stand-In Meeting Agent for Fetch.ai Agentverse / ASI:One (speaks the Chat Protocol).

Run locally with a mailbox so Agentverse can reach it:
    set AGENT_SEED=<a long secret phrase>      (keeps the agent's address stable)
    set GEMINI_API_KEY=<your Gemini key>
    python agent.py
Then open the Inspector link it prints and choose Connect -> Mailbox.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from stand_in_logic import RateLimiter, respond

SEED = os.environ.get("AGENT_SEED", "")
API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("TEXT_MODEL", "gemini-2.5-flash")
if not SEED:
    raise SystemExit("Set AGENT_SEED to a long secret phrase (it fixes the agent's address).")
if not API_KEY:
    raise SystemExit("Set GEMINI_API_KEY (free at aistudio.google.com).")

agent = Agent(
    name="stand-in-meeting-agent",
    seed=SEED,
    port=int(os.environ.get("AGENT_PORT", "8000")),
    mailbox=True,
    publish_agent_details=True,
)
chat = Protocol(spec=chat_protocol_spec)
limiter = RateLimiter()


def _reply(text: str, end: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=content)


@chat.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage) -> None:
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
    if not text:
        return
    if not limiter.allow(sender):
        await ctx.send(sender, _reply("You've reached the hourly limit. Please try again later."))
        return
    ctx.logger.info("job from %s (%d chars)", sender, len(text))
    # The Gemini call blocks, so run it off the event loop.
    answer = await asyncio.to_thread(respond, text, API_KEY, MODEL)
    await ctx.send(sender, _reply(answer))


@chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
    ctx.logger.info("ack from %s for %s", sender, msg.acknowledged_msg_id)


agent.include(chat, publish_manifest=True)


@agent.on_event("startup")
async def started(ctx: Context) -> None:
    ctx.logger.info("Stand-In Meeting Agent address: %s", agent.address)


if __name__ == "__main__":
    agent.run()
