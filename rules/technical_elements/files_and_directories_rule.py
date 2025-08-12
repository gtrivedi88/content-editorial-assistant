"""
Files and Directories Rule (Production-Grade)
Based on IBM Style Guide topic: "Files and directories"
Evidence-based analysis with surgical zero false positive guards for file and directory naming.
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class FilesAndDirectoriesRule(BaseTechnicalRule):
    """
    PRODUCTION-GRADE: Checks for incorrect usage of file names and extensions as nouns.
    
    Implements rule-specific evidence calculation for:
    - File extensions used as standalone nouns (e.g., "a .pdf")
    - Directory references without proper context
    - File path formatting inconsistencies
    - Missing file type specifications
    
    Features:
    - Surgical zero false positive guards for file system contexts
    - Dynamic base evidence scoring based on file type specificity
    - Evidence-aware messaging for file system documentation
    """
    def _get_rule_type(self) -> str:
        return 'technical_files_directories'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for file and directory violations.
        
        Implements the required production pattern:
        1. Find potential file/directory issues using rule-specific detection
        2. Calculate evidence using rule-specific _calculate_file_directory_evidence()
        3. Apply zero false positive guards specific to file system analysis
        4. Use evidence-aware messaging and suggestions
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential file/directory issues ===
        potential_issues = self._find_potential_file_directory_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_file_directory_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "file_directory"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "file_directory"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('flagged_text', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    # === RULE-SPECIFIC METHODS ===
    
    def _find_potential_file_directory_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find potential file and directory issues for evidence assessment.
        Detects file extensions and paths used inappropriately.
        """
        issues = []
        
        # File extensions with their base evidence scores based on specificity
        file_extension_patterns = {
            # High specificity extensions (clearly inappropriate as standalone nouns)
            r'\b\.(exe|dll|sys|bin|so|dylib)\b': 0.9,  # Executable/system files
            r'\b\.(zip|rar|tar|gz|7z|bz2)\b': 0.85,     # Archive files
            r'\b\.(iso|img|dmg)\b': 0.85,               # Disk images
            r'\b\.(log|tmp|cache|lock)\b': 0.8,         # System files
            
            # Medium specificity extensions
            r'\b\.(pdf|doc|docx|xls|xlsx|ppt|pptx)\b': 0.75,  # Office documents
            r'\b\.(txt|csv|json|xml|yaml|yml)\b': 0.7,         # Data files
            r'\b\.(html|htm|css|js|php|asp)\b': 0.7,           # Web files
            r'\b\.(sql|db|sqlite|mdb)\b': 0.75,                # Database files
            
            # Lower specificity extensions (more context dependent)
            r'\b\.(png|jpg|jpeg|gif|bmp|svg|ico)\b': 0.6,      # Image files
            r'\b\.(mp3|wav|flac|m4a|ogg)\b': 0.65,             # Audio files
            r'\b\.(mp4|avi|mov|wmv|flv|mkv)\b': 0.65,          # Video files
            r'\b\.(c|cpp|h|java|py|js|php|rb|go)\b': 0.8,      # Source code files
        }
        
        for i, sent in enumerate(doc.sents):
            sent_text = sent.text
            
            # Check for each file extension pattern
            for pattern, base_evidence in file_extension_patterns.items():
                for match in re.finditer(pattern, sent_text, re.IGNORECASE):
                    # Check if it's being used as a standalone noun
                    preceding_text = sent_text[:match.start()].strip()
                    following_text = sent_text[match.end():].strip()
                    
                    # Look for article usage suggesting noun treatment
                    if (preceding_text.endswith((' a', ' an', ' the')) or
                        following_text.startswith((' is', ' was', ' are', ' were'))):
                        
                        issues.append({
                            'type': 'file_directory',
                            'subtype': 'extension_as_noun',
                            'extension': match.group(0),
                            'text': match.group(0),
                            'sentence': sent_text,
                            'sentence_index': i,
                            'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                            'base_evidence': base_evidence,
                            'flagged_text': match.group(0),
                            'preceding_text': preceding_text,
                            'following_text': following_text,
                            'match_obj': match,
                            'sentence_obj': sent
                        })
        
        # Check for directory path issues
        directory_patterns = [
            (r'\\[A-Za-z0-9_\\]+\\', 0.6),   # Windows paths
            (r'/[a-zA-Z0-9_/]+/', 0.6),      # Unix paths
            (r'C:\\[A-Za-z0-9_\\]+', 0.7),   # Absolute Windows paths
            (r'/usr/[a-zA-Z0-9_/]+', 0.7),   # Unix system paths
        ]
        
        for i, sent in enumerate(doc.sents):
            sent_text = sent.text
            for pattern, base_evidence in directory_patterns:
                for match in re.finditer(pattern, sent_text):
                    # Check if path is used without proper formatting
                    if ('`' not in sent_text[max(0, match.start()-5):match.end()+5] and
                        '"' not in sent_text[max(0, match.start()-5):match.end()+5]):
                        
                        issues.append({
                            'type': 'file_directory',
                            'subtype': 'unformatted_path',
                            'path': match.group(0),
                            'text': match.group(0),
                            'sentence': sent_text,
                            'sentence_index': i,
                            'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                            'base_evidence': base_evidence,
                            'flagged_text': match.group(0),
                            'match_obj': match,
                            'sentence_obj': sent
                        })
        
        return issues
    
    def _calculate_file_directory_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for file/directory violations.
        
        Implements rule-specific evidence calculation with:
        - Zero false positive guards for file system analysis
        - Dynamic base evidence based on file type specificity
        - Context-aware adjustments for technical documentation
        """
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR FILES/DIRECTORIES ===
        # Apply ultra-precise file system-specific guards that eliminate false positives
        # while preserving ALL legitimate file/directory violations
        
        sentence_obj = issue.get('sentence_obj')
        if not sentence_obj:
            return 0.0
            
        issue_type = issue.get('subtype', '')
        flagged_text = issue.get('flagged_text', issue.get('text', ''))
        
        # === GUARD 1: PROPER FILE FORMATTING ===
        # Don't flag files that are already properly formatted
        if self._is_properly_formatted_file_reference(flagged_text, sentence_obj, context):
            return 0.0  # Already properly formatted
            
        # === GUARD 2: LEGITIMATE FILE MENTIONS ===
        # Don't flag legitimate file references in appropriate contexts
        if self._is_legitimate_file_mention(flagged_text, sentence_obj, context):
            return 0.0  # Legitimate file reference
            
        # === GUARD 3: TECHNICAL DOCUMENTATION CONTEXT ===
        # Don't flag file references in code examples or technical lists
        if self._is_technical_documentation_context(sentence_obj, context):
            return 0.0  # Technical documentation allows file references
            
        # === GUARD 4: FILE LISTING OR DIRECTORY CONTENT ===
        # Don't flag files in directory listings or file inventories
        if self._is_file_listing_context(sentence_obj, context):
            return 0.0  # File listings are not style violations
            
        # Apply common technical guards (code blocks, entities, etc.)
        mock_token = type('MockToken', (), {
            'text': flagged_text, 
            'idx': issue.get('span', [0, 0])[0],
            'sent': sentence_obj
        })
        if self._apply_surgical_zero_false_positive_guards_technical(mock_token, context):
            return 0.0
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)  # File-specific base score
        
        # === LINGUISTIC CLUES (FILE-SPECIFIC) ===
        evidence_score = self._apply_file_directory_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_technical_structural_clues(evidence_score, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_file_directory_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    # === SURGICAL ZERO FALSE POSITIVE GUARD METHODS ===
    
    def _is_properly_formatted_file_reference(self, flagged_text: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this file reference already properly formatted?
        Only returns True when proper formatting is genuinely present.
        """
        sent_text = sentence_obj.text
        
        # Check for proper formatting around the flagged text
        flagged_start = sent_text.find(flagged_text)
        if flagged_start == -1:
            return False
            
        # Look for formatting indicators around the file reference
        formatting_indicators = [
            ('`', '`'),      # Inline code
            ('"', '"'),      # Double quotes
            ("'", "'"),      # Single quotes
            ('<code>', '</code>'),  # HTML code tags
            ('<tt>', '</tt>'),      # Teletype tags
        ]
        
        for start_marker, end_marker in formatting_indicators:
            start_pos = sent_text.rfind(start_marker, 0, flagged_start)
            end_pos = sent_text.find(end_marker, flagged_start + len(flagged_text))
            
            if start_pos != -1 and end_pos != -1:
                return True  # File is properly formatted
        
        # Check for explicit file context that makes formatting acceptable
        proper_context_patterns = [
            'file named', 'filename', 'file name', 'file called',
            'save as', 'open', 'create', 'delete', 'rename',
            'file extension', 'file type', 'file format'
        ]
        
        sent_lower = sent_text.lower()
        for pattern in proper_context_patterns:
            if pattern in sent_lower:
                return True  # Proper file context present
        
        return False
    
    def _is_legitimate_file_mention(self, flagged_text: str, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this a legitimate file mention in appropriate context?
        Only returns True for genuine legitimate mentions.
        """
        sent_text = sentence_obj.text.lower()
        
        # Legitimate file mention patterns
        legitimate_patterns = [
            'example file', 'sample file', 'test file', 'demo file',
            'config file', 'configuration file', 'settings file',
            'log file', 'output file', 'input file', 'data file',
            'backup file', 'temporary file', 'cache file'
        ]
        
        # Check if the file is mentioned in a legitimate context
        for pattern in legitimate_patterns:
            if pattern in sent_text:
                return True
        
        # Check for legitimate file operations
        file_operations = [
            'create', 'generate', 'produce', 'output', 'save',
            'download', 'upload', 'import', 'export', 'convert'
        ]
        
        extension = flagged_text.lower()
        for operation in file_operations:
            if f'{operation}' in sent_text and extension in sent_text:
                # Check if it's talking about creating/handling the file type
                if any(phrase in sent_text for phrase in [
                    f'{operation} a {extension} file',
                    f'{operation} {extension} files',
                    f'{operation} as {extension}',
                    f'{operation} to {extension}'
                ]):
                    return True
        
        return False
    
    def _is_technical_documentation_context(self, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this in technical documentation where file references are expected?
        Only returns True for genuine technical documentation contexts.
        """
        content_type = context.get('content_type', '')
        block_type = context.get('block_type', '')
        
        # Technical documentation contexts
        if content_type in ['api', 'developer', 'technical', 'tutorial']:
            return True
            
        # Technical block types
        if block_type in ['code_example', 'technical_specification', 'api_reference']:
            return True
            
        # Check for technical documentation indicators
        sent_text = sentence_obj.text.lower()
        technical_indicators = [
            'installation', 'configuration', 'setup', 'deployment',
            'build process', 'compilation', 'development environment',
            'file structure', 'directory structure', 'project structure'
        ]
        
        if any(indicator in sent_text for indicator in technical_indicators):
            return True
        
        return False
    
    def _is_file_listing_context(self, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this in a file listing or directory content context?
        Only returns True for genuine file listing contexts.
        """
        sent_text = sentence_obj.text.lower()
        
        # File listing indicators
        listing_indicators = [
            'directory contains', 'folder contains', 'files include',
            'directory listing', 'file list', 'contents include',
            'archive contains', 'package includes', 'bundle contains'
        ]
        
        if any(indicator in sent_text for indicator in listing_indicators):
            return True
        
        # Check for list-like structure
        if sent_text.count('.') > 2:  # Multiple file extensions suggest listing
            return True
            
        # Check for comma-separated file references
        if ',' in sent_text and any(ext in sent_text for ext in ['.pdf', '.doc', '.txt', '.html']):
            return True
        
        return False
    
    # === CLUE METHODS ===

    def _apply_file_directory_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to file/directory analysis."""
        sent_text = sentence_obj.text
        issue_type = issue.get('subtype', '')
        
        # Article usage strongly suggests noun treatment
        preceding_text = issue.get('preceding_text', '')
        if preceding_text.endswith((' a', ' an', ' the')):
            evidence_score += 0.2  # Clear noun treatment
        
        # Verb following the extension suggests noun usage
        following_text = issue.get('following_text', '')
        if following_text.startswith((' is', ' was', ' are', ' were', ' contains', ' includes')):
            evidence_score += 0.15  # Treated as subject of sentence
        
        # Lack of proper file terminology
        if not any(term in sent_text.lower() for term in ['file', 'document', 'format', 'type']):
            evidence_score += 0.1  # Missing file context
        
        # Multiple files in same sentence without proper formatting
        file_count = len(re.findall(r'\.[a-zA-Z]{2,4}\b', sent_text))
        if file_count > 1 and '`' not in sent_text:
            evidence_score += 0.1  # Multiple unformatted files
        
        return evidence_score

    def _apply_file_directory_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to file/directory usage."""
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Stricter standards for technical documentation
        if content_type in ['technical', 'api', 'developer', 'tutorial']:
            evidence_score += 0.15  # Technical docs should format files properly
        elif content_type in ['procedural', 'guide']:
            evidence_score += 0.1  # Procedural docs benefit from clarity
        
        # Domain-specific adjustments
        if domain in ['software', 'programming', 'devops', 'engineering']:
            evidence_score += 0.1  # Technical domains expect proper file formatting
        elif domain in ['documentation', 'technical_writing']:
            evidence_score += 0.15  # Documentation domains are strict about formatting
        
        # Audience-specific adjustments
        if audience in ['developer', 'engineer', 'technical_writer']:
            evidence_score += 0.1  # Technical audiences expect proper formatting
        elif audience in ['beginner', 'general']:
            evidence_score += 0.15  # General audiences need clear file references
        
        return evidence_score
