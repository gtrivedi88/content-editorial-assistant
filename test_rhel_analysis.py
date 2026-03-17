"""End-to-end analysis of RHEL 5.2 content to reproduce FPs."""
import os
os.environ['LLM_PROVIDER'] = 'none'

from app import create_app
app = create_app()

RHEL_TEXT = """5.2. Configuring a network bridge by using the RHEL web console

Use the RHEL web console to configure a network bridge if you prefer to manage network settings using a web browser-based interface.

Prerequisites

Two or more physical or virtual network devices are installed on the server.
To use Ethernet devices as ports of the bridge, the physical or virtual Ethernet devices must be installed on the server.
To use bond or Virtual Local Area Network (VLAN) devices as ports of the bridge, you can either create these devices while you create the bridge or you can create them in advance as described in:

Configuring a network bond by using the RHEL web console
Configuring VLAN tagging by using the RHEL web console
Procedure

Select the Networking tab in the navigation on the left side of the screen.
Click Add bridge in the Interfaces section.
Enter the name of the bridge device you want to create.
Select the interfaces that should be ports of the bridge.
Optional: Enable the Spanning tree protocol (STP) feature to avoid bridge loops and broadcast radiation.
Click Apply.
By default, the bridge uses a dynamic IP address. If you want to set a static IP address:

Click the name of the bridge in the Interfaces section.
Click Edit next to the protocol you want to configure.
Select Manual next to Addresses, and enter the IP address, prefix, and default gateway.
In the DNS section, click the + button, and enter the IP address of the DNS server. Repeat this step to set multiple DNS servers.
In the DNS search domains section, click the + button, and enter the search domain.
If the interface requires static routes, configure them in the Routes section.
Click Apply
Verification

Select the Networking tab in the navigation on the left side of the screen, and check if there is incoming and outgoing traffic on the interface."""

with app.app_context():
    from app.services.analysis.preprocessor import preprocess
    from app.services.analysis.deterministic import run_deterministic_analysis

    prep = preprocess(RHEL_TEXT, 'plaintext')

    # Show detected blocks
    print('=== BLOCKS ===')
    for b in prep.get('blocks', []):
        bt = b.block_type
        content_preview = repr(b.content[:80])
        print(f'  [{bt}] pos={b.start_pos}-{b.end_pos}: {content_preview}')

    print()

    # Run deterministic analysis
    issues = run_deterministic_analysis(
        text=prep['cleaned_text'],
        sentences=prep.get('sentences', []),
        nlp=prep.get('nlp'),
        spacy_doc=prep.get('spacy_doc'),
        blocks=prep.get('blocks', []),
        content_type='procedure',
    )

    # Filter to using_clarity issues
    using_issues = [i for i in issues if i.get('type') == 'using_clarity']
    print(f'=== USING_CLARITY ISSUES: {len(using_issues)} ===')
    for issue in using_issues:
        ft = repr(issue.get('flagged_text', ''))
        sp = issue.get('span')
        sent = repr(issue.get('sentence', '')[:100])
        print(f'  flagged={ft} span={sp} sentence={sent}')

    # Show ALL issues
    print(f'\n=== ALL ISSUES: {len(issues)} ===')
    for issue in issues:
        itype = issue.get('type', '')
        ft = repr(issue.get('flagged_text', '')[:40])
        msg = repr(issue.get('message', '')[:70])
        print(f'  [{itype}] flagged={ft} msg={msg}')
