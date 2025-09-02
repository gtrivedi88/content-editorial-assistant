/**
 * Modular Documentation Compliance Scoring Algorithm
 * 
 * This algorithm uses advanced weightings and multi-factor analysis to provide
 * meaningful, actionable compliance scores for modular documentation.
 */

class ModularComplianceScorer {
    constructor() {
        // World-class scoring weights based on Red Hat documentation standards impact
        this.WEIGHTS = {
            // Issue severity weights (exponential to emphasize critical failures)
            SEVERITY: {
                'high': 25,    // FAIL issues - critical structural violations
                'medium': 8,   // WARN issues - style/quality recommendations  
                'low': 2       // INFO issues - minor improvements
            },
            
            // Content type complexity factors (different standards have different complexity)
            COMPLEXITY: {
                'procedure': 1.2,   // Most complex - strict structural requirements
                'reference': 1.1,   // Medium - organized data requirements
                'concept': 1.0      // Base - explanatory content requirements
            },
            
            // Volume scaling factor (larger docs should be more forgiving per-issue)
            VOLUME_SCALING: {
                MIN_WORDS: 50,    // Below this, penalties are amplified
                OPTIMAL_WORDS: 400, // Sweet spot for most modules
                MAX_SCALING: 0.7   // Maximum forgiveness for very long docs
            }
        };
        
        // Scoring bands for categorization
        this.SCORE_BANDS = {
            EXCELLENT: { min: 90, label: 'Excellent', color: 'green', icon: 'trophy' },
            GOOD: { min: 75, label: 'Good', color: 'green', icon: 'check-circle' },
            FAIR: { min: 60, label: 'Fair', color: 'gold', icon: 'exclamation-triangle' },
            NEEDS_WORK: { min: 40, label: 'Needs Work', color: 'orange', icon: 'tools' },
            POOR: { min: 0, label: 'Poor', color: 'red', icon: 'times-circle' }
        };
    }

    /**
     * Calculate comprehensive modular compliance score
     * @param {Object} complianceData - Modular compliance results from backend
     * @param {Object} documentStats - Document statistics (word count, etc.)
     * @returns {Object} Detailed scoring result
     */
    calculateComplianceScore(complianceData, documentStats = {}) {
        if (!complianceData || !complianceData.issues) {
            return this._getDefaultScore(complianceData?.content_type || 'concept');
        }

        const contentType = complianceData.content_type || 'concept';
        const wordCount = documentStats.word_count || 0;
        
        // Core scoring calculation
        const baseScore = this._calculateBaseScore(complianceData.issues, wordCount, contentType);
        
        // Advanced adjustments
        const adjustedScore = this._applyAdvancedAdjustments(baseScore, complianceData, documentStats);
        
        // Final score (0-100 scale)
        const finalScore = Math.max(0, Math.min(100, adjustedScore));
        
        // Generate detailed analysis
        return {
            score: finalScore,
            band: this._getScoreBand(finalScore),
            breakdown: this._generateScoreBreakdown(complianceData.issues, wordCount, contentType),
            insights: this._generateInsights(finalScore, complianceData, documentStats),
            recommendations: this._generateRecommendations(complianceData.issues, finalScore),
            metadata: {
                contentType,
                totalIssues: complianceData.total_issues || 0,
                wordCount,
                algorithm: 'ModularComplianceScorer v1.0'
            }
        };
    }

    /**
     * Calculate base score using weighted penalty system
     */
    _calculateBaseScore(issues, wordCount, contentType) {
        const complexityFactor = this.WEIGHTS.COMPLEXITY[contentType] || 1.0;
        const volumeScale = this._calculateVolumeScale(wordCount);
        
        let totalPenalty = 0;
        const issuesByType = this._categorizeIssues(issues);
        
        // Apply severity-based penalties
        Object.entries(issuesByType).forEach(([severity, count]) => {
            const severityWeight = this.WEIGHTS.SEVERITY[severity] || 5;
            const adjustedPenalty = severityWeight * count * complexityFactor * volumeScale;
            totalPenalty += adjustedPenalty;
        });
        
        // Start from perfect score and subtract penalties
        // Use logarithmic decay to prevent complete failure for documents with many minor issues
        const penaltyImpact = Math.log(totalPenalty + 1) * 15; // Logarithmic penalty scaling
        const baseScore = 100 - penaltyImpact;
        
        return baseScore;
    }

    /**
     * Apply advanced scoring adjustments for nuanced evaluation
     */
    _applyAdvancedAdjustments(baseScore, complianceData, documentStats) {
        let adjustedScore = baseScore;
        
        // Bonus for good structural elements (if detected)
        if (complianceData.structural_analysis) {
            const structuralBonus = this._calculateStructuralBonus(complianceData.structural_analysis);
            adjustedScore += structuralBonus;
        }
        
        // Penalty reduction for partial compliance (sophisticated partial credit)
        const partialCreditAdjustment = this._calculatePartialCredit(complianceData.issues);
        adjustedScore += partialCreditAdjustment;
        
        // Content maturity bonus (reward substantial, well-formed content)
        const maturityBonus = this._calculateMaturityBonus(documentStats);
        adjustedScore += maturityBonus;
        
        return adjustedScore;
    }

    /**
     * Calculate volume-based scaling factor
     */
    _calculateVolumeScale(wordCount) {
        if (wordCount < this.WEIGHTS.VOLUME_SCALING.MIN_WORDS) {
            return 1.3; // Amplify penalties for very short docs
        }
        
        if (wordCount > this.WEIGHTS.VOLUME_SCALING.OPTIMAL_WORDS) {
            // Gradually reduce penalty impact for longer docs
            const excessWords = wordCount - this.WEIGHTS.VOLUME_SCALING.OPTIMAL_WORDS;
            const scalingFactor = Math.max(
                this.WEIGHTS.VOLUME_SCALING.MAX_SCALING,
                1.0 - (excessWords / 2000) * 0.3
            );
            return scalingFactor;
        }
        
        return 1.0; // Optimal range
    }

    /**
     * Calculate bonus for good structural elements
     */
    _calculateStructuralBonus(structuralAnalysis) {
        let bonus = 0;
        
        // Reward presence of key structural elements
        if (structuralAnalysis.hasIntroduction) bonus += 2;
        if (structuralAnalysis.hasProperHeadings) bonus += 2;
        if (structuralAnalysis.hasStructuredContent) bonus += 3;
        if (structuralAnalysis.hasConclusion) bonus += 1;
        
        return Math.min(8, bonus); // Cap structural bonus
    }

    /**
     * Calculate partial credit for near-compliant content
     */
    _calculatePartialCredit(issues) {
        // Reward attempts at compliance even if not perfect
        let partialCredit = 0;
        
        // Count different types of issues to assess overall effort
        const failureCount = issues.filter(issue => issue.severity === 'high').length;
        const warningCount = issues.filter(issue => issue.severity === 'medium').length;
        const infoCount = issues.filter(issue => issue.severity === 'low').length;
        
        // If there are mostly warnings/info vs failures, give partial credit
        if (failureCount <= 2 && warningCount > 0) {
            partialCredit += Math.min(5, warningCount * 0.5); // Reward attempt at structure
        }
        
        return partialCredit;
    }

    /**
     * Calculate maturity bonus for substantial content
     */
    _calculateMaturityBonus(documentStats) {
        const wordCount = documentStats.word_count || 0;
        let bonus = 0;
        
        // Reward substantial, well-developed content
        if (wordCount > 200) bonus += 1;
        if (wordCount > 500) bonus += 2;
        if (wordCount > 1000) bonus += 2;
        
        // Reward good structure indicators
        const sentenceCount = documentStats.sentence_count || 0;
        const paragraphCount = documentStats.paragraph_count || 0;
        
        if (paragraphCount >= 3) bonus += 1;
        if (sentenceCount > paragraphCount * 2) bonus += 1; // Good sentence variety
        
        return Math.min(6, bonus); // Cap maturity bonus
    }

    /**
     * Categorize issues by severity for analysis
     */
    _categorizeIssues(issues) {
        return issues.reduce((acc, issue) => {
            const severity = issue.severity || 'medium';
            acc[severity] = (acc[severity] || 0) + 1;
            return acc;
        }, {});
    }

    /**
     * Determine score band and visual representation
     */
    _getScoreBand(score) {
        for (const [key, band] of Object.entries(this.SCORE_BANDS)) {
            if (score >= band.min) {
                return { ...band, key };
            }
        }
        return this.SCORE_BANDS.POOR;
    }

    /**
     * Generate detailed score breakdown
     */
    _generateScoreBreakdown(issues, wordCount, contentType) {
        const issuesByType = this._categorizeIssues(issues);
        const complexityFactor = this.WEIGHTS.COMPLEXITY[contentType];
        const volumeScale = this._calculateVolumeScale(wordCount);
        
        return {
            issueBreakdown: issuesByType,
            factors: {
                contentComplexity: complexityFactor,
                volumeScaling: volumeScale,
                totalIssues: issues.length
            }
        };
    }

    /**
     * Generate actionable insights
     */
    _generateInsights(score, complianceData, documentStats) {
        const insights = [];
        const issues = complianceData.issues || [];
        const contentType = complianceData.content_type;
        
        // Score-based insights
        if (score >= 90) {
            insights.push('Excellent compliance with modular documentation standards');
        } else if (score >= 75) {
            insights.push('Good structural compliance with minor improvements needed');
        } else if (score >= 60) {
            insights.push('Fair compliance - address key structural requirements');
        } else {
            insights.push('Significant structural improvements needed for compliance');
        }
        
        // Issue-specific insights
        const criticalIssues = issues.filter(issue => issue.severity === 'high').length;
        if (criticalIssues > 0) {
            insights.push(`${criticalIssues} critical ${contentType} requirement${criticalIssues === 1 ? '' : 's'} need immediate attention`);
        }
        
        return insights;
    }

    /**
     * Generate targeted recommendations
     */
    _generateRecommendations(issues, score) {
        const recommendations = [];
        
        // Priority-based recommendations
        const criticalIssues = issues.filter(issue => issue.severity === 'high');
        if (criticalIssues.length > 0) {
            recommendations.push('Priority: Fix critical structural violations first');
        }
        
        if (score < 75) {
            recommendations.push('Focus on required structural elements before style improvements');
        }
        
        const warningIssues = issues.filter(issue => issue.severity === 'medium');
        if (warningIssues.length > 0 && criticalIssues.length === 0) {
            recommendations.push('Polish content by addressing style and format recommendations');
        }
        
        return recommendations;
    }

    /**
     * Get default score for content without compliance data
     */
    _getDefaultScore(contentType) {
        return {
            score: 50,
            band: this.SCORE_BANDS.NEEDS_WORK,
            breakdown: { issueBreakdown: {}, factors: {} },
            insights: ['Modular compliance analysis not available'],
            recommendations: ['Run modular compliance analysis for detailed scoring'],
            metadata: {
                contentType,
                totalIssues: 0,
                wordCount: 0,
                algorithm: 'ModularComplianceScorer v1.0 (default)'
            }
        };
    }
}

// Global instance for use across the application
window.ModularComplianceScorer = new ModularComplianceScorer();

/**
 * Convenience function to calculate compliance score
 */
function calculateModularComplianceScore(complianceData, documentStats) {
    return window.ModularComplianceScorer.calculateComplianceScore(complianceData, documentStats);
}
