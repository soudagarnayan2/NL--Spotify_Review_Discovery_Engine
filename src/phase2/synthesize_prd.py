import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Template-based PRD for rules/offline fallback
PRD_TEMPLATE = """# Product Requirement Document (PRD): Spotify AI-Powered Music Discovery

## 1. Executive Summary & Objective
Spotify's Growth Team is introducing an AI-Powered Music Discovery extension to break users—specifically **Routine Listeners**—out of repetitive recommendation loops (algorithmic exploitation) and build a trust-centered music exploration experience.

The core objective is to decrease passive recommendation skipping, increase catalog coverage, and drive long-term user retention.

---

## 2. Target Persona & User Research Synthesis
Based on 200 parsed reviews (Phase 1) and 5 qualitative user interviews (Phase 2), we have formalized our target persona:

### Target Persona: The "Routine background Listener"
- **Profile**: Busy professionals or commuters who listen to Spotify daily for work or travel. They rely heavily on playlists, Daily Mixes, and Smart Shuffle.
- **Key Friction Points**:
  - **Algorithmic Bubbles (46.7% of negative feedback)**: The recommendation engine pushes songs they already liked or artists they already follow.
  - **Smart Shuffle Loop Fatigue**: Smart Shuffle repeats the same 15-20 songs out of 600-song playlists.
  - **Taste Pollution Fear**: Users refuse to listen to outlier genres (e.g., focus music, kids' music) because one outlier play ruins their Daily Mixes permanently.
  - **Decision Paralysis**: Users spend 15-20 minutes scrolling through recommended grid boxes trying to choose a new vibe, only to give up and return to comfort songs.

---

## 3. Core Product Features (MVP Scope)

### Feature 1: Natural Language Discovery Prompt (Vibe Search)
- **Description**: A conversational, multi-turn text interface where users describe abstract moods, contexts, or musical textures rather than just naming genres.
- **Example**: *"Give me slow, acoustic indie folk with nostalgic guitars that sounds like sitting by a window on a rainy afternoon."*

### Feature 2: Context-Aware Filtering & Safe Exploration Controls
- **Description**: A toggle to adjust the "Exploration vs. Exploitation Ratio" (0% familiar to 100% uncharted discovery), allowing users to force recommendations of completely unknown artists.
- **Example**: A slider for "Niche discovery rate".

### Feature 3: Discovery Sandbox Mode (Anti-Pollution)
- **Description**: A session-based "Sandbox Mode" toggle. When enabled, tracks played do not update or pollute the user's permanent taste profile vector.
- **Example**: *"Temporary listening mode for studying or kids' bedtime."*

### Feature 4: Interactive Memory Loop
- **Description**: An interactive chat agent that supports refinement queries (e.g., *"Make it faster,"* *"Actually, remove instrumental tracks"*).

---

## 4. Success Metrics
- **Catalog Coverage**: Increase the unique artist coverage surfaced by 30% for routine listeners.
- **Skip Rate Reduction**: Reduce smart shuffle and playlist skip rates from an average of 45% down to under 20%.
- **Retention & Engagement**: Raise daily active sessions of discovery pages by 15%.
"""

def generate_prd_prompt(insights_data, transcripts):
    prompt = f"""
    You are a Senior Product Manager on Spotify's Growth Team. You are tasked with writing a comprehensive Product Requirement Document (PRD) for the "AI-Powered Music Discovery System".
    
    We have gathered two primary inputs:
    
    1. Sentiment & Review Analysis Metrics (Phase 1):
    {json.dumps(insights_data.get("statistics", {}), indent=2)}
    
    Actionable insights from reviews:
    {json.dumps(insights_data.get("insights", []), indent=2)}
    
    2. User Interview Transcripts (Phase 2):
    {transcripts}
    
    Write a detailed, structured, and formal PRD. You MUST include these sections:
    # Product Requirement Document (PRD): Spotify AI-Powered Music Discovery
    
    ## 1. Executive Summary & Objective
    Describe the recommendation bubble problem and business objective.
    
    ## 2. Target Persona & User Research Synthesis
    Define the "Routine Listener" persona. Synthesize the findings from reviews and transcripts, emphasizing:
    - Algorithmic bubble repetition.
    - Smart Shuffle loop issues.
    - Taste pollution.
    - Decision paralysis.
    
    ## 3. Core Product Features (MVP Scope)
    Outline at least 3 detailed features solving these issues (e.g. Natural Language Vibe Search, Sandbox Listening Mode, Exploration/Exploitation Slider).
    
    ## 4. Success Metrics & Exit Criteria
    List clear metrics (Catalog Coverage, Skip Rate, User Engagement).
    
    Format the response as clean Markdown.
    """
    return prompt

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
    logger_msg = f"Connecting to Google Docs MCP for PRD: {title}"
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
            return extract_mcp_url(response, "https://docs.google.com/document/d/mock-mcp-prd-doc-id")

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

async def main():
    parser = argparse.ArgumentParser(description="Synthesize research and reviews into a PRD and publish to Google Docs using Groq.")
    parser.add_argument("--insights", type=str, default="data/processed_insights.json", help="Path to Phase 1 insights JSON")
    parser.add_argument("--transcripts", type=str, default="data/workspace/google_doc_UserInterviewTranscripts.md", help="Path to Phase 2 transcripts Markdown")
    parser.add_argument("--recipient", type=str, default="stakeholders@spotify.com", help="Email recipient for the notification")
    parser.add_argument("--docs-mcp-server", type=str, default="", help="Path to Google Docs MCP server js file")
    parser.add_argument("--gmail-mcp-server", type=str, default="", help="Path to Gmail MCP server js file")
    
    args = parser.parse_args()
    
    # 1. Ingest insights data
    insights_path = os.path.abspath(args.insights)
    if not os.path.exists(insights_path):
        print(f"Error: Insights file does not exist: {insights_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(insights_path, 'r', encoding='utf-8') as f:
        insights_data = json.load(f)
        
    # 2. Ingest user transcripts
    transcripts_path = os.path.abspath(args.transcripts)
    transcripts_content = ""
    if os.path.exists(transcripts_path):
        with open(transcripts_path, 'r', encoding='utf-8') as f:
            transcripts_content = f.read()
    else:
        print(f"Warning: Transcripts file not found at: {transcripts_path}. Using fallback default transcripts.")
        
    # 3. Call LLM (Groq) for synthesis if key is present
    prd_markdown = PRD_TEMPLATE
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if groq_api_key:
        print("Groq API key found. Launching Llama 3 synthesis...")
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            prompt = generate_prd_prompt(insights_data, transcripts_content)
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant", # Llama 3.1 8B model on Groq
                temperature=0.3
            )
            prd_markdown = chat_completion.choices[0].message.content
            print("Groq synthesis completed successfully.")
        except Exception as e:
            print(f"Groq API call failed: {e}. Falling back to default PRD template.", file=sys.stderr)
    else:
        print("No Groq API key found. Synthesizing PRD using default template.")
        
    # Generate Workspace notifications
    doc_title = f"Product Requirements Document (PRD) - Spotify AI Music Discovery - {datetime.now().strftime('%Y-%m-%d')}"
    use_active_mcp = MCP_AVAILABLE and args.docs_mcp_server
    
    doc_url = "https://docs.google.com/document/d/1yPrDScRiPtWvXyZ1234567890spotifyPRD"
    
    if use_active_mcp:
        print("Active MCP detected. Exporting PRD to Google Docs...")
        try:
            doc_url = await call_mcp_create_doc(args.docs_mcp_server, doc_title, prd_markdown)
            print(f"PRD published to Google Docs: {doc_url}")
            
            if args.gmail_mcp_server:
                email_subject = "[Growth Team] PRD Ready: Spotify AI-Powered Music Discovery"
                email_body = f"""Hello Stakeholders,

The Product Requirement Document (PRD) for the Spotify AI-powered Music Discovery System has been compiled using our Groq/Llama-3 synthesis model.

📂 Google Doc Link: {doc_url}

This document details the target "Routine Listener" persona, root problem statement, MVP feature specifications (Vibe Search, Exploration Slider, Sandbox Mode), and success metrics.

Please review the document to approve Phase 3 (MVP Implementation).

Best regards,
Spotify Growth Team AI Assistant
"""
                await call_mcp_send_gmail(args.gmail_mcp_server, email_subject, email_body, args.recipient)
                print("Notification email sent via Gmail MCP!")
            return
        except Exception as e:
            print(f"Active MCP Workspace export failed: {e}. Falling back to simulation.", file=sys.stderr)
            
    # Mock / Simulation Mode
    print("\n--- Running in MCP Workspace Simulation Mode ---")
    print("Writing PRD and sent logs to local simulated Workspace files in 'data/workspace/' directory...")
    
    doc_dir = os.path.abspath("data/workspace")
    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)
        
    # Save simulated PRD Doc
    prd_doc_path = os.path.join(doc_dir, "google_doc_ProductRequirementsDocument.md")
    with open(prd_doc_path, 'w', encoding='utf-8') as f:
        f.write(prd_markdown)
        
    # Save simulated Gmail Memo
    email_subject = "[Growth Team] PRD Ready: Spotify AI-Powered Music Discovery"
    email_body = f"""Hello Stakeholders,

The Product Requirement Document (PRD) for the Spotify AI-powered Music Discovery System has been compiled using our Groq/Llama-3 synthesis model.

📂 Google Doc Link: {doc_url}

This document details the target "Routine Listener" persona, root problem statement, MVP feature specifications (Vibe Search, Exploration Slider, Sandbox Mode), and success metrics.

Please review the document to approve Phase 3 (MVP Implementation).

Best regards,
Spotify Growth Team AI Assistant
"""
    gmail_path = os.path.join(doc_dir, "gmail_sent_PRD_Memo.txt")
    with open(gmail_path, 'w', encoding='utf-8') as f:
        f.write(f"TO: {args.recipient}\n")
        f.write(f"SUBJECT: {email_subject}\n")
        f.write("="*50 + "\n")
        f.write(email_body)
        
    print(f"\n[MCP Mock PRD Doc Created] saved to: {prd_doc_path}")
    print(f"[MCP Mock Gmail Sent] logged to: {gmail_path}")
    print("=================================================================")
    print("SIMULATED PRD MEMO SENT:")
    print(f"Subject: {email_subject}")
    print(email_body)
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(main())
