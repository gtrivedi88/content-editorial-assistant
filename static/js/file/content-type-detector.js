/**
 * Content Type Detector — lightweight frontend mirror of the backend's
 * 4-tier weighted multi-type scoring engine.
 *
 * Used ONLY to decide popup vs. no-popup before analysis begins.
 * The badge ALWAYS reflects the backend's response.detected_content_type,
 * never this detector's output (Trap 2 fix).
 *
 * Trap 1 fix: all regexes include the `m` (multiline) flag.
 * Trap 3 fix: \u00a0 handles non-breaking spaces from browser paste.
 * Trap 4 fix: no `g` flag on existence-check regexes; `String.match()`
 *             for counting (avoids lastIndex state mutation).
 */

// Tier 2: Structural markers — existence checks only (no 'g' flag)
const _STRUCT_PROCEDURE_RE = /^(?:\.)?(Procedure|Prerequisites|Verification|Troubleshooting)\s*$/im;
const _STRUCT_REFERENCE_RE = /^(?:\.)?(Additional resources|Related information)\s*$/im;

// Tier 3: Lexical title guard — existence checks only (no 'g' flag)
const _CONCEPT_TITLE_RE = /^(?:=\s+)?(About|Understanding|Architecture|Introduction)\b/im;
const _PROCEDURE_TITLE_RE = /^(?:=\s+)?(Configuring|Creating|Installing|Managing|Updating|Using|Adding|Removing|Deploying|Enabling|Setting)\b/im;
const _REFERENCE_TITLE_RE = /^(?:=\s+)?.*(?:Reference|Parameters|Properties|Commands|Variables|Attributes)\s*$/im;

// Tier 4: Content shape — 'g' flag needed for counting
const _NUMBERED_STEPS_RE = /^\d+\.\s+[A-Z]/gm;
const _IMPERATIVE_STEPS_RE = /^\d+\.\s+(?:Click|Select|Enter|Run|Type|Open|Navigate|Configure|Set|Add|Remove|Create|Install|Enable|Disable|Verify|Check|Ensure)\b/gm;
const _OPTIONAL_PREFIX_RE = /^Optional:/im;
const _TABLE_MARKER_RE = /^\|===/gm;
const _DEF_LIST_RE = /::\s*$/gm;

// Tier 1: Metadata — AsciiDoc attribute (existence check, no 'g')
const _CONTENT_TYPE_ATTR_RE = /:_mod-docs-content-type:\s*(CONCEPT|PROCEDURE|REFERENCE|ASSEMBLY)/im;

/**
 * Count regex matches using String.match() to avoid lastIndex mutation.
 *
 * @param {RegExp} re - A global regex (must have 'g' flag)
 * @param {string} text - The text to search
 * @returns {number} Number of matches
 */
function _countMatches(re, text) {
    const matches = text.match(re);
    return matches ? matches.length : 0;
}

/**
 * Detect content type from text using the same 4-tier weighted scoring
 * as the backend preprocessor.
 *
 * @param {string} text - Plain text content to analyze
 * @returns {string|null} Detected type ('procedure', 'concept', 'reference')
 *                        or null if ambiguous (triggers popup)
 */
export function detectContentType(text) {
    if (!text || !text.trim()) return null;

    // Tier 1: explicit AsciiDoc attribute → instant win
    const attrMatch = text.match(_CONTENT_TYPE_ATTR_RE);
    if (attrMatch) {
        return attrMatch[1].toLowerCase();
    }

    // Tiers 2-4: multi-type scoring
    const scores = { procedure: 0, concept: 0, reference: 0 };

    // Tier 2: structural markers (+20 each)
    if (_STRUCT_PROCEDURE_RE.test(text)) {
        // Check which specific markers are present
        const lines = text.split('\n');
        for (const line of lines) {
            const trimmed = line.replace(/^\.*/, '').trim().toLowerCase();
            if (trimmed === 'procedure') scores.procedure += 20;
            if (trimmed === 'prerequisites') scores.procedure += 20;
            if (trimmed === 'verification') scores.procedure += 20;
            if (trimmed === 'troubleshooting') scores.procedure += 20;
        }
    }

    if (_STRUCT_REFERENCE_RE.test(text)) {
        scores.reference += 20;
    }

    // Tier 3: lexical title guard (+10)
    if (_CONCEPT_TITLE_RE.test(text)) scores.concept += 10;
    if (_PROCEDURE_TITLE_RE.test(text)) scores.procedure += 10;
    if (_REFERENCE_TITLE_RE.test(text)) scores.reference += 10;

    // Tier 4: content shape (+5)
    if (_countMatches(_NUMBERED_STEPS_RE, text) >= 3) scores.procedure += 5;
    if (_countMatches(_IMPERATIVE_STEPS_RE, text) >= 2) scores.procedure += 5;
    if (_OPTIONAL_PREFIX_RE.test(text)) scores.procedure += 5;

    const tables = _countMatches(_TABLE_MARKER_RE, text);
    const defLists = _countMatches(_DEF_LIST_RE, text);
    if (tables > 0 || defLists > 2) scores.reference += 5;

    // Winner takes all — must meet threshold of 5
    let best = 'procedure';
    if (scores.concept > scores[best]) best = 'concept';
    if (scores.reference > scores[best]) best = 'reference';

    if (scores[best] >= 5) return best;

    return null;
}
