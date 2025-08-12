#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing for Audience & Medium Rules
Tests all rules against diverse real-world scenarios to ensure production readiness.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None
    print("ERROR: SpaCy not available")
    sys.exit(1)

# Import from relative paths within the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tone_rule import ToneRule
from conversational_style_rule import ConversationalStyleRule
from global_audiences_rule import GlobalAudiencesRule
from llm_consumability_rule import LLMConsumabilityRule

def test_audience_medium_comprehensive():
    print("🎯 COMPREHENSIVE AUDIENCE & MEDIUM RULES TEST")
    print("Testing all rules against diverse real-world scenarios")
    print("=" * 80)
    
    test_scenarios = [
        # === TONE RULE SCENARIOS ===
        {
            "rule": ToneRule(),
            "category": "Business Communication",
            "content": "This solution is a slam dunk that will leverage our core competencies to pick the low-hanging fruit.",
            "context": {"content_type": "business", "audience": "executive", "domain": "corporate"},
            "should_detect": True,
            "expected_terms": ["slam dunk", "leverage", "low-hanging fruit"],
            "description": "Business jargon in corporate communication"
        },
        {
            "rule": ToneRule(),
            "content": "The algorithm leverages machine learning to optimize performance through data-driven insights.",
            "context": {"content_type": "technical", "audience": "developer", "domain": "ai"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Technical leverage usage (legitimate)"
        },
        {
            "rule": ToneRule(),
            "content": "Our API is cutting-edge and provides best-in-class performance for enterprise solutions.",
            "context": {"content_type": "marketing", "audience": "business", "domain": "enterprise"},
            "should_detect": True,
            "expected_terms": ["cutting-edge", "best-in-class"],
            "description": "Marketing buzzwords"
        },
        {
            "rule": ToneRule(),
            "content": "As the CEO mentioned: \"This is a game-changer that will disrupt the industry.\"",
            "context": {"content_type": "news", "audience": "media", "block_type": "quote"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Quoted business language (should be exempt)"
        },
        
        # === CONVERSATIONAL STYLE RULE SCENARIOS ===
        {
            "rule": ConversationalStyleRule(),
            "category": "Technical Documentation",
            "content": "Subsequently, one must utilize the aforementioned methodology to accomplish the desired outcome.",
            "context": {"content_type": "technical", "audience": "developer", "domain": "documentation"},
            "should_detect": True,
            "expected_terms": ["subsequently", "aforementioned", "utilize"],
            "description": "Overly formal technical writing"
        },
        {
            "rule": ConversationalStyleRule(),
            "content": "Use the `configure()` method to set up your application.",
            "context": {"content_type": "technical", "audience": "developer", "block_type": "inline_code"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Code context (should be exempt)"
        },
        {
            "rule": ConversationalStyleRule(),
            "content": "The API endpoint facilitates the transmission of data between client and server applications.",
            "context": {"content_type": "technical", "audience": "expert", "domain": "api"},
            "should_detect": True,
            "expected_terms": ["facilitates", "transmission"],
            "description": "Formal API documentation"
        },
        {
            "rule": ConversationalStyleRule(),
            "content": "Click the button to save your changes.",
            "context": {"content_type": "tutorial", "audience": "beginner", "domain": "ui"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Simple instructional language"
        },
        
        # === GLOBAL AUDIENCES RULE SCENARIOS ===
        {
            "rule": GlobalAudiencesRule(),
            "category": "User Interface",
            "content": "Don't forget to save your work before you close the application.",
            "context": {"content_type": "ui", "audience": "global", "domain": "software"},
            "should_detect": True,
            "expected_terms": ["Don't"],
            "description": "Negative construction in UI"
        },
        {
            "rule": GlobalAudiencesRule(),
            "content": "You can't access this feature without premium subscription.",
            "context": {"content_type": "error", "audience": "global", "domain": "subscription"},
            "should_detect": True,
            "expected_terms": ["can't"],
            "description": "Negative construction in error message"
        },
        {
            "rule": GlobalAudiencesRule(),
            "content": "This comprehensive documentation explains the implementation details, configuration options, security considerations, and troubleshooting procedures for the entire system architecture.",
            "context": {"content_type": "documentation", "audience": "global", "domain": "technical"},
            "should_detect": True,
            "expected_terms": ["sentence length"],
            "description": "Very long sentence for global audiences"
        },
        {
            "rule": GlobalAudiencesRule(),
            "content": "Save your work frequently.",
            "context": {"content_type": "ui", "audience": "global", "domain": "software"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Positive, simple instruction"
        },
        {
            "rule": GlobalAudiencesRule(),
            "content": "The `npm install` command won't work without proper permissions.",
            "context": {"content_type": "technical", "audience": "developer", "block_type": "code_block"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Code context (should be exempt)"
        },
        
        # === LLM CONSUMABILITY RULE SCENARIOS ===
        {
            "rule": LLMConsumabilityRule(),
            "category": "Content Completeness",
            "content": "Overview",
            "context": {"content_type": "documentation", "audience": "general", "block_type": "heading"},
            "should_detect": True,
            "expected_terms": ["incomplete"],
            "description": "Single word heading (incomplete)"
        },
        {
            "rule": LLMConsumabilityRule(),
            "content": "API Documentation Overview",
            "context": {"content_type": "documentation", "audience": "developer", "block_type": "heading"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Complete heading"
        },
        {
            "rule": LLMConsumabilityRule(),
            "content": "This feature works.",
            "context": {"content_type": "documentation", "audience": "general", "block_type": "paragraph"},
            "should_detect": True,
            "expected_terms": ["short"],
            "description": "Very short explanation"
        },
        {
            "rule": LLMConsumabilityRule(),
            "content": "This authentication feature works by validating user credentials against the configured identity provider and establishing a secure session.",
            "context": {"content_type": "documentation", "audience": "general", "block_type": "paragraph"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Adequate explanation length"
        },
        {
            "rule": LLMConsumabilityRule(),
            "content": "Install dependencies",
            "context": {"content_type": "tutorial", "audience": "developer", "block_type": "step"},
            "should_detect": True,
            "expected_terms": ["incomplete"],
            "description": "Incomplete step description"
        },
        {
            "rule": LLMConsumabilityRule(),
            "content": "API.",
            "context": {"content_type": "technical", "audience": "developer", "block_type": "paragraph"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Technical identifier (should be exempt)"
        },
        
        # === EDGE CASE SCENARIOS ===
        {
            "rule": ToneRule(),
            "category": "Code Documentation",
            "content": "// This is a game-changer function that leverages async programming",
            "context": {"content_type": "technical", "audience": "developer", "block_type": "code_comment"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Business jargon in code comments (should be exempt)"
        },
        {
            "rule": ConversationalStyleRule(),
            "content": "The aforementioned configuration facilitates optimal performance.",
            "context": {"content_type": "legal", "audience": "legal", "domain": "compliance"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Formal language in legal context (appropriate)"
        },
        {
            "rule": GlobalAudiencesRule(),
            "content": "Don't use this API endpoint as it's deprecated.",
            "context": {"content_type": "technical", "audience": "developer", "domain": "api"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Negative construction in technical warning (appropriate)"
        },
        
        # === MIXED CONTENT SCENARIOS ===
        {
            "rule": ToneRule(),
            "category": "Mixed Content",
            "content": "Our cutting-edge platform leverages AI to deliver best-in-class solutions that are real game-changers.",
            "context": {"content_type": "marketing", "audience": "customer", "domain": "ai"},
            "should_detect": True,
            "expected_terms": ["cutting-edge", "leverages", "best-in-class", "game-changers"],
            "description": "Multiple business jargon terms"
        },
        {
            "rule": ConversationalStyleRule(),
            "content": "Subsequently, users must utilize the aforementioned configuration to facilitate proper functionality.",
            "context": {"content_type": "tutorial", "audience": "beginner", "domain": "software"},
            "should_detect": True,
            "expected_terms": ["subsequently", "utilize", "aforementioned", "facilitate"],
            "description": "Multiple formal terms in beginner content"
        },
        
        # === CONTEXT-SPECIFIC SCENARIOS ===
        {
            "rule": ToneRule(),
            "category": "Domain-Specific",
            "content": "This solution leverages blockchain technology for enterprise applications.",
            "context": {"content_type": "technical", "audience": "expert", "domain": "blockchain"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Domain-appropriate technical language"
        },
        {
            "rule": LLMConsumabilityRule(),
            "content": "Error: Connection failed",
            "context": {"content_type": "error", "audience": "user", "block_type": "message"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Error message (appropriate brevity)"
        }
    ]
    
    total_tests = len(test_scenarios)
    passed_tests = 0
    category_results = {}
    rule_results = {}
    
    for i, scenario in enumerate(test_scenarios, 1):
        rule = scenario["rule"]
        rule_name = type(rule).__name__
        category = scenario.get("category", rule_name)
        content = scenario["content"]
        context = scenario["context"]
        should_detect = scenario["should_detect"]
        expected_terms = scenario["expected_terms"]
        description = scenario["description"]
        
        # Track category and rule results
        if category not in category_results:
            category_results[category] = {"total": 0, "passed": 0}
        category_results[category]["total"] += 1
        
        if rule_name not in rule_results:
            rule_results[rule_name] = {"total": 0, "passed": 0}
        rule_results[rule_name]["total"] += 1
        
        print(f"\n🧪 Test {i}/{total_tests}: {category}")
        print(f"📝 {description}")
        print(f"📄 Content: '{content[:80]}{'...' if len(content) > 80 else ''}'")
        print(f"🎯 Rule: {rule_name}")
        
        # Run the rule
        errors = rule.analyze(content, [content], nlp, context)
        
        has_detection = len(errors) > 0
        detected_terms = []
        evidence_scores = []
        
        if errors:
            for error in errors:
                flagged_text = error.get('flagged_text', '')
                evidence_score = error.get('evidence_score', 0.0)
                detected_terms.append(flagged_text)
                evidence_scores.append(evidence_score)
        
        # Validate results
        detection_correct = has_detection == should_detect
        
        terms_correct = True
        if should_detect and expected_terms:
            # For LLM rule, check for general concepts rather than exact terms
            if rule_name == "LLMConsumabilityRule":
                # Check if any expected concept is mentioned in detected terms or error messages
                found_concepts = []
                for expected in expected_terms:
                    if any(expected.lower() in detected.lower() for detected in detected_terms):
                        found_concepts.append(expected)
                    elif errors and any(expected.lower() in str(error).lower() for error in errors):
                        found_concepts.append(expected)
                terms_correct = len(found_concepts) > 0 if expected_terms else True
            else:
                # Exact term matching for other rules
                for expected in expected_terms:
                    found = any(expected.lower() in detected.lower() for detected in detected_terms)
                    if not found:
                        terms_correct = False
                        break
        
        passed = detection_correct and terms_correct
        
        if passed:
            passed_tests += 1
            category_results[category]["passed"] += 1
            rule_results[rule_name]["passed"] += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"🎯 Expected Detection: {should_detect} | Got: {has_detection}")
        
        if expected_terms:
            print(f"🎯 Expected Terms/Concepts: {expected_terms}")
        if detected_terms:
            print(f"🔍 Detected Terms: {detected_terms}")
            print(f"📊 Evidence Scores: {[f'{score:.2f}' for score in evidence_scores]}")
        
        print(f"🏆 Result: {status}")
        
        if not passed:
            if not detection_correct:
                print(f"   ❌ Detection mismatch: expected {should_detect}, got {has_detection}")
            if not terms_correct:
                print(f"   ❌ Term/concept detection incorrect")
    
    # Summary by category
    print("\n" + "=" * 80)
    print("📊 RESULTS BY CATEGORY")
    print("=" * 80)
    
    for category, results in category_results.items():
        total = results["total"]
        passed = results["passed"]
        percentage = (passed / total) * 100 if total > 0 else 0
        status = "✅" if percentage == 100 else "❌"
        print(f"{status} {category:30} {passed}/{total} ({percentage:.1f}%)")
    
    # Summary by rule
    print("\n" + "=" * 80)
    print("📊 RESULTS BY RULE")
    print("=" * 80)
    
    for rule_name, results in rule_results.items():
        total = results["total"]
        passed = results["passed"]
        percentage = (passed / total) * 100 if total > 0 else 0
        status = "✅" if percentage == 100 else "❌"
        print(f"{status} {rule_name:30} {passed}/{total} ({percentage:.1f}%)")
    
    # Overall summary
    overall_percentage = (passed_tests / total_tests) * 100
    print("\n" + "=" * 80)
    print("🎯 OVERALL AUDIENCE & MEDIUM TEST RESULTS")
    print("=" * 80)
    print(f"Tests Passed: {passed_tests}/{total_tests} ({overall_percentage:.1f}%)")
    
    if overall_percentage == 100:
        print("🏆 ✅ PERFECT AUDIENCE & MEDIUM PERFORMANCE!")
        print("✅ All evidence-based features working correctly")
        print("✅ Zero false positives, zero false negatives")
        print("✅ Production-ready across all scenarios")
    elif overall_percentage >= 95:
        print("✅ EXCELLENT performance on audience & medium rules")
        print("⚠️  Minor edge cases detected")
    elif overall_percentage >= 90:
        print("✅ GOOD performance overall")
        print("🔧 Some issues need attention")
    else:
        print("❌ Performance issues detected")
        print("🚨 Requires immediate investigation")
    
    return overall_percentage

if __name__ == "__main__":
    success_rate = test_audience_medium_comprehensive()
