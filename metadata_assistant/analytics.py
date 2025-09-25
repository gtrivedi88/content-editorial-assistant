"""
Content Performance Analytics Service
Provides strategic content intelligence and SEO opportunity analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import sessionmaker

# Database imports will be handled dynamically to avoid circular imports
logger = logging.getLogger(__name__)


class ContentPerformanceAnalytics:
    """
    Service for analyzing content performance and generating strategic insights.
    Transforms metadata history into actionable content intelligence.
    """
    
    def __init__(self, database_session=None):
        """Initialize with database session."""
        self.db_session = database_session
        self.logger = logger
        
    def set_database_session(self, session):
        """Set database session (for dependency injection)."""
        self.db_session = session
    
    def generate_seo_opportunity_analysis(self, time_period_days: int = 30) -> Dict[str, Any]:
        """
        Generate SEO opportunity analysis from metadata performance.
        Identifies high-traffic, low-competition topics and content gaps.
        """
        try:
            from database.models import MetadataGeneration, ContentPerformanceMetrics
            
            if not self.db_session:
                self.logger.error("No database session available for SEO analysis")
                return {'error': 'Database session not available'}
            
            # Query recent metadata generations with performance data
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            
            recent_content = self.db_session.query(MetadataGeneration, ContentPerformanceMetrics)\
                .join(ContentPerformanceMetrics, isouter=True)\
                .filter(MetadataGeneration.created_at >= cutoff_date)\
                .all()
            
            if not recent_content:
                return {
                    'high_opportunity_gaps': [],
                    'recommendations': ['No content performance data available for analysis'],
                    'analysis_period': f'{time_period_days} days',
                    'content_analyzed': 0
                }
            
            analysis = {
                'high_performing_patterns': self._identify_high_performing_patterns(recent_content),
                'underperforming_categories': self._identify_underperforming_categories(recent_content),
                'keyword_opportunities': self._identify_keyword_gaps(recent_content),
                'taxonomy_effectiveness': self._analyze_taxonomy_performance(recent_content),
                'title_optimization_opportunities': self._identify_title_improvements(recent_content),
                'analysis_period': f'{time_period_days} days',
                'content_analyzed': len(recent_content)
            }
            
            # Generate high-level recommendations
            analysis['recommendations'] = self._generate_seo_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"SEO opportunity analysis failed: {e}")
            return {'error': str(e)}
    
    def generate_content_gap_analysis(self) -> Dict[str, Any]:
        """
        Identify content gaps based on taxonomy and performance data.
        Finds underrepresented topics with high performance potential.
        """
        try:
            from database.models import MetadataGeneration, ContentPerformanceMetrics
            
            if not self.db_session:
                return {'error': 'Database session not available'}
            
            # Analyze taxonomy distribution with performance data
            taxonomy_stats = self.db_session.query(
                MetadataGeneration.taxonomy_tags,
                func.count(MetadataGeneration.id).label('content_count'),
                func.avg(ContentPerformanceMetrics.page_views).label('avg_views'),
                func.avg(ContentPerformanceMetrics.organic_search_traffic).label('avg_organic_traffic')
            ).outerjoin(ContentPerformanceMetrics)\
             .group_by(MetadataGeneration.taxonomy_tags)\
             .having(func.count(MetadataGeneration.id) >= 1)\
             .all()
            
            # Process taxonomy data
            taxonomy_performance = self._process_taxonomy_stats(taxonomy_stats)
            
            gaps = {
                'underrepresented_topics': self._find_content_gaps(taxonomy_performance),
                'high_demand_low_supply': self._find_high_demand_gaps(taxonomy_performance),
                'content_distribution': self._analyze_content_distribution(taxonomy_performance),
                'recommended_content_creation': self._generate_content_recommendations(taxonomy_performance),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return gaps
            
        except Exception as e:
            self.logger.error(f"Content gap analysis failed: {e}")
            return {'error': str(e)}
    
    def get_metadata_learning_insights(self) -> Dict[str, Any]:
        """
        Analyze learning data to improve metadata generation algorithms.
        Identifies patterns in user corrections and algorithm performance.
        """
        try:
            from database.models import MetadataFeedback, TaxonomyLearning
            
            if not self.db_session:
                return {'error': 'Database session not available'}
            
            # Get recent feedback data
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            recent_feedback = self.db_session.query(MetadataFeedback)\
                .filter(MetadataFeedback.created_at >= cutoff_date)\
                .all()
            
            # Get taxonomy learning data
            recent_learning = self.db_session.query(TaxonomyLearning)\
                .filter(TaxonomyLearning.created_at >= cutoff_date)\
                .all()
            
            insights = {
                'most_corrected_components': self._analyze_correction_patterns(recent_feedback),
                'algorithm_accuracy_trends': self._analyze_algorithm_performance(recent_learning),
                'user_satisfaction_trends': self._analyze_satisfaction_trends(recent_feedback),
                'improvement_recommendations': self._generate_algorithm_recommendations(recent_feedback, recent_learning),
                'feedback_volume': len(recent_feedback),
                'learning_data_points': len(recent_learning),
                'analysis_period': '30 days'
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Learning insights analysis failed: {e}")
            return {'error': str(e)}
    
    def get_content_roi_analysis(self) -> Dict[str, Any]:
        """
        Analyze content ROI based on performance metrics and creation effort.
        Identifies high-ROI content patterns and optimization opportunities.
        """
        try:
            from database.models import MetadataGeneration, ContentPerformanceMetrics
            
            if not self.db_session:
                return {'error': 'Database session not available'}
            
            # Get content with performance data
            content_with_metrics = self.db_session.query(MetadataGeneration, ContentPerformanceMetrics)\
                .join(ContentPerformanceMetrics)\
                .filter(ContentPerformanceMetrics.page_views > 0)\
                .all()
            
            if not content_with_metrics:
                return {
                    'high_roi_patterns': {},
                    'optimization_opportunities': [],
                    'roi_insights': 'Insufficient performance data for ROI analysis'
                }
            
            # Analyze ROI patterns
            roi_analysis = {
                'high_roi_patterns': self._identify_high_roi_patterns(content_with_metrics),
                'low_roi_content': self._identify_low_roi_content(content_with_metrics),
                'optimization_opportunities': self._identify_roi_optimization_opportunities(content_with_metrics),
                'roi_by_taxonomy': self._analyze_roi_by_taxonomy(content_with_metrics),
                'content_analyzed': len(content_with_metrics)
            }
            
            return roi_analysis
            
        except Exception as e:
            self.logger.error(f"Content ROI analysis failed: {e}")
            return {'error': str(e)}
    
    # Private helper methods
    
    def _identify_high_performing_patterns(self, content_data: List[Tuple]) -> Dict[str, Any]:
        """Identify patterns in high-performing content."""
        if not content_data:
            return {}
        
        # Filter to top 20% performers
        performance_scores = []
        for metadata, metrics in content_data:
            if metrics:
                # Calculate composite performance score
                score = (metrics.page_views or 0) + (metrics.organic_search_traffic or 0) * 2
                performance_scores.append((metadata, metrics, score))
        
        if not performance_scores:
            return {'message': 'No performance data available'}
        
        # Get top 20%
        performance_scores.sort(key=lambda x: x[2], reverse=True)
        top_20_percent = performance_scores[:max(1, len(performance_scores) // 5)]
        
        patterns = {
            'optimal_title_length': self._analyze_title_length_performance(top_20_percent),
            'high_performing_keywords': self._analyze_keyword_performance(top_20_percent),
            'effective_descriptions': self._analyze_description_patterns(top_20_percent),
            'successful_taxonomy_combinations': self._analyze_taxonomy_combinations(top_20_percent)
        }
        
        return patterns
    
    def _identify_underperforming_categories(self, content_data: List[Tuple]) -> Dict[str, Any]:
        """Identify taxonomy categories with poor performance."""
        category_performance = defaultdict(list)
        
        for metadata, metrics in content_data:
            if metadata.taxonomy_tags and metrics:
                performance_score = (metrics.page_views or 0) + (metrics.organic_search_traffic or 0)
                for tag in metadata.taxonomy_tags:
                    category_performance[tag].append(performance_score)
        
        # Calculate average performance per category
        underperforming = {}
        for category, scores in category_performance.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            if avg_score < 100:  # Threshold for underperformance
                underperforming[category] = {
                    'average_performance': avg_score,
                    'content_count': len(scores),
                    'improvement_potential': 'high' if len(scores) > 5 else 'medium'
                }
        
        return underperforming
    
    def _identify_keyword_gaps(self, content_data: List[Tuple]) -> Dict[str, Any]:
        """Identify keyword opportunities based on performance data."""
        keyword_performance = defaultdict(list)
        
        for metadata, metrics in content_data:
            if metadata.keywords and metrics:
                performance_score = metrics.organic_search_traffic or 0
                for keyword in metadata.keywords:
                    keyword_performance[keyword].append(performance_score)
        
        # Find high-performing keywords that are underutilized
        opportunities = {}
        for keyword, scores in keyword_performance.items():
            if len(scores) < 3 and sum(scores) > 50:  # High performance, low usage
                opportunities[keyword] = {
                    'average_traffic': sum(scores) / len(scores),
                    'usage_count': len(scores),
                    'opportunity_score': sum(scores) / len(scores) * (10 - len(scores))
                }
        
        return dict(sorted(opportunities.items(), key=lambda x: x[1]['opportunity_score'], reverse=True)[:10])
    
    def _analyze_taxonomy_performance(self, content_data: List[Tuple]) -> Dict[str, Any]:
        """Analyze performance by taxonomy categories."""
        taxonomy_stats = defaultdict(lambda: {'views': [], 'traffic': [], 'count': 0})
        
        for metadata, metrics in content_data:
            if metadata.taxonomy_tags and metrics:
                for tag in metadata.taxonomy_tags:
                    taxonomy_stats[tag]['views'].append(metrics.page_views or 0)
                    taxonomy_stats[tag]['traffic'].append(metrics.organic_search_traffic or 0)
                    taxonomy_stats[tag]['count'] += 1
        
        # Calculate averages
        performance = {}
        for tag, stats in taxonomy_stats.items():
            if stats['count'] > 0:
                performance[tag] = {
                    'average_views': sum(stats['views']) / len(stats['views']),
                    'average_traffic': sum(stats['traffic']) / len(stats['traffic']),
                    'content_count': stats['count'],
                    'effectiveness_score': (sum(stats['views']) + sum(stats['traffic']) * 2) / stats['count']
                }
        
        return dict(sorted(performance.items(), key=lambda x: x[1]['effectiveness_score'], reverse=True))
    
    def _identify_title_improvements(self, content_data: List[Tuple]) -> List[Dict[str, Any]]:
        """Identify opportunities for title optimization."""
        opportunities = []
        
        for metadata, metrics in content_data:
            if not metrics or not metadata.title:
                continue
                
            performance_score = (metrics.page_views or 0) + (metrics.organic_search_traffic or 0)
            title_length = len(metadata.title)
            
            # Identify potential issues
            issues = []
            if title_length > 70:
                issues.append('Title too long for SEO')
            elif title_length < 30:
                issues.append('Title might be too short')
            
            if performance_score < 50:
                issues.append('Low performance - consider title optimization')
            
            if issues:
                opportunities.append({
                    'metadata_id': metadata.metadata_id,
                    'current_title': metadata.title,
                    'performance_score': performance_score,
                    'issues': issues,
                    'optimization_priority': 'high' if performance_score < 25 else 'medium'
                })
        
        return sorted(opportunities, key=lambda x: x['performance_score'])[:10]
    
    def _process_taxonomy_stats(self, taxonomy_stats: List[Tuple]) -> Dict[str, Dict]:
        """Process raw taxonomy statistics."""
        processed = {}
        
        for row in taxonomy_stats:
            taxonomy_tags, content_count, avg_views, avg_traffic = row
            
            if taxonomy_tags:  # taxonomy_tags is a JSON field
                for tag in taxonomy_tags:
                    if tag not in processed:
                        processed[tag] = {
                            'content_count': 0,
                            'total_views': 0,
                            'total_traffic': 0
                        }
                    
                    processed[tag]['content_count'] += content_count or 0
                    processed[tag]['total_views'] += (avg_views or 0) * (content_count or 0)
                    processed[tag]['total_traffic'] += (avg_traffic or 0) * (content_count or 0)
        
        # Calculate averages
        for tag_data in processed.values():
            if tag_data['content_count'] > 0:
                tag_data['avg_views'] = tag_data['total_views'] / tag_data['content_count']
                tag_data['avg_traffic'] = tag_data['total_traffic'] / tag_data['content_count']
        
        return processed
    
    def _find_content_gaps(self, taxonomy_performance: Dict) -> List[Dict[str, Any]]:
        """Find underrepresented topics with high potential."""
        gaps = []
        
        # Standard taxonomy categories that should have content
        expected_categories = [
            'Troubleshooting', 'Installation', 'API_Documentation', 
            'Security', 'Best_Practices', 'Configuration', 'Tutorial'
        ]
        
        for category in expected_categories:
            if category not in taxonomy_performance:
                gaps.append({
                    'category': category,
                    'current_content': 0,
                    'opportunity_type': 'missing_category',
                    'priority': 'high',
                    'recommendation': f'Create foundational {category} content'
                })
            elif taxonomy_performance[category]['content_count'] < 3:
                gaps.append({
                    'category': category,
                    'current_content': taxonomy_performance[category]['content_count'],
                    'opportunity_type': 'underrepresented',
                    'priority': 'medium',
                    'recommendation': f'Expand {category} content library'
                })
        
        return gaps
    
    def _generate_seo_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable SEO recommendations based on analysis."""
        recommendations = []
        
        # High-performing patterns recommendations
        if analysis.get('high_performing_patterns'):
            patterns = analysis['high_performing_patterns']
            if 'optimal_title_length' in patterns:
                recommendations.append(f"Optimize titles to {patterns['optimal_title_length']} characters for best performance")
        
        # Keyword opportunities
        if analysis.get('keyword_opportunities'):
            top_keywords = list(analysis['keyword_opportunities'].keys())[:3]
            if top_keywords:
                recommendations.append(f"Focus on high-opportunity keywords: {', '.join(top_keywords)}")
        
        # Underperforming categories
        if analysis.get('underperforming_categories'):
            underperforming = list(analysis['underperforming_categories'].keys())[:2]
            if underperforming:
                recommendations.append(f"Improve content quality in: {', '.join(underperforming)}")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("Continue collecting performance data for more specific recommendations")
        
        return recommendations
    
    def _analyze_correction_patterns(self, feedback_data: List) -> Dict[str, Any]:
        """Analyze patterns in user corrections."""
        component_corrections = Counter()
        correction_reasons = Counter()
        
        for feedback in feedback_data:
            component_corrections[feedback.component] += 1
            if feedback.correction_reason:
                correction_reasons[feedback.correction_reason] += 1
        
        return {
            'most_corrected_components': dict(component_corrections.most_common(5)),
            'common_correction_reasons': dict(correction_reasons.most_common(5)),
            'total_corrections': len(feedback_data)
        }
    
    def _analyze_algorithm_performance(self, learning_data: List) -> Dict[str, Any]:
        """Analyze algorithm performance trends."""
        algorithm_accuracy = defaultdict(list)
        
        for learning in learning_data:
            if learning.algorithm_used and learning.accuracy_score is not None:
                algorithm_accuracy[learning.algorithm_used].append(learning.accuracy_score)
        
        performance = {}
        for algorithm, scores in algorithm_accuracy.items():
            if scores:
                performance[algorithm] = {
                    'average_accuracy': sum(scores) / len(scores),
                    'samples': len(scores),
                    'trend': 'improving' if scores[-5:] and sum(scores[-5:]) / len(scores[-5:]) > sum(scores) / len(scores) else 'stable'
                }
        
        return performance
    
    def _analyze_satisfaction_trends(self, feedback_data: List) -> Dict[str, Any]:
        """Analyze user satisfaction trends."""
        # This would integrate with user ratings from the existing system
        satisfaction_data = {
            'total_feedback_entries': len(feedback_data),
            'trend': 'stable',  # Placeholder - would be calculated from actual ratings
            'improvement_areas': []
        }
        
        return satisfaction_data
    
    def _generate_algorithm_recommendations(self, feedback_data: List, learning_data: List) -> List[str]:
        """Generate recommendations for algorithm improvements."""
        recommendations = []
        
        # Analyze correction patterns
        component_corrections = Counter(f.component for f in feedback_data)
        
        if component_corrections.get('keywords', 0) > 5:
            recommendations.append("Improve keyword extraction algorithm - high correction rate")
        
        if component_corrections.get('taxonomy', 0) > 3:
            recommendations.append("Enhance taxonomy classification with more training data")
        
        # Analyze algorithm performance
        if learning_data:
            avg_accuracy = sum(l.accuracy_score or 0 for l in learning_data) / len(learning_data)
            if avg_accuracy < 0.7:
                recommendations.append("Overall classification accuracy below 70% - consider model retraining")
        
        if not recommendations:
            recommendations.append("Continue monitoring algorithm performance")
        
        return recommendations
    
    # Additional helper methods for ROI analysis
    
    def _identify_high_roi_patterns(self, content_data: List[Tuple]) -> Dict[str, Any]:
        """Identify content patterns with high ROI."""
        # Calculate ROI based on performance vs. estimated creation effort
        roi_data = []
        
        for metadata, metrics in content_data:
            # Estimate creation effort based on content length and complexity
            effort_score = 1.0  # Base effort
            if metadata.content_length:
                if metadata.content_length > 5000:
                    effort_score += 2.0
                elif metadata.content_length > 2000:
                    effort_score += 1.0
            
            # Calculate performance value
            performance_value = (metrics.page_views or 0) + (metrics.organic_search_traffic or 0) * 3
            
            # ROI = Value / Effort
            roi = performance_value / effort_score if effort_score > 0 else 0
            
            if roi > 0:
                roi_data.append({
                    'metadata': metadata,
                    'metrics': metrics,
                    'roi': roi,
                    'performance_value': performance_value,
                    'effort_score': effort_score
                })
        
        # Sort by ROI and get patterns from top performers
        roi_data.sort(key=lambda x: x['roi'], reverse=True)
        top_roi = roi_data[:len(roi_data)//4] if roi_data else []  # Top 25%
        
        if not top_roi:
            return {}
        
        # Analyze patterns in high-ROI content
        patterns = {
            'average_roi': sum(item['roi'] for item in top_roi) / len(top_roi),
            'common_taxonomy': self._find_common_patterns([item['metadata'].taxonomy_tags for item in top_roi]),
            'optimal_length_range': self._analyze_content_length_patterns(top_roi),
            'high_roi_count': len(top_roi)
        }
        
        return patterns
    
    def _find_common_patterns(self, taxonomy_lists: List[List[str]]) -> List[str]:
        """Find common taxonomy patterns in high-ROI content."""
        if not taxonomy_lists:
            return []
        
        # Flatten and count all tags
        all_tags = []
        for tag_list in taxonomy_lists:
            if tag_list:
                all_tags.extend(tag_list)
        
        tag_counts = Counter(all_tags)
        # Return tags that appear in at least 25% of high-ROI content
        threshold = max(1, len(taxonomy_lists) // 4)
        
        return [tag for tag, count in tag_counts.items() if count >= threshold]
    
    def _analyze_content_length_patterns(self, roi_data: List[Dict]) -> Dict[str, int]:
        """Analyze optimal content length for high ROI."""
        lengths = [item['metadata'].content_length for item in roi_data if item['metadata'].content_length]
        
        if not lengths:
            return {}
        
        lengths.sort()
        return {
            'min': min(lengths),
            'max': max(lengths),
            'median': lengths[len(lengths)//2],
            'recommended_range': f"{lengths[len(lengths)//4]}-{lengths[3*len(lengths)//4]} characters"
        }
