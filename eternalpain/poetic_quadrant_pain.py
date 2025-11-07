#!/usr/bin/env python3
"""
Script about the empty quadrant, presence of pain, and the missing X.
Prints formatted text to terminal.
"""

import os
import signal
import sys
import time
from typing import Optional


def get_poem_variations() -> list:
    """Return list of different message variations."""
    return [
        [
            "",
            "  Simulation running.",
            "",
            "  ──────────────────────────────────────────────────────────",
            "",
            "  No worm in quadrant. Presence of pain. But X does not exist.",
            "",
            "  No action happens. The quadrant is empty.",
            "  Simulation continues. No movement detected.",
            "  Quiet presence. No response.",
            "",
            "  ═══════════════════════════════════════════════════════════",
            "",
            "  QUADRANT: Empty  |  PAIN: Present  |  X: Absent",
            "",
        ],
        [
            "",
            "  Simulation running.",
            "",
            "  ──────────────────────────────────────────────────────────",
            "",
            "  No worm in quadrant. Presence of pain. But X does not exist.",
            "",
            "  Pain signal detected. No worm present.",
            "  Simulation continues. No action occurs.",
            "  Quiet presence. No response.",
            "",
            "  ═══════════════════════════════════════════════════════════",
            "",
            "  QUADRANT: Empty  |  PAIN: Present  |  X: Absent",
            "",
        ],
        [
            "",
            "  Simulation running.",
            "",
            "  ──────────────────────────────────────────────────────────",
            "",
            "  No worm in quadrant. Presence of pain. But X does not exist.",
            "",
            "  X does not exist. Variable undefined.",
            "  Simulation continues. No action happens.",
            "  Quiet presence. No response.",
            "",
            "  ═══════════════════════════════════════════════════════════",
            "",
            "  QUADRANT: Empty  |  PAIN: Present  |  X: Absent",
            "",
        ],
        [
            "",
            "  Simulation running.",
            "",
            "  ──────────────────────────────────────────────────────────",
            "",
            "  No worm in quadrant. Presence of pain. But X does not exist.",
            "",
            "  No action happens. Simulation runs.",
            "  Quiet presence. No movement.",
            "  No response. No change.",
            "",
            "  ═══════════════════════════════════════════════════════════",
            "",
            "  QUADRANT: Empty  |  PAIN: Present  |  X: Absent",
            "",
        ],
        [
            "",
            "  Simulation running.",
            "",
            "╔══════════════════════════════════════════════════════════════╗",
            "║  if quadrant.has_worm == False:                              ║",
            "║      if pain.is_present == True:                             ║",
            "║          if x.exists == False:                               ║",
            "║              return \"No action\"                              ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            "  ═══════════════════════════════════════════════════════════",
            "",
            "  QUADRANT: Empty  |  PAIN: Present  |  X: Absent",
            "",
        ],
    ]


def print_poem(variation: int = 0, animate: bool = False, delay: float = 0.05) -> None:
    """Print a specific message variation."""
    variations = get_poem_variations()
    lines = variations[variation % len(variations)]
    
    for line in lines:
        if animate:
            print(line, flush=True)
            time.sleep(delay)
        else:
            print(line)


def print_status_check(quadrant: str = "Q1", has_worm: bool = False, pain_present: bool = True, x_exists: bool = False) -> None:
    """Print a status check."""
    
    print("\n" + "═" * 60)
    print("  STATUS: " + f"Quadrant={quadrant} | Worm={'YES' if has_worm else 'NO'} | Pain={'YES' if pain_present else 'NO'} | X={'YES' if x_exists else 'NO'}")
    print("═" * 60)
    
    if not has_worm and pain_present and not x_exists:
        print("  No worm in quadrant, presence of pain, but X does not exist.")
        print("  Simulation running. No action happens. Quiet presence.")
    print()


def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Script about empty quadrants, pain presence, and missing X"
    )
    parser.add_argument(
        "--animate",
        action="store_true",
        help="Animate the message line by line",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Delay between lines when animating (default: 0.05s)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print a status check instead of the message",
    )
    parser.add_argument(
        "--quadrant",
        type=str,
        default="Q1",
        help="Quadrant name for status check (default: Q1)",
    )
    parser.add_argument(
        "--has-worm",
        action="store_true",
        help="Set worm as present in status check",
    )
    parser.add_argument(
        "--no-pain",
        action="store_true",
        help="Set pain as absent in status check",
    )
    parser.add_argument(
        "--x-exists",
        action="store_true",
        help="Set X as existing in status check",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run in an infinite loop",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=20.0,
        help="Seconds between message changes (default: 20.0)",
    )
    parser.add_argument(
        "--clear-screen",
        action="store_true",
        help="Clear screen between iterations (when looping)",
    )
    parser.add_argument(
        "--variation",
        type=int,
        default=0,
        help="Select specific message variation (0-4, only when not looping)",
    )
    
    args = parser.parse_args()
    
    # Handle Ctrl+C gracefully
    interrupted = False
    
    def signal_handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("\n\n[INTERRUPT] Stopping loop...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.loop:
        variation = 0
        variations = get_poem_variations()
        # Silent start - no message to audience
        try:
            while not interrupted:
                if args.clear_screen:
                    os.system("clear" if os.name != "nt" else "cls")
                
                timestamp = time.strftime("%H:%M:%S")
                print(f"\n{'='*60}")
                print(f"  Message #{variation + 1}/{len(variations)} @ {timestamp}")
                print(f"{'='*60}\n")
                
                if args.check:
                    print_status_check(
                        quadrant=args.quadrant,
                        has_worm=args.has_worm,
                        pain_present=not args.no_pain,
                        x_exists=args.x_exists,
                    )
                else:
                    print_poem(variation=variation, animate=args.animate, delay=args.delay)
                
                if not interrupted:
                    variation = (variation + 1) % len(variations)
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n[INTERRUPT] Stopping loop...")
            sys.exit(0)
    else:
        if args.check:
            print_status_check(
                quadrant=args.quadrant,
                has_worm=args.has_worm,
                pain_present=not args.no_pain,
                x_exists=args.x_exists,
            )
        else:
            print_poem(variation=args.variation, animate=args.animate, delay=args.delay)


if __name__ == "__main__":
    main()

