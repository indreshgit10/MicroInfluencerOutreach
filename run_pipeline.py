"""
Master Pipeline Runner - Automated Micro-Influencer Outreach System
Executes the complete end-to-end workflow:
Discovery -> Filtering -> Enrichment -> AI Personalization -> Sending Layer -> Outreach Tracker
"""

import sys
import os
import time

# Ensure UTF-8 output on Windows consoles
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from backend.pipeline.discovery import InfluencerDiscoveryEngine
from backend.pipeline.filter_classify import InfluencerFilterClassifier
from backend.pipeline.enrichment import InfluencerEnrichmentEngine
from backend.pipeline.personalization import MessagePersonalizationEngine
from backend.pipeline.sending_layer import OutreachSendingLayer

console = Console(force_terminal=True, legacy_windows=False)

def run_full_pipeline(target_niche: str = "Technology", simulation: bool = True):
    start_time = time.time()
    console.print(Panel.fit(
        f"[bold cyan]Automated Micro-Influencer Outreach System[/bold cyan]\n"
        f"[green]Niche:[/green] {target_niche} | [yellow]Execution Mode:[/yellow] {'Simulation / Anti-Spam Sandbox' if simulation else 'Live SMTP'}",
        border_style="cyan"
    ))

    # STAGE 1: INFLUENCER DISCOVERY
    console.print("\n[bold blue]=== Stage 1: Influencer Discovery ===[/bold blue]")
    discovery_engine = InfluencerDiscoveryEngine(target_niche=target_niche)
    discovered = discovery_engine.run_discovery(min_count=50)
    console.print(f"[green][+] Discovered {len(discovered)} authentic influencer profiles.[/green]")

    # STAGE 2: FILTERING & CLASSIFICATION
    console.print("\n[bold blue]=== Stage 2: Filtering & Classification ===[/bold blue]")
    filter_engine = InfluencerFilterClassifier(target_category=target_niche)
    filtered = filter_engine.run_filtering(discovered)
    passed = [f for f in filtered if f["passed"]]
    failed = [f for f in filtered if not f["passed"]]
    console.print(f"[green][+] Filtering complete: {len(passed)} Qualified Micro-Influencers | {len(failed)} Disqualified Candidates[/green]")

    # STAGE 3: PROFILE ENRICHMENT
    console.print("\n[bold blue]=== Stage 3: Profile Enrichment ===[/bold blue]")
    enrichment_engine = InfluencerEnrichmentEngine()
    enriched = enrichment_engine.run_enrichment(filtered)
    emails_count = sum(1 for e in enriched if e.get("has_valid_email") and e.get("passed"))
    console.print(f"[green][+] Enrichment complete: {emails_count} verified emails found for shortlisted candidates.[/green]")

    # STAGE 4: MESSAGE PERSONALIZATION
    console.print("\n[bold blue]=== Stage 4: AI Message Personalization ===[/bold blue]")
    personalization_engine = MessagePersonalizationEngine()
    outreach = personalization_engine.run_personalization(enriched)
    console.print(f"[green][+] Generated {len(outreach)} tailored pitches (Email: 60-90 words, DM: 15-30 words).[/green]")

    # STAGE 5: SENDING LAYER & TRACKING
    console.print("\n[bold blue]=== Stage 5: Sending Layer & Outreach Tracker ===[/bold blue]")
    sending_engine = OutreachSendingLayer()
    tracker_logs = sending_engine.process_outreach(outreach, simulate_all=simulation)
    console.print(f"[green][+] Processed and recorded {len(tracker_logs)} entries in Outreach Tracker.[/green]")

    # SUMMARY DASHBOARD TABLE
    console.print("\n[bold magenta]=== Summary of Shortlisted Outreach Candidates ===[/bold magenta]")
    table = Table(title="Qualified Micro-Influencers & Outreach Pitch Preview", box=box.ROUNDED)
    table.add_column("Influencer", style="cyan", no_wrap=True)
    table.add_column("Platform", style="magenta")
    table.add_column("Followers", justify="right", style="green")
    table.add_column("Engagement", justify="right", style="yellow")
    table.add_column("Email Status", style="blue")
    table.add_column("Email Pitch Preview (60-90 words)", style="white")
    table.add_column("Instagram DM (15-30 words)", style="bright_cyan")

    for item in outreach[:8]: # Display sample preview
        email_preview = item['email_pitch'][:90] + "..." if len(item['email_pitch']) > 90 else item['email_pitch']
        dm_preview = item['instagram_dm']
        table.add_row(
            item["name"],
            item["platform"],
            f"{next((c['follower_count'] for c in discovered if c['name'] == item['name']), 0):,}",
            f"{next((c['engagement_rate'] for c in discovered if c['name'] == item['name']), 0.0)}%",
            item["contact_email"] if item["contact_email"] != "Not Found" else "[red]Not Found[/red]",
            f"{email_preview} [dim]({item['email_word_count']} words)[/dim]",
            f"{dm_preview} [dim]({item['dm_word_count']} words)[/dim]"
        )

    console.print(table)
    elapsed = time.time() - start_time
    console.print(f"\n[bold green][+] Pipeline completed in {elapsed:.2f}s! All datasets saved to ./data/ directory.[/bold green]\n")

if __name__ == "__main__":
    run_full_pipeline()
