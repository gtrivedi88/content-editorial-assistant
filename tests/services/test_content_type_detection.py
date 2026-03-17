"""Tests for the 4-tier weighted multi-type content type detection engine.

Validates that _detect_content_type() correctly identifies procedure,
concept, and reference documents from various structural markers,
title patterns, and content shape signals.
"""

import pytest

from app.services.analysis.preprocessor import _detect_content_type


class TestTier1Metadata:
    """Tier 1: AsciiDoc :_mod-docs-content-type: attribute — instant win."""

    def test_procedure_attribute(self):
        text = ":_mod-docs-content-type: PROCEDURE\n\nSome content here."
        assert _detect_content_type(text) == "procedure"

    def test_concept_attribute(self):
        text = ":_mod-docs-content-type: CONCEPT\n\nSome content here."
        assert _detect_content_type(text) == "concept"

    def test_reference_attribute(self):
        text = ":_mod-docs-content-type: REFERENCE\n\nSome content here."
        assert _detect_content_type(text) == "reference"

    def test_assembly_attribute(self):
        text = ":_mod-docs-content-type: ASSEMBLY\n\nSome content here."
        assert _detect_content_type(text) == "assembly"

    def test_attribute_case_insensitive(self):
        text = ":_mod-docs-content-type: procedure\n\nSome content."
        assert _detect_content_type(text) == "procedure"

    def test_attribute_overrides_all_other_signals(self):
        """Attribute takes priority even when other tiers disagree."""
        text = (
            ":_mod-docs-content-type: CONCEPT\n\n"
            "Prerequisites\n\n"
            "Procedure\n\n"
            "1. Click the button.\n"
            "2. Enter the value.\n"
            "3. Select the option.\n"
        )
        assert _detect_content_type(text) == "concept"


class TestTier2StructuralMarkers:
    """Tier 2: Standalone structural headings — +20 per marker."""

    def test_asciidoc_procedure_marker(self):
        text = ".Procedure\n\n1. Do something.\n2. Do another.\n3. Finish."
        assert _detect_content_type(text) == "procedure"

    def test_plain_text_procedure_marker(self):
        text = "Procedure\n\n1. Do something.\n2. Do another.\n3. Finish."
        assert _detect_content_type(text) == "procedure"

    def test_prerequisites_marker(self):
        text = "Prerequisites\n\n* Have admin access.\n\nProcedure\n\n1. Click Install."
        assert _detect_content_type(text) == "procedure"

    def test_verification_marker(self):
        text = "Procedure\n\n1. Install it.\n\nVerification\n\n1. Check the status."
        assert _detect_content_type(text) == "procedure"

    def test_troubleshooting_marker(self):
        text = "Procedure\n\n1. Do it.\n\nTroubleshooting\n\nIf it fails, retry."
        assert _detect_content_type(text) == "procedure"

    def test_additional_resources_reference(self):
        text = "Additional resources\n\n* Link to docs.\n* Another link."
        assert _detect_content_type(text) == "reference"

    def test_related_information_reference(self):
        text = "Related information\n\n* See the guide.\n* Check the FAQ."
        assert _detect_content_type(text) == "reference"

    def test_asciidoc_prerequisites_with_dot(self):
        text = ".Prerequisites\n\n* Have access.\n\n.Procedure\n\n. Do it."
        assert _detect_content_type(text) == "procedure"

    def test_nonbreaking_space_trap3(self):
        """Trap 3: non-breaking space after marker from browser paste."""
        text = "Procedure\u00a0\n\n1. Click Install.\n2. Select option.\n3. Confirm."
        assert _detect_content_type(text) == "procedure"


class TestTier3LexicalTitleGuard:
    """Tier 3: Title naming conventions — +10."""

    def test_concept_title_about(self):
        text = "About network bridges\n\nA network bridge connects two networks."
        assert _detect_content_type(text) == "concept"

    def test_concept_title_understanding(self):
        text = "Understanding network bridges\n\nBridges forward packets."
        assert _detect_content_type(text) == "concept"

    def test_concept_title_architecture(self):
        text = "Architecture of the system\n\nThe system has three layers."
        assert _detect_content_type(text) == "concept"

    def test_concept_title_introduction(self):
        text = "Introduction to OpenShift\n\nOpenShift is a platform."
        assert _detect_content_type(text) == "concept"

    def test_procedure_title_configuring(self):
        text = "Configuring a network bridge\n\nFollow these steps."
        assert _detect_content_type(text) == "procedure"

    def test_procedure_title_installing(self):
        text = "Installing the package\n\nUse the package manager."
        assert _detect_content_type(text) == "procedure"

    def test_procedure_title_creating(self):
        text = "Creating a new project\n\nSet up the workspace."
        assert _detect_content_type(text) == "procedure"

    def test_reference_title_reference(self):
        text = "Command Reference\n\ncurl: transfers data.\nwget: downloads files."
        assert _detect_content_type(text) == "reference"

    def test_reference_title_parameters(self):
        text = "Configuration Parameters\n\nport: the TCP port.\nhost: the hostname."
        assert _detect_content_type(text) == "reference"

    def test_asciidoc_heading_procedure_title(self):
        text = "= Configuring a network bridge\n\nUse nmcli to configure."
        assert _detect_content_type(text) == "procedure"

    def test_asciidoc_heading_concept_title(self):
        text = "= Understanding containers\n\nContainers isolate processes."
        assert _detect_content_type(text) == "concept"


class TestTier4ContentShape:
    """Tier 4: Content shape signals — +5."""

    def test_numbered_steps_procedure(self):
        text = (
            "Follow these steps:\n\n"
            "1. Open the terminal.\n"
            "2. Run the command.\n"
            "3. Verify the output.\n"
            "4. Close the terminal.\n"
        )
        assert _detect_content_type(text) == "procedure"

    def test_imperative_steps_procedure(self):
        text = (
            "Steps:\n\n"
            "1. Click Settings.\n"
            "2. Select Advanced.\n"
            "3. Enter the hostname.\n"
        )
        assert _detect_content_type(text) == "procedure"

    def test_optional_prefix_procedure(self):
        text = (
            "Steps:\n\n"
            "1. Open the file.\n"
            "2. Edit the config.\n"
            "3. Save the file.\n"
            "Optional: restart the service.\n"
        )
        assert _detect_content_type(text) == "procedure"

    def test_table_markers_reference(self):
        text = (
            "Parameter table:\n\n"
            "|===\n"
            "| Name | Type | Default\n"
            "| port | int | 8080\n"
            "|===\n"
        )
        assert _detect_content_type(text) == "reference"

    def test_definition_lists_reference(self):
        text = (
            "port::\n  The TCP port number.\n\n"
            "host::\n  The hostname.\n\n"
            "timeout::\n  Connection timeout in seconds.\n"
        )
        assert _detect_content_type(text) == "reference"


class TestMultiTypeScoring:
    """Multi-type scoring — highest score wins."""

    def test_procedure_wins_over_concept_with_structural_markers(self):
        """Procedure structural markers outweigh concept title."""
        text = (
            "Understanding the installation process\n\n"
            "Prerequisites\n\n"
            "* Admin access\n\n"
            "Procedure\n\n"
            "1. Click Install.\n"
            "2. Select the option.\n"
            "3. Confirm.\n"
        )
        assert _detect_content_type(text) == "procedure"

    def test_reference_with_tables_and_title(self):
        text = (
            "Configuration Parameters\n\n"
            "Additional resources\n\n"
            "|===\n"
            "| Key | Value\n"
            "|===\n"
        )
        assert _detect_content_type(text) == "reference"

    def test_sme_rhel_procedure_scenario(self):
        """The exact SME scenario: pasted RHEL 5.2 procedure content."""
        text = (
            "Configuring a network bridge by using the RHEL web console\n\n"
            "Prerequisites\n\n"
            "* The machine has two or more network interfaces.\n"
            "* You are logged in to the RHEL web console.\n\n"
            "Procedure\n\n"
            "1. Click Networking in the navigation.\n"
            "2. Click Add bridge in the Interfaces section.\n"
            "3. Enter a name for the bridge device.\n"
            "4. Select the interfaces that should be ports of the bridge.\n"
            "5. Optional: Configure further settings.\n\n"
            "Verification\n\n"
            "1. Select the bridge interface and verify the settings.\n"
        )
        assert _detect_content_type(text) == "procedure"


class TestAmbiguousContent:
    """Ambiguous content — returns None for popup trigger."""

    def test_generic_prose_returns_none(self):
        text = "This is a paragraph of generic text without any markers."
        assert _detect_content_type(text) is None

    def test_empty_text_returns_none(self):
        assert _detect_content_type("") is None

    def test_short_text_returns_none(self):
        text = "Hello world."
        assert _detect_content_type(text) is None

    def test_below_threshold_returns_none(self):
        """Single numbered step (< 3 threshold) is not enough."""
        text = "Some text.\n1. One step only."
        assert _detect_content_type(text) is None


class TestUserSelectedFlag:
    """Orchestrator respects user_selected flag."""

    def test_resolve_detected_content_type_auto(self):
        from app.services.analysis.orchestrator import _resolve_detected_content_type
        result = _resolve_detected_content_type("concept", "procedure", False)
        assert result == "procedure"

    def test_resolve_detected_content_type_user_selected(self):
        from app.services.analysis.orchestrator import _resolve_detected_content_type
        result = _resolve_detected_content_type("procedure", "concept", True)
        assert result == "procedure"

    def test_resolve_detected_content_type_no_detection(self):
        from app.services.analysis.orchestrator import _resolve_detected_content_type
        result = _resolve_detected_content_type("concept", None, False)
        assert result == "concept"


class TestReleaseNotesEnum:
    """ContentType enum accepts release_notes."""

    def test_release_notes_value(self):
        from app.models.enums import ContentType
        ct = ContentType("release_notes")
        assert ct == ContentType.RELEASE_NOTES
        assert ct.value == "release_notes"
