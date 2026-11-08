# Stand-In Meeting Agent (Fetch.ai Agentverse / ASI:One)

An agent people, or other agents, can hire for two meeting jobs. It speaks the Chat Protocol.

- **Prepare** (before a meeting): send the agenda, who you are and your notes. It replies with a briefing, likely questions with short answers drawn only from your material (anything missing is marked "Needs your input"), and an "About you" text for the Stand-In Chrome extension.
- **Follow up** (after a meeting): send the transcript or captions. It replies with a summary, decisions, open questions and action items with owners.

It does not join calls. To have an AI delegate speak for you in Google Meet, use the Stand-In Chrome extension in this repo. Everything the agent writes is a draft to check.

## Run it

```
cd apps/agent
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
set AGENT_SEED=<a long secret phrase>     # fixes the agent's address; keep it private
set GEMINI_API_KEY=<your key>             # free at aistudio.google.com
python agent.py
```

Then open the **Inspector** link it prints and choose **Connect → Mailbox**. In Agentverse, open the agent, fill in its README/description (copy the paragraph above) so people can find it, and test it from ASI:One chat.

Tests (no network): `python -m unittest`

Data: the text a person sends is forwarded to Google Gemini to write the reply, and is not stored by the agent. Each sender is limited to 10 requests per hour.
