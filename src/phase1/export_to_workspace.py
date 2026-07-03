import os
import sys
import json
import argparse
import asyncio
from datetime import datetime

# Reconfigure stdout to use UTF-8 to prevent encoding errors on Windows when printing unicode
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Attempt to import MCP SDK libraries
MCP_AVAILABLE = False
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    pass

def generate_report_markdown(insights_data):
    stats = insights_data.get("statistics", {})
    metadata = insights_data.get("metadata", {})
    records = insights_data.get("records", [])
    
    # Calculate percentages
    total = metadata.get("total_reviews", 0)
    sentiments = stats.get("sentiments", {})
    topics = stats.get("topics", {})
    
    pos_pct = (sentiments.get("Positive", 0) / total * 100) if total > 0 else 0
    neg_pct = (sentiments.get("Negative", 0) / total * 100) if total > 0 else 0
    neu_pct = (sentiments.get("Neutral", 0) / total * 100) if total > 0 else 0

    md = f"""# Spotify AI Review Discovery Engine: Insights Report
**Generated on**: {metadata.get("analysis_date", datetime.now().strftime('%Y-%m-%d'))}
**Analysis Engine**: {metadata.get("engine", "Rules-based fallback")}
**Total Ingested Reviews**: {total}

---

## 1. Sentiment Distribution Analysis
- **Negative Feedback**: {sentiments.get("Negative", 0)} ({neg_pct:.1f}%)
- **Neutral Feedback**: {sentiments.get("Neutral", 0)} ({neu_pct:.1f}%)
- **Positive Feedback**: {sentiments.get("Positive", 0)} ({pos_pct:.1f}%)

> [!IMPORTANT]
> Over {neg_pct:.1f}% of reviews contain complaints about recommendation stagnation, expressing high friction around algorithmic echo chambers and repeat listening habits.

---

## 2. Recommendation Friction: Topic Categorization
Here is the breakdown of the primary issues users report facing:

"""
    for topic, count in topics.items():
        pct = (count / total * 100) if total > 0 else 0
        md += f"- **{topic}**: {count} occurrences ({pct:.1f}%)\n"
        
    md += "\n---\n\n## 3. Core Actionable Insights\n\n"
    
    for idx, insight in enumerate(insights_data.get("insights", [])):
        md += f"### Insight {idx+1}: {insight.get('topic')}\n"
        md += f"- **Key Finding**: {insight.get('findings')}\n"
        md += f"- **Severity**: {insight.get('severity')}\n\n"
        
    md += "---\n\n## 4. Key User Quotes (Structured by Platform)\n\n"
    
    # Group negative records by platform group
    app_store_records = [r for r in records if r.get("sentiment") == "Negative" and r.get("platform") == "app_store"][:3]
    play_store_records = [r for r in records if r.get("sentiment") == "Negative" and r.get("platform") == "play_store"][:3]
    social_records = [r for r in records if r.get("sentiment") == "Negative" and r.get("platform") in ("reddit", "twitter")][:3]
    
    md += "### Apple App Store:\n"
    if app_store_records:
        for r in app_store_records:
            md += f"> \"{r.get('content')}\"\n"
            md += f"*(User: {r.get('user')} - Date: {r.get('date')} - Category: {r.get('topic')}*)\n\n"
    else:
        md += "*No negative App Store reviews sampled.*\n\n"
        
    md += "### Google Play Store & Community Forums:\n"
    if play_store_records:
        for r in play_store_records:
            md += f"> \"{r.get('content')}\"\n"
            md += f"*(User: {r.get('user')} - Date: {r.get('date')} - Category: {r.get('topic')}*)\n\n"
    else:
        md += "*No negative Google Play Store reviews sampled.*\n\n"
        
    md += "### Reddit & Twitter Discussions:\n"
    if social_records:
        for r in social_records:
            md += f"> \"{r.get('content')}\"\n"
            md += f"*(Platform: {r.get('platform').capitalize()}, User: {r.get('user')} - Date: {r.get('date')} - Category: {r.get('topic')}*)\n\n"
    else:
        md += "*No negative social media discussions sampled.*\n\n"
            
    return md

def generate_email_content(insights_data, report_link="[Mock Google Doc Link]"):
    stats = insights_data.get("statistics", {})
    metadata = insights_data.get("metadata", {})
    total = metadata.get("total_reviews", 0)
    neg_count = stats.get("sentiments", {}).get("Negative", 0)
    
    subject = "[Growth Team] Spotify AI Review Discovery Engine - Insights Report Ready"
    body = f"""Hello Team,

The AI Review Discovery Engine has finished analyzing the latest user reviews and social media comments regarding Spotify's recommendation algorithms.

### Summary Metrics:
- Total Reviews Ingested: {total}
- Negative Feedback: {neg_count} ({((neg_count / total * 100) if total > 0 else 0):.1f}%)
- Target Segment: Routine Spotify Listeners suffering from Algorithmic Bubbles.

The detailed insights report has been generated in Google Workspace:
📂 Google Doc Link: {report_link}

### Primary Findings:
1. Algorithmic Bubble & Stagnation: Casual and routine listeners feel stuck in loops where they get recommended what they already listen to.
2. Smart Shuffle Issues: Users feel smart shuffle repeats tracks they've skipped multiple times.
3. Taste Pollution: Users dread listening to outliers (joke songs/kids' tracks) because they ruin their recommendation profile.

Please review the full Google Doc report to prepare for Phase 2 (Qualitative User Research validation).

Best regards,
Spotify Growth Team AI Assistant
"""
    return subject, body

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

async def call_mcp_google_docs(server_path, report_title, md_content):
    print("Connecting to Google Docs MCP server via stdio...")
    server_params = StdioServerParameters(
        command="node",
        args=[server_path],
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Successfully initialized Google Docs MCP session.")
            
            print(f"Calling 'create_document' tool for title: {report_title}...")
            response = await session.call_tool("create_document", {"title": report_title, "content": md_content})
            print(f"Tool response: {response}")
            return extract_mcp_url(response, "https://docs.google.com/document/d/mock-mcp-doc-id")

async def call_mcp_gmail(server_path, subject, body, recipient="stakeholders@spotify.com"):
    print("Connecting to Gmail MCP server via stdio...")
    server_params = StdioServerParameters(
        command="node",
        args=[server_path],
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Successfully initialized Gmail MCP session.")
            
            print(f"Calling 'send_email' tool to: {recipient}...")
            response = await session.call_tool("send_email", {
                "to": recipient,
                "subject": subject,
                "body": body
            })
            print(f"Tool response: {response}")
            return True

async def main():
    parser = argparse.ArgumentParser(description="Export review analysis insights to Google Workspace via MCP.")
    parser.add_argument("--input", type=str, default="data/processed_insights.json", help="Path to analyzed insights JSON")
    parser.add_argument("--recipient", type=str, default="stakeholders@spotify.com", help="Gmail recipient for the notification memo")
    parser.add_argument("--docs-mcp-server", type=str, default="", help="Path to Google Docs MCP server js file (optional)")
    parser.add_argument("--gmail-mcp-server", type=str, default="", help="Path to Gmail MCP server js file (optional)")
    
    args = parser.parse_args()
    
    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"Error: Insights file does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(input_path, 'r', encoding='utf-8') as f:
        insights_data = json.load(f)
        
    report_title = f"Review Analysis & Discovery Insights Report - {datetime.now().strftime('%Y-%m-%d')}"
    md_content = generate_report_markdown(insights_data)
    
    use_active_mcp = MCP_AVAILABLE and args.docs_mcp_server and args.gmail_mcp_server
    
    if use_active_mcp:
        print("Active MCP parameters detected. Launching MCP Google Workspace flow...")
        try:
            doc_url = await call_mcp_google_docs(args.docs_mcp_server, report_title, md_content)
            subject, body = generate_email_content(insights_data, report_link=doc_url)
            await call_mcp_gmail(args.gmail_mcp_server, subject, body, args.recipient)
            print("\nSuccessfully executed workspace export using active MCP servers!")
            return
        except Exception as e:
            print(f"\nActive MCP flow failed: {e}. Falling back to local workspace simulation...", file=sys.stderr)
            
    # Mock / Simulation Mode fallback
    print("\n--- Running in MCP Workspace Simulation Mode ---")
    print("No active MCP server path arguments provided or SDK was unavailable.")
    print("Writing outputs to local simulated Workspace files in 'data/workspace/' directory...")
    
    doc_url = "https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ123456spotify"
    subject, body = generate_email_content(insights_data, report_link=doc_url)
    
    doc_dir = os.path.abspath("data/workspace")
    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)
        
    doc_path = os.path.join(doc_dir, "google_doc_ReviewAnalysisInsightsReport.md")
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    gmail_path = os.path.join(doc_dir, "gmail_sent_NotificationMemo.txt")
    with open(gmail_path, 'w', encoding='utf-8') as f:
        f.write(f"TO: {args.recipient}\n")
        f.write(f"SUBJECT: {subject}\n")
        f.write("="*50 + "\n")
        f.write(body)
        
    print(f"\n[MCP Mock Doc Created] saved to: {doc_path}")
    print(f"[MCP Mock Gmail Sent] logged to: {gmail_path}")
    print("=================================================================")
    print("SIMULATED EMAIL DRAFT SENT:")
    print(f"Subject: {subject}")
    print(body)
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(main())
