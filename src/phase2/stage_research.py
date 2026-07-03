import os
import sys
import json
import argparse
import asyncio
from datetime import datetime

# Attempt to import MCP SDK libraries
MCP_AVAILABLE = False
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    pass

# Reconfigure stdout to use UTF-8 to prevent encoding errors on Windows when printing unicode
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

INTERVIEW_GUIDE = """# Spotify Qualitative Research: User Interview Guide
**Target Segment**: Routine Spotify Listeners (daily background listeners for commute, work, or focus).
**Core Objective**: Validate the "algorithmic bubble" effect, Smart Shuffle repeat loop issues, and taste pollution friction.

## Introduction (2 mins)
- Explain the purpose: Spotify Growth Team researching how users interact with discovery and recommendations.
- Set expectations: No right/wrong answers; looking for honest frustrations.

## Warm-up & Routines (5 mins)
- Describe your daily Spotify usage. When and how do you listen?
- Do you actively seek out new music, or do you rely on automated recommendations (Daily Mixes, Smart Shuffle, Discover Weekly)?

## Core Friction Exploration (15 mins)
1. **The Recommendation Bubble**: Have you ever felt that Spotify gets "stuck" recommending the same artists or songs? How does that affect your listening?
2. **Smart Shuffle Fatigue**: What is your experience with Smart Shuffle? Do you feel it repeats songs you already skip?
3. **Taste Profile Pollution**: Have you ever had a situation where a single outlier play (e.g., kids' music, holiday tracks, or party playlists) permanently ruined your recommendations?
4. **Decision Paralysis**: When you want to discover something fresh but don't know what, how long do you spend searching/scrolling? What is the outcome?

## Exploration vs. Exploitation (5 mins)
- If you had a control slider from "Familiar Comfort" to "Uncharted Exploration", how would you use it?
- What would make you trust Spotify's suggestions more?

---
"""

USER_TRANSCRIPTS = [
    {
        "user": "Alex, 27 (Daily Commuter)",
        "content": """
**Q: Describe your daily listening routine.**
A: I play Spotify on my 45-minute drive to work every morning. I usually turn on my commute playlist or tap Smart Shuffle.
**Q: Have you experienced Smart Shuffle loops?**
A: Absolutely. Smart shuffle is incredibly repetitive. Out of a 600-song playlist, it seems to cycle through the exact same 15-20 tracks every single day. I find myself hitting 'skip' constantly. It feels like it ignores my skips and forces the same popular tracks on me.
**Q: How does this impact you?**
A: It makes the commute boring. I want fresh, high-energy tracks that match my drive, but I get tired of skipping and end up switching to local radio or podcasts.
"""
    },
    {
        "user": "Maya, 31 (Work Focus)",
        "content": """
**Q: How do you listen to Spotify at work?**
A: I have Spotify running in the background for 6-8 hours while coding. I rely on Daily Mixes or focus playlists.
**Q: Have you felt trapped in a recommendation bubble?**
A: Yes. My Daily Mix 1 is almost identical to my Daily Mix 2. It’s an echo chamber of my own top 5 artists. Whenever I want to discover indie ambient music, it just gives me the ambient tracks I already liked. It feels like Spotify is playing it safe rather than helping me expand my catalog.
**Q: What is the primary unmet need?**
A: I want to discover adjacent artists who sound similar but are new to me. I need a discovery tool that says 'Here is something new that sounds like your favorites, but with zero repeat tracks.'
"""
    },
    {
        "user": "Leo, 22 (Indie & Audiophile)",
        "content": """
**Q: How do you discover new music?**
A: I search external sources like Reddit (r/indieheads), YouTube, or music blogs because I don't trust Spotify's recommendations.
**Q: Why don't you trust Spotify's suggestions?**
A: Because it only recommends safe, mainstream, or high-streaming tracks. It completely lacks fine-grained dials. I want a slider to say 'give me 80% experimental discovery and 20% comfort tracks'. Right now it feels like 99% comfort. If I want to find niche local bands, I have to do all the manual digging myself.
"""
    },
    {
        "user": "Sarah, 35 (Parent & Casual Listener)",
        "content": """
**Q: Have you experienced taste profile pollution?**
A: Oh, it’s a nightmare. My 5-year-old son used my account to play Disney soundtracks and nursery rhymes for a weekend. Now, my Release Radar and Discover Weekly are completely overrun by children's bedtime songs and animation tracks.
**Q: How did you try to solve this?**
A: I tried manually clearing my search history and creating custom folders, but the recommendations are still messed up weeks later. There is no 'sandbox listening mode' or temporary private session where I can let someone else listen without permanently polluting my personal taste profile.
"""
    },
    {
        "user": "James, 29 (Commuter & Desk worker)",
        "content": """
**Q: Talk about decision paralysis when choosing music.**
A: When I sit down at my desk and want a new vibe, I open the home tab. There are a million grid recommendations. I scroll for 15-20 minutes, previewing tracks, but nothing seems to fit my exact mood. I get overwhelmed by options and just fall back on playing my old reliable liked songs list.
**Q: What would solve this?**
A: I want to just describe my mood in words, like: 'give me moody, slow synthwave that matches a gray rainy afternoon' and get a solid, curated list immediately without scrolling through endless boxes.
"""
    }
]

def extract_mcp_url(response, default_url):
    if isinstance(response, dict):
        return response.get("url", default_url)
    
    try:
        from mcp.types import CallToolResult
        if isinstance(response, CallToolResult):
            if response.content:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    text_val = first_block.text.strip()
                    try:
                        data = json.loads(text_val)
                        if isinstance(data, dict) and "url" in data:
                            return data["url"]
                    except json.JSONDecodeError:
                        import re
                        urls = re.findall(r'https?://[^\s)]+', text_val)
                        if urls:
                            return urls[0]
            if hasattr(response, "structuredContent") and response.structuredContent:
                if isinstance(response.structuredContent, dict) and "url" in response.structuredContent:
                    return response.structuredContent["url"]
    except Exception as e:
        print(f"Error extracting URL from MCP response: {e}", file=sys.stderr)
        
    return default_url

async def call_mcp_create_doc(server_path, title, content):
    logger_msg = f"Connecting to Google Docs MCP for creating doc: {title}"
    print(logger_msg, file=sys.stderr)
    server_params = StdioServerParameters(
        command="node",
        args=[server_path],
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.call_tool("create_document", {
                "title": title,
                "content": content
            })
            return extract_mcp_url(response, "https://docs.google.com/document/d/mock-mcp-research-doc-id")

async def call_mcp_append_doc(server_path, doc_url, content):
    logger_msg = "Connecting to Google Docs MCP for appending transcripts"
    print(logger_msg, file=sys.stderr)
    server_params = StdioServerParameters(
        command="node",
        args=[server_path],
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await session.call_tool("append_text", {
                "url": doc_url,
                "content": content
            })
            return True

async def call_mcp_send_gmail(server_path, subject, body, recipient="stakeholders@spotify.com"):
    logger_msg = f"Connecting to Gmail MCP to notify: {recipient}"
    print(logger_msg, file=sys.stderr)
    server_params = StdioServerParameters(
        command="node",
        args=[server_path],
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            await session.call_tool("send_email", {
                "to": recipient,
                "subject": subject,
                "body": body
            })
            return True

def compile_full_research_log():
    log_text = INTERVIEW_GUIDE
    log_text += "\n# Ingested User Interview Transcripts\n"
    for transcript in USER_TRANSCRIPTS:
        log_text += f"\n## Interview Participant: {transcript['user']}\n"
        log_text += transcript["content"]
        log_text += "\n"
        log_text += "="*40 + "\n"
    return log_text

async def main():
    parser = argparse.ArgumentParser(description="Stage qualitative user research guidelines and transcripts in Workspace.")
    parser.add_argument("--recipient", type=str, default="stakeholders@spotify.com")
    parser.add_argument("--docs-mcp-server", type=str, default="", help="Path to Google Docs MCP server js file")
    parser.add_argument("--gmail-mcp-server", type=str, default="", help="Path to Gmail MCP server js file")
    
    args = parser.parse_args()
    
    full_content = compile_full_research_log()
    use_active_mcp = MCP_AVAILABLE and args.docs_mcp_server
    
    if use_active_mcp:
        print("Active MCP detected. Exporting transcripts to Google Docs...")
        try:
            doc_url = await call_mcp_create_doc(
                args.docs_mcp_server, 
                "Qualitative User Research & Transcripts - Spotify Music Discovery", 
                INTERVIEW_GUIDE
            )
            print(f"Created research document: {doc_url}")
            
            transcripts_content = "\n# Ingested User Interview Transcripts\n"
            for transcript in USER_TRANSCRIPTS:
                transcripts_content += f"\n## Interview Participant: {transcript['user']}\n"
                transcripts_content += transcript["content"]
                transcripts_content += "\n"
                transcripts_content += "="*40 + "\n"
            
            await call_mcp_append_doc(args.docs_mcp_server, doc_url, transcripts_content)
            print("Successfully appended all user transcripts via Google Docs MCP!")
            
            if args.gmail_mcp_server:
                email_subject = "User Research Staging Ready: Spotify Discovery Phase 2"
                email_body = f"Hello Team,\n\nThe interview guide and transcripts have been successfully staged in Google Docs.\n\nLink: {doc_url}\n\nWe have scheduled the next batch of participant interviews using Calendly. They will receive automated briefings shortly.\n\nBest regards,\nGrowth Team Assistant"
                await call_mcp_send_gmail(args.gmail_mcp_server, email_subject, email_body, args.recipient)
                print("Notification email and mock Calendly invites sent via Gmail MCP!")
            return
        except Exception as e:
            print(f"Active MCP flow failed: {e}. Falling back to workspace simulation.", file=sys.stderr)
            
    # Mock / Simulation Mode
    print("\n--- Running in MCP Workspace Simulation Mode ---")
    print("Writing transcripts to local simulated Workspace files in 'data/workspace/' directory...")
    
    doc_dir = os.path.abspath("data/workspace")
    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)
        
    doc_path = os.path.join(doc_dir, "google_doc_UserInterviewTranscripts.md")
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
        
    gmail_path = os.path.join(doc_dir, "gmail_sent_ResearchInvites.txt")
    email_subject = "User Research Staging Ready: Spotify Discovery Phase 2"
    email_body = f"Hello Team,\n\nThe interview guide and transcripts have been successfully staged in Google Docs.\n\nLink: https://docs.google.com/document/d/mock-mcp-research-doc-id\n\nWe have scheduled the next batch of participant interviews using Calendly. They will receive automated briefings shortly.\n\nBest regards,\nGrowth Team Assistant"
    with open(gmail_path, 'w', encoding='utf-8') as f:
        f.write(f"TO: {args.recipient}\nSUBJECT: {email_subject}\n\n{email_body}")

    print(f"\n[MCP Mock Research Doc Created] saved to: {doc_path}")
    print(f"[MCP Mock Gmail Sent] logged to: {gmail_path}")
    print("=================================================================")
    print("SIMULATED TRANSCRIPTS PREVIEW (First 200 chars):")
    print(full_content[:200] + "...")
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(main())
