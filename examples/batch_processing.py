#!/usr/bin/env python3
"""
Example: Batch Processing Clinical Documents

This script demonstrates how to process multiple clinical documents
for de-identification, with progress tracking and output options.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pii_detector import PIIDetector, get_detector
from src.deidentify import Deidentifier, ReplacementStrategy


def process_documents(
    input_files: List[str],
    output_dir: str,
    strategy: str = "placeholder",
    confidence: float = 0.5
) -> Dict:
    """
    Process multiple clinical documents for de-identification.

    Args:
        input_files: List of input file paths
        output_dir: Directory to write de-identified files
        strategy: Replacement strategy (placeholder, consistent, redact, hash)
        confidence: Confidence threshold (0-1)

    Returns:
        Summary statistics
    """
    # Initialize
    detector = get_detector()
    detector.confidence_threshold = confidence

    strategy_map = {
        "placeholder": ReplacementStrategy.PLACEHOLDER,
        "consistent": ReplacementStrategy.CONSISTENT,
        "redact": ReplacementStrategy.REDACT,
        "hash": ReplacementStrategy.HASH,
    }
    deidentifier = Deidentifier(
        detector=detector,
        strategy=strategy_map.get(strategy, ReplacementStrategy.PLACEHOLDER)
    )

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Process files
    stats = {
        "files_processed": 0,
        "total_entities": 0,
        "entities_by_type": {},
        "files": []
    }

    for file_path in input_files:
        path = Path(file_path)

        if not path.exists():
            print(f"Warning: File not found: {file_path}")
            continue

        print(f"Processing: {path.name}...")

        # Read input
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # De-identify
        result = deidentifier.deidentify(text)

        # Write output
        output_file = output_path / f"{path.stem}_deidentified{path.suffix}"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.deidentified_text)

        # Track statistics
        stats["files_processed"] += 1
        stats["total_entities"] += result.entity_count

        for entity in result.entities_found:
            entity_type = entity.entity_type.value
            stats["entities_by_type"][entity_type] = (
                stats["entities_by_type"].get(entity_type, 0) + 1
            )

        stats["files"].append({
            "input": str(path),
            "output": str(output_file),
            "entities": result.entity_count,
            "replacements": result.replacements_made
        })

        print(f"  -> {result.entity_count} entities found")
        print(f"  -> Saved to: {output_file}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Batch process clinical documents for PII de-identification"
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Input files or directory"
    )
    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "-s", "--strategy",
        choices=["placeholder", "consistent", "redact", "hash"],
        default="placeholder",
        help="Replacement strategy (default: placeholder)"
    )
    parser.add_argument(
        "-c", "--confidence",
        type=float,
        default=0.5,
        help="Confidence threshold 0-1 (default: 0.5)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Save detailed statistics to JSON"
    )

    args = parser.parse_args()

    # Expand input files
    input_files = []
    for path in args.input:
        p = Path(path)
        if p.is_dir():
            # Add all text files in directory
            input_files.extend(p.glob("*.txt"))
            input_files.extend(p.glob("*.md"))
        else:
            input_files.append(path)

    if not input_files:
        print("No input files found!")
        sys.exit(1)

    print("=" * 60)
    print("Medical PII De-identification - Batch Processing")
    print("=" * 60)
    print(f"Input files: {len(input_files)}")
    print(f"Output directory: {args.output}")
    print(f"Strategy: {args.strategy}")
    print(f"Confidence: {args.confidence}")
    print("=" * 60)
    print()

    # Process documents
    stats = process_documents(
        input_files=[str(f) for f in input_files],
        output_dir=args.output,
        strategy=args.strategy,
        confidence=args.confidence
    )

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {stats['files_processed']}")
    print(f"Total entities found: {stats['total_entities']}")
    print()
    print("Entities by type:")
    for entity_type, count in sorted(
        stats["entities_by_type"].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {entity_type}: {count}")

    # Save statistics if requested
    if args.stats:
        stats_file = Path(args.output) / "processing_stats.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"\nStatistics saved to: {stats_file}")

    print()
    print("Processing complete!")


if __name__ == "__main__":
    main()
