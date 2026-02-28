/**
 * IBM Style Guide group mapping — O(1) lookup from backend rule type to UI group.
 * Replaces error-categories.js (5 regex-based categories → 11 IBM Style Guide sections).
 */

const GROUPS = {
    audience_and_medium: {
        key: 'audience_and_medium',
        label: 'Audience and medium',
        icon: 'fas fa-users',
    },
    language_and_grammar: {
        key: 'language_and_grammar',
        label: 'Language and grammar',
        icon: 'fas fa-language',
    },
    punctuation: {
        key: 'punctuation',
        label: 'Punctuation',
        icon: 'fas fa-ellipsis',
    },
    numbers_and_measurement: {
        key: 'numbers_and_measurement',
        label: 'Numbers and measurement',
        icon: 'fas fa-hashtag',
    },
    structure_and_format: {
        key: 'structure_and_format',
        label: 'Structure and format',
        icon: 'fas fa-sitemap',
    },
    references: {
        key: 'references',
        label: 'References',
        icon: 'fas fa-quote-right',
    },
    technical_elements: {
        key: 'technical_elements',
        label: 'Technical elements',
        icon: 'fas fa-code',
    },
    legal_information: {
        key: 'legal_information',
        label: 'Legal information',
        icon: 'fas fa-gavel',
    },
    word_usage: {
        key: 'word_usage',
        label: 'Word usage',
        icon: 'fas fa-font',
    },
    modular_compliance: {
        key: 'modular_compliance',
        label: 'Modular compliance',
        icon: 'fas fa-puzzle-piece',
    },
    general: {
        key: 'general',
        label: 'General',
        icon: 'fas fa-check-circle',
    },
};

/**
 * Pre-built Map<ruleType, groupKey> for O(1) lookup.
 * Every backend rule type string maps to exactly one IBM Style Guide group.
 */
const TYPE_TO_GROUP = new Map([
    // audience_and_medium
    ['tone', 'audience_and_medium'],
    ['conversational_style', 'audience_and_medium'],
    ['accessibility', 'audience_and_medium'],
    ['global_audiences', 'audience_and_medium'],
    ['llm_consumability', 'audience_and_medium'],
    ['active_voice', 'audience_and_medium'],
    ['sentence_variety', 'audience_and_medium'],
    ['anthropomorphism', 'audience_and_medium'],

    // language_and_grammar
    ['spelling', 'language_and_grammar'],
    ['contractions', 'language_and_grammar'],
    ['capitalization', 'language_and_grammar'],
    ['abbreviations', 'language_and_grammar'],
    ['inclusive_language', 'language_and_grammar'],
    ['terminology', 'language_and_grammar'],
    ['plurals', 'language_and_grammar'],
    ['possessives', 'language_and_grammar'],
    ['prefixes', 'language_and_grammar'],
    ['verbs', 'language_and_grammar'],
    ['articles', 'language_and_grammar'],
    ['pronouns', 'language_and_grammar'],
    ['conjunctions', 'language_and_grammar'],
    ['prepositions', 'language_and_grammar'],
    ['adverbs_only', 'language_and_grammar'],

    // punctuation
    ['periods', 'punctuation'],
    ['commas', 'punctuation'],
    ['hyphens', 'punctuation'],
    ['semicolons', 'punctuation'],
    ['colons', 'punctuation'],
    ['quotation_marks', 'punctuation'],
    ['punctuation_and_symbols', 'punctuation'],
    ['dashes', 'punctuation'],
    ['ellipses', 'punctuation'],
    ['exclamation_points', 'punctuation'],
    ['slashes', 'punctuation'],
    ['spacing', 'punctuation'],
    ['parentheses', 'punctuation'],
    ['apostrophes', 'punctuation'],

    // numbers_and_measurement
    ['numbers_general', 'numbers_and_measurement'],
    ['numbers_currency', 'numbers_and_measurement'],
    ['dates_and_times', 'numbers_and_measurement'],
    ['numerals_vs_words', 'numbers_and_measurement'],
    ['units_of_measurement', 'numbers_and_measurement'],
    ['number_formatting', 'numbers_and_measurement'],
    ['date_time', 'numbers_and_measurement'],
    ['measurement_units', 'numbers_and_measurement'],
    ['currency', 'numbers_and_measurement'],

    // structure_and_format
    ['headings', 'structure_and_format'],
    ['lists', 'structure_and_format'],
    ['list_punctuation', 'structure_and_format'],
    ['list_consistency', 'structure_and_format'],
    ['list_parallelism', 'structure_and_format'],
    ['procedures', 'structure_and_format'],
    ['paragraphs', 'structure_and_format'],
    ['highlighting', 'structure_and_format'],
    ['indentation', 'structure_and_format'],
    ['admonitions', 'structure_and_format'],
    ['admonition_content', 'structure_and_format'],
    ['notes', 'structure_and_format'],
    ['messages', 'structure_and_format'],
    ['glossaries', 'structure_and_format'],
    ['self_referential_text', 'structure_and_format'],
    ['tables', 'structure_and_format'],

    // references
    ['references_citations', 'references'],
    ['references_geographic', 'references'],
    ['references_names_titles', 'references'],
    ['references_product_names', 'references'],
    ['references_product_versions', 'references'],
    ['citations', 'references'],
    ['geographic_locations', 'references'],
    ['names_and_titles', 'references'],
    ['product_names', 'references'],
    ['product_versions', 'references'],

    // technical_elements
    ['technical_code_examples', 'technical_elements'],
    ['technical_command_line_entry', 'technical_elements'],
    ['technical_command_syntax', 'technical_elements'],
    ['technical_commands', 'technical_elements'],
    ['technical_files_directories', 'technical_elements'],
    ['technical_keyboard_keys', 'technical_elements'],
    ['technical_menus_navigation', 'technical_elements'],
    ['technical_mouse_buttons', 'technical_elements'],
    ['technical_programming_elements', 'technical_elements'],
    ['technical_ui_elements', 'technical_elements'],
    ['technical_web_addresses', 'technical_elements'],
    ['code_examples', 'technical_elements'],
    ['command_line_entry', 'technical_elements'],
    ['command_syntax', 'technical_elements'],
    ['commands', 'technical_elements'],
    ['files_directories', 'technical_elements'],
    ['keyboard_keys', 'technical_elements'],
    ['menus_navigation', 'technical_elements'],
    ['mouse_buttons', 'technical_elements'],
    ['programming_elements', 'technical_elements'],
    ['ui_elements', 'technical_elements'],
    ['web_addresses', 'technical_elements'],

    // legal_information
    ['claims', 'legal_information'],
    ['company_names', 'legal_information'],
    ['personal_information', 'legal_information'],

    // word_usage (A-Z rules + special)
    ['word_usage_a', 'word_usage'],
    ['word_usage_b', 'word_usage'],
    ['word_usage_c', 'word_usage'],
    ['word_usage_d', 'word_usage'],
    ['word_usage_e', 'word_usage'],
    ['word_usage_f', 'word_usage'],
    ['word_usage_g', 'word_usage'],
    ['word_usage_h', 'word_usage'],
    ['word_usage_i', 'word_usage'],
    ['word_usage_j', 'word_usage'],
    ['word_usage_k', 'word_usage'],
    ['word_usage_l', 'word_usage'],
    ['word_usage_m', 'word_usage'],
    ['word_usage_n', 'word_usage'],
    ['word_usage_o', 'word_usage'],
    ['word_usage_p', 'word_usage'],
    ['word_usage_q', 'word_usage'],
    ['word_usage_r', 'word_usage'],
    ['word_usage_s', 'word_usage'],
    ['word_usage_t', 'word_usage'],
    ['word_usage_u', 'word_usage'],
    ['word_usage_v', 'word_usage'],
    ['word_usage_w', 'word_usage'],
    ['word_usage_x', 'word_usage'],
    ['word_usage_y', 'word_usage'],
    ['word_usage_z', 'word_usage'],
    ['word_usage_special', 'word_usage'],
    ['special_chars', 'word_usage'],

    // modular_compliance
    ['concept_module', 'modular_compliance'],
    ['procedure_module', 'modular_compliance'],
    ['reference_module', 'modular_compliance'],
    ['assembly_module', 'modular_compliance'],
    ['cross_reference_compliance', 'modular_compliance'],
    ['template_compliance', 'modular_compliance'],
    ['inter_module_analysis', 'modular_compliance'],
    ['cross_reference', 'modular_compliance'],

    // general (root-level rules)
    ['sentence_length', 'general'],
    ['second_person', 'general'],
]);

/**
 * Map a backend error type string to an IBM Style Guide group key.
 * @param {string} type - e.g. "word_usage_a", "spelling", "active_voice"
 * @returns {string} - group key, e.g. "language_and_grammar"
 */
export function getGroup(type) {
    if (!type) return 'general';
    return TYPE_TO_GROUP.get(type) || 'general';
}

/**
 * Get group metadata (label, icon).
 */
export function getGroupMeta(groupKey) {
    return GROUPS[groupKey] || GROUPS.general;
}

/**
 * Get all group keys in display order.
 */
export function getAllGroups() {
    return Object.keys(GROUPS);
}

/**
 * Format a rule type string for display.
 * "word_usage_a" → "Word Usage A", "active_voice" → "Active Voice"
 */
export function formatRuleType(type) {
    if (!type) return 'Unknown';
    return type
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
}
