#!/usr/bin/env python3
"""
Convert AsciiDoc files to Markdown for TechDocs consumption.

This script converts all .adoc files in the modules directory to .md files
in a techdocs-compatible structure.
"""

import os
import subprocess
import shutil
import re
from pathlib import Path

try:
    import html2text
except ImportError:
    print("Installing html2text...")
    subprocess.run(["pip", "install", "html2text"], check=True)
    import html2text

# Directories
SCRIPT_DIR = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR / "modules"
OUTPUT_DIR = SCRIPT_DIR / "markdown"

# Mapping of AsciiDoc files to Markdown output
FILE_MAPPINGS = {
    # ROOT module
    "ROOT/pages/index.adoc": "index.md",
    "ROOT/pages/training-guide.adoc": "training-guide.md",
    "ROOT/pages/getting-started.adoc": "getting-started.md",
    "ROOT/pages/api-reference.adoc": "api-reference.md",
    "ROOT/pages/environment-variables.adoc": "environment-variables.md",
    "ROOT/pages/deployment-guide.adoc": "deployment-guide.md",
    "ROOT/pages/llm-rules-implementation.adoc": "llm-rules-implementation.md",

    # Architecture module
    "architecture/pages/architecture.adoc": "architecture.md",
    "architecture/pages/data-flow-diagram.adoc": "data-flow-diagram.md",

    # How-to module
    "how-to/pages/how-to-add-new-rule.adoc": "how-to-add-new-rule.md",
    "how-to/pages/how-to-add-new-ambiguity-detector.adoc": "how-to-add-new-ambiguity-detector.md",
    "how-to/pages/how-to-add-new-model.adoc": "how-to-add-new-model.md",
    "how-to/pages/configure-providers.adoc": "configure-providers.md",
    "how-to/pages/testing-setup.adoc": "testing-setup.md",
    "how-to/pages/testing-guide.adoc": "testing-guide.md",
    "how-to/pages/writing-tests.adoc": "writing-tests.md",
}


def check_asciidoctor():
    """Check if asciidoctor is installed."""
    try:
        result = subprocess.run(
            ["asciidoctor", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Found asciidoctor: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ asciidoctor not found. Please install it:")
        print("  gem install asciidoctor")
        return False


def convert_adoc_to_markdown(input_file: Path, output_file: Path):
    """
    Convert AsciiDoc file to Markdown using asciidoctor and html2text.

    Args:
        input_file: Path to input .adoc file
        output_file: Path to output .md file
    """
    print(f"Converting {input_file.name} -> {output_file.name}")

    temp_html = output_file.with_suffix('.tmp.html')

    try:
        # Step 1: Convert AsciiDoc to HTML using asciidoctor
        subprocess.run(
            [
                "asciidoctor",
                "-o", str(temp_html),
                "-a", "source-highlighter=highlight.js",
                str(input_file)
            ],
            check=True,
            capture_output=True,
            text=True
        )

        # Step 2: Read HTML content
        with open(temp_html, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Step 3: Convert HTML to Markdown using html2text
        h = html2text.HTML2Text()
        h.body_width = 0  # Don't wrap text
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.skip_internal_links = False
        h.inline_links = True
        h.protect_links = True
        h.mark_code = True

        markdown_content = h.handle(html_content)

        # Step 4: Clean up the markdown
        # Remove excessive newlines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

        # Fix xref links (convert Antora xrefs to simple links)
        markdown_content = re.sub(
            r'xref:([^[]+)\[([^\]]+)\]',
            r'[\2](\1)',
            markdown_content
        )

        # Write the markdown file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"  ✓ Created {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error converting {input_file}: {e}")
        if e.stderr:
            print(f"    {e.stderr}")
    except Exception as e:
        print(f"  ✗ Error processing {input_file}: {e}")
    finally:
        # Clean up temporary HTML file
        if temp_html.exists():
            temp_html.unlink()


def main():
    """Main conversion process."""
    print("=" * 60)
    print("AsciiDoc to Markdown Converter for TechDocs")
    print("=" * 60)
    print()

    # Check dependencies
    if not check_asciidoctor():
        print("\nPlease install missing dependencies and try again.")
        return 1

    print("✓ Python html2text library available")

    print()

    # Create output directory
    if OUTPUT_DIR.exists():
        print(f"Cleaning output directory: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created output directory: {OUTPUT_DIR}")
    print()

    # Convert each file
    converted = 0
    failed = 0

    for adoc_path, md_path in FILE_MAPPINGS.items():
        input_file = MODULES_DIR / adoc_path
        output_file = OUTPUT_DIR / md_path

        if not input_file.exists():
            print(f"⚠ Skipping {adoc_path} (not found)")
            failed += 1
            continue

        try:
            convert_adoc_to_markdown(input_file, output_file)
            converted += 1
        except Exception as e:
            print(f"✗ Failed to convert {adoc_path}: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Conversion complete!")
    print(f"  ✓ Converted: {converted} files")
    if failed > 0:
        print(f"  ✗ Failed: {failed} files")
    print(f"  → Output directory: {OUTPUT_DIR}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
