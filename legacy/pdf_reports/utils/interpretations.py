"""
Metrics Interpreter Module

Provides human-readable interpretations and insights for metrics.
Designed to help executives and writers understand their writing quality.
"""

from typing import Dict, Any, List
from collections import Counter


class MetricsInterpreter:
    """Generate human-readable interpretations of writing metrics."""
    
    @classmethod
    def interpret_grade_level(cls, grade_level: float) -> Dict[str, str]:
        """Interpret grade level with audience context."""
        if grade_level < 6:
            return {
                'category': 'Elementary',
                'audience': 'General public, beginners',
                'assessment': 'May be too simple for professional content',
                'recommendation': 'Consider adding more sophisticated vocabulary and sentence structures for professional credibility.',
                'icon': '📚'
            }
        elif grade_level < 9:
            return {
                'category': 'Middle School',
                'audience': 'Broad general audience',
                'assessment': 'Accessible but may lack technical authority',
                'recommendation': 'Good for user guides and general documentation. Consider the expertise level of your target audience.',
                'icon': '📖'
            }
        elif grade_level <= 11:
            return {
                'category': 'High School',
                'audience': 'Professional audience',
                'assessment': 'Ideal for most professional technical audiences',
                'recommendation': 'Excellent readability for technical documentation. Your content balances accessibility with professionalism.',
                'icon': '✅'
            }
        elif grade_level <= 13:
            return {
                'category': 'College',
                'audience': 'Technical professionals, specialists',
                'assessment': 'Appropriate for technical content with specialized audience',
                'recommendation': 'Good for expert-level documentation. Ensure your audience has the necessary background.',
                'icon': '🎓'
            }
        elif grade_level <= 16:
            return {
                'category': 'Graduate',
                'audience': 'Advanced specialists, researchers',
                'assessment': 'May be challenging for general readers',
                'recommendation': 'Consider simplifying complex sentences and reducing jargon for broader accessibility.',
                'icon': '📊'
            }
        else:
            return {
                'category': 'Post-Graduate',
                'audience': 'Domain experts only',
                'assessment': 'Very challenging for most readers',
                'recommendation': 'Strongly consider simplifying. Break down complex concepts and use clearer sentence structures.',
                'icon': '⚠️'
            }
    
    @classmethod
    def interpret_readability(cls, flesch_score: float) -> Dict[str, str]:
        """Interpret Flesch Reading Ease score."""
        if flesch_score >= 90:
            return {
                'category': 'Very Easy',
                'description': 'Easily understood by 5th graders',
                'assessment': 'Extremely accessible writing',
                'color': 'success'
            }
        elif flesch_score >= 80:
            return {
                'category': 'Easy',
                'description': 'Conversational English for consumers',
                'assessment': 'Very accessible writing',
                'color': 'success'
            }
        elif flesch_score >= 70:
            return {
                'category': 'Fairly Easy',
                'description': 'Understood by 7th graders',
                'assessment': 'Good accessibility',
                'color': 'success'
            }
        elif flesch_score >= 60:
            return {
                'category': 'Standard',
                'description': 'Plain English for most adults',
                'assessment': 'Appropriate for general professional content',
                'color': 'good'
            }
        elif flesch_score >= 50:
            return {
                'category': 'Fairly Difficult',
                'description': 'High school graduate level',
                'assessment': 'Suitable for educated readers',
                'color': 'warning'
            }
        elif flesch_score >= 30:
            return {
                'category': 'Difficult',
                'description': 'College graduate level',
                'assessment': 'May limit accessibility',
                'color': 'warning'
            }
        else:
            return {
                'category': 'Very Difficult',
                'description': 'Professional/academic level',
                'assessment': 'Consider simplifying for broader reach',
                'color': 'danger'
            }
    
    @classmethod
    def interpret_sentence_length(cls, avg_length: float) -> Dict[str, str]:
        """Interpret average sentence length."""
        if avg_length < 10:
            return {
                'assessment': 'Sentences may be too choppy',
                'recommendation': 'Consider combining related ideas for better flow.',
                'status': 'warning'
            }
        elif avg_length < 15:
            return {
                'assessment': 'Concise sentences, good for technical writing',
                'recommendation': 'Excellent for step-by-step instructions and quick reads.',
                'status': 'success'
            }
        elif avg_length <= 20:
            return {
                'assessment': 'Ideal sentence length for professional communication',
                'recommendation': 'Perfect balance of detail and readability.',
                'status': 'success'
            }
        elif avg_length <= 25:
            return {
                'assessment': 'Sentences getting lengthy',
                'recommendation': 'Consider breaking some sentences for better clarity.',
                'status': 'warning'
            }
        else:
            return {
                'assessment': 'Sentences too long for easy comprehension',
                'recommendation': 'Break into shorter, clearer statements. Aim for 15-20 words.',
                'status': 'danger'
            }
    
    @classmethod
    def interpret_passive_voice(cls, percentage: float) -> Dict[str, str]:
        """Interpret passive voice percentage."""
        if percentage <= 10:
            return {
                'assessment': 'Excellent use of active voice',
                'recommendation': 'Your writing is direct and engaging. Great job!',
                'status': 'success'
            }
        elif percentage <= 15:
            return {
                'assessment': 'Good active voice usage',
                'recommendation': 'Well-balanced writing with appropriate passive voice where needed.',
                'status': 'success'
            }
        elif percentage <= 25:
            return {
                'assessment': 'Acceptable but could improve',
                'recommendation': 'Consider converting some passive constructions to active voice for stronger impact.',
                'status': 'warning'
            }
        else:
            return {
                'assessment': 'Too much passive voice',
                'recommendation': 'Actively rewrite sentences for stronger, clearer communication.',
                'status': 'danger'
            }
    
    @classmethod
    def interpret_complex_words(cls, percentage: float) -> Dict[str, str]:
        """Interpret complex words percentage."""
        if percentage <= 15:
            return {
                'assessment': 'Accessible vocabulary',
                'recommendation': 'Good balance of simple and complex terms.',
                'status': 'success'
            }
        elif percentage <= 20:
            return {
                'assessment': 'Moderate complexity',
                'recommendation': 'Appropriate for professional content.',
                'status': 'success'
            }
        elif percentage <= 30:
            return {
                'assessment': 'Higher complexity vocabulary',
                'recommendation': 'Consider simpler alternatives for non-essential technical terms.',
                'status': 'warning'
            }
        else:
            return {
                'assessment': 'High vocabulary complexity',
                'recommendation': 'Simplify where possible. Use technical terms only when necessary.',
                'status': 'danger'
            }
    
    @classmethod
    def interpret_vocabulary_diversity(cls, diversity: float) -> Dict[str, str]:
        """Interpret vocabulary diversity (type-token ratio)."""
        if diversity >= 0.8:
            return {
                'assessment': 'Excellent vocabulary variety',
                'recommendation': 'Rich vocabulary keeps readers engaged.',
                'status': 'success'
            }
        elif diversity >= 0.6:
            return {
                'assessment': 'Good vocabulary diversity',
                'recommendation': 'Healthy mix of repeated and varied terms.',
                'status': 'success'
            }
        elif diversity >= 0.4:
            return {
                'assessment': 'Moderate diversity',
                'recommendation': 'Consider using synonyms to reduce repetition.',
                'status': 'warning'
            }
        else:
            return {
                'assessment': 'Limited vocabulary diversity',
                'recommendation': 'Vary word choices to make content more engaging.',
                'status': 'danger'
            }
    
    @classmethod
    def interpret_fog_index(cls, fog_index: float) -> Dict[str, str]:
        """Interpret Gunning Fog Index."""
        if fog_index <= 8:
            return {
                'assessment': 'Very easy to read',
                'education': 'Elementary school level',
                'status': 'success'
            }
        elif fog_index <= 10:
            return {
                'assessment': 'Easy to read',
                'education': 'High school freshman',
                'status': 'success'
            }
        elif fog_index <= 12:
            return {
                'assessment': 'Good for technical documentation',
                'education': 'High school senior',
                'status': 'success'
            }
        elif fog_index <= 14:
            return {
                'assessment': 'Moderately complex',
                'education': 'College level',
                'status': 'warning'
            }
        else:
            return {
                'assessment': 'Complex text',
                'education': 'Post-graduate level',
                'status': 'danger'
            }
    
    @classmethod
    def interpret_overall_score(cls, score: float) -> Dict[str, str]:
        """Interpret overall writing quality score."""
        if score >= 90:
            return {
                'grade': 'A+',
                'category': 'Exceptional',
                'description': 'Publication-ready content with excellent readability and style.',
                'color': 'success'
            }
        elif score >= 80:
            return {
                'grade': 'A',
                'category': 'Excellent',
                'description': 'High-quality writing that meets professional standards.',
                'color': 'success'
            }
        elif score >= 70:
            return {
                'grade': 'B',
                'category': 'Good',
                'description': 'Solid writing with minor areas for improvement.',
                'color': 'good'
            }
        elif score >= 60:
            return {
                'grade': 'C',
                'category': 'Satisfactory',
                'description': 'Acceptable writing that would benefit from revision.',
                'color': 'warning'
            }
        elif score >= 50:
            return {
                'grade': 'D',
                'category': 'Needs Work',
                'description': 'Significant improvements recommended before publishing.',
                'color': 'warning'
            }
        else:
            return {
                'grade': 'F',
                'category': 'Requires Revision',
                'description': 'Major revisions needed for professional use.',
                'color': 'danger'
            }
    
    @classmethod
    def generate_executive_insights(cls, analysis_data: Dict[str, Any]) -> List[str]:
        """Generate key insights for executive summary."""
        insights = []
        
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        word_count = statistics.get('word_count', 0)
        
        # Word count insight
        if word_count > 0:
            if word_count < 100:
                insights.append(f"Brief content ({word_count} words) - suitable for quick reference.")
            elif word_count < 500:
                insights.append(f"Concise document ({word_count} words) - typical for focused topics.")
            elif word_count < 2000:
                insights.append(f"Substantial content ({word_count:,} words) - comprehensive coverage.")
            else:
                insights.append(f"Extensive document ({word_count:,} words) - consider breaking into sections.")
        
        # Readability insight
        flesch = technical_metrics.get('flesch_reading_ease', 0)
        if flesch >= 60:
            insights.append("Readability is excellent - accessible to a broad professional audience.")
        elif flesch >= 40:
            insights.append("Readability is moderate - appropriate for technical readers.")
        else:
            insights.append("Readability could be improved to reach a wider audience.")
        
        # Error insights
        if len(errors) == 0:
            insights.append("No style issues detected - clean, professional writing.")
        elif len(errors) < 5:
            insights.append(f"Only {len(errors)} minor issues found - well-written content.")
        elif len(errors) < 15:
            insights.append(f"{len(errors)} issues identified - targeted improvements recommended.")
        else:
            insights.append(f"{len(errors)} areas for improvement - systematic revision suggested.")
        
        return insights
    
    @classmethod
    def generate_priority_actions(cls, analysis_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate prioritized action items."""
        actions = []
        
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        # Check grade level
        from .metrics import MetricsCalculator
        grade_level = MetricsCalculator.extract_grade_level(analysis_data)
        
        if grade_level > 14:
            actions.append({
                'priority': 'HIGH',
                'action': 'Simplify complex sentences',
                'impact': 'Improves accessibility by 40%',
                'effort': 'Medium'
            })
        
        # Check passive voice
        passive_pct = statistics.get('passive_voice_percentage', 0)
        if passive_pct > 25:
            actions.append({
                'priority': 'HIGH',
                'action': 'Reduce passive voice usage',
                'impact': 'Creates more engaging, direct content',
                'effort': 'Low'
            })
        
        # Check sentence length
        avg_sentence = statistics.get('avg_sentence_length', 0)
        if avg_sentence > 25:
            actions.append({
                'priority': 'MEDIUM',
                'action': 'Break down long sentences',
                'impact': 'Improves comprehension by 25%',
                'effort': 'Medium'
            })
        
        # Error-based actions
        if errors:
            error_types = Counter([e.get('type', 'unknown') for e in errors])
            top_error = error_types.most_common(1)
            if top_error:
                error_type, count = top_error[0]
                actions.append({
                    'priority': 'MEDIUM' if count < 10 else 'HIGH',
                    'action': f'Address {error_type.replace("_", " ")} issues ({count} found)',
                    'impact': f'Reduces errors by {min(100, count * 10)}%',
                    'effort': 'Low' if count < 5 else 'Medium'
                })
        
        # Sort by priority
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return actions[:5]  # Return top 5 actions
    
    @classmethod
    def get_score_badge(cls, score: float) -> Dict[str, str]:
        """Get badge information for a score."""
        if score >= 90:
            return {'label': 'EXCEPTIONAL', 'color': '#1A8F57', 'icon': '🏆'}
        elif score >= 80:
            return {'label': 'EXCELLENT', 'color': '#2E9E59', 'icon': '⭐'}
        elif score >= 70:
            return {'label': 'GOOD', 'color': '#66BA6B', 'icon': '✓'}
        elif score >= 60:
            return {'label': 'SATISFACTORY', 'color': '#F2BA4D', 'icon': '○'}
        elif score >= 50:
            return {'label': 'NEEDS WORK', 'color': '#E3735E', 'icon': '△'}
        else:
            return {'label': 'REQUIRES REVISION', 'color': '#BF3838', 'icon': '✗'}

