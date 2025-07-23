/**
 * Engagement & Tone Analyzer Module
 * Analyzes text for user engagement, voice consistency, and writing strength
 */

// Calculate comprehensive engagement and tone metrics
function calculateEngagementMetrics(text, statistics) {
    if (!text || !text.trim()) {
        return {
            engagement_score: 0,
            direct_address_percentage: 0,
            adverb_density: 0,
            engagement_category: 'Unknown',
            voice_analysis: {
                second_person: 0,
                first_person: 0,
                total_pronouns: 0
            },
            recommendations: []
        };
    }

    const wordCount = statistics.word_count || text.split(/\s+/).length;
    const recommendations = [];

    // Voice Analysis - Direct Address Assessment
    const voiceMetrics = analyzeVoicePattern(text, wordCount);
    
    // Adverb Density Analysis
    const adverbMetrics = analyzeAdverbDensity(text, wordCount);
    
    // Calculate overall engagement score
    const engagementScore = calculateOverallEngagementScore(voiceMetrics, adverbMetrics, recommendations);
    
    // Determine engagement category
    const category = getEngagementCategory(engagementScore);
    
    return {
        engagement_score: Math.round(engagementScore),
        direct_address_percentage: voiceMetrics.direct_address_percentage,
        adverb_density: adverbMetrics.density,
        engagement_category: category,
        voice_analysis: voiceMetrics,
        adverb_analysis: adverbMetrics,
        recommendations: recommendations
    };
}

// Analyze voice patterns and direct address usage
function analyzeVoicePattern(text, wordCount) {
    // Second person pronouns (direct address)
    const secondPersonPatterns = /\b(you|your|yours|yourself|yourselves)\b/gi;
    const secondPersonMatches = text.match(secondPersonPatterns) || [];
    const secondPersonCount = secondPersonMatches.length;
    
    // First person pronouns (authorial voice)
    const firstPersonPatterns = /\b(I|we|our|us|my|mine|myself|ourselves|me)\b/gi;
    const firstPersonMatches = text.match(firstPersonPatterns) || [];
    const firstPersonCount = firstPersonMatches.length;
    
    // Third person pronouns
    const thirdPersonPatterns = /\b(he|she|it|they|him|her|them|his|hers|its|their|theirs)\b/gi;
    const thirdPersonMatches = text.match(thirdPersonPatterns) || [];
    const thirdPersonCount = thirdPersonMatches.length;
    
    const totalPronouns = secondPersonCount + firstPersonCount + thirdPersonCount;
    const directAddressPercentage = totalPronouns > 0 ? (secondPersonCount / totalPronouns) * 100 : 0;
    
    return {
        second_person: secondPersonCount,
        first_person: firstPersonCount,
        third_person: thirdPersonCount,
        total_pronouns: totalPronouns,
        direct_address_percentage: directAddressPercentage,
        words_per_pronoun: totalPronouns > 0 ? wordCount / totalPronouns : 0
    };
}

// Analyze adverb density and writing strength
function analyzeAdverbDensity(text, wordCount) {
    // Common adverbs and qualifiers that weaken writing
    const adverbPatterns = [
        // -ly adverbs
        /\b\w+ly\b/gi,
        // Qualifying words
        /\b(very|really|quite|rather|somewhat|pretty|fairly|extremely|incredibly|absolutely|completely|totally|entirely|perfectly|exactly|precisely|literally|actually|basically|essentially|generally|typically|usually|normally|obviously|clearly|definitely|certainly|probably|possibly|maybe|perhaps|likely|unlikely)\b/gi
    ];
    
    let totalAdverbs = 0;
    const adverbTypes = {
        ly_adverbs: 0,
        qualifiers: 0
    };
    
    // Count -ly adverbs
    const lyAdverbs = text.match(adverbPatterns[0]) || [];
    adverbTypes.ly_adverbs = lyAdverbs.length;
    
    // Count qualifiers
    const qualifiers = text.match(adverbPatterns[1]) || [];
    adverbTypes.qualifiers = qualifiers.length;
    
    totalAdverbs = adverbTypes.ly_adverbs + adverbTypes.qualifiers;
    const density = wordCount > 0 ? (totalAdverbs / wordCount) * 100 : 0;
    
    return {
        total_adverbs: totalAdverbs,
        density: density,
        ly_adverbs: adverbTypes.ly_adverbs,
        qualifiers: adverbTypes.qualifiers,
        strength_score: Math.max(0, 100 - (density * 10)) // Higher density = lower strength
    };
}

// Calculate overall engagement score
function calculateOverallEngagementScore(voiceMetrics, adverbMetrics, recommendations) {
    let score = 85; // Base score
    
    // Voice Analysis Impact (40% of score)
    const directAddressRatio = voiceMetrics.direct_address_percentage / 100;
    
    if (directAddressRatio >= 0.6) {
        // Excellent direct address usage for technical writing
        score += 15;
    } else if (directAddressRatio >= 0.4) {
        // Good direct address usage
        score += 5;
    } else if (directAddressRatio >= 0.2) {
        // Fair direct address usage
        score -= 5;
        recommendations.push('Consider using more direct address ("you") to engage readers');
    } else {
        // Poor direct address usage
        score -= 15;
        recommendations.push('Add more direct address ("you", "your") to connect with readers');
    }
    
    // Excessive first person penalty
    if (voiceMetrics.first_person > voiceMetrics.second_person * 0.5) {
        score -= 10;
        recommendations.push('Reduce first-person references to maintain professional tone');
    }
    
    // Adverb Density Impact (60% of score)
    if (adverbMetrics.density <= 3) {
        // Excellent - strong, direct writing
        score += 10;
    } else if (adverbMetrics.density <= 5) {
        // Good adverb usage
        score += 0;
    } else if (adverbMetrics.density <= 8) {
        // Fair - room for improvement
        score -= 10;
        recommendations.push('Consider reducing adverbs for stronger, more direct writing');
    } else {
        // Poor - too many adverbs
        score -= 20;
        recommendations.push('Remove unnecessary adverbs and qualifiers to strengthen your writing');
    }
    
    // Qualifier-heavy writing penalty
    if (adverbMetrics.qualifiers > adverbMetrics.ly_adverbs * 1.5) {
        score -= 5;
        recommendations.push('Reduce hedge words like "really", "very", "quite" for more confident tone');
    }
    
    return Math.max(0, Math.min(100, score));
}

// Get engagement category based on score
function getEngagementCategory(score) {
    if (score >= 85) return 'Highly Engaging';
    if (score >= 70) return 'Engaging';
    if (score >= 55) return 'Moderately Engaging';
    if (score >= 40) return 'Needs Improvement';
    return 'Poor Engagement';
}

// Get status for color coding
function getEngagementStatus(score) {
    if (score >= 70) return 'success';
    if (score >= 55) return 'warning';
    return 'danger';
}

// Generate insights for the engagement metrics
function generateEngagementInsights(metrics) {
    const insights = [];
    
    // Direct address insights
    if (metrics.direct_address_percentage >= 60) {
        insights.push('Excellent use of direct address - speaks directly to users');
    } else if (metrics.direct_address_percentage >= 40) {
        insights.push('Good user engagement through direct address');
    } else {
        insights.push('Consider using more "you" and "your" to engage readers');
    }
    
    // Adverb density insights
    if (metrics.adverb_density <= 3) {
        insights.push('Strong, direct writing with minimal unnecessary qualifiers');
    } else if (metrics.adverb_density <= 5) {
        insights.push('Good writing strength with appropriate modifier usage');
    } else {
        insights.push('Consider reducing adverbs for more impactful writing');
    }
    
    return insights;
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.EngagementAnalyzer = {
        calculateEngagementMetrics,
        getEngagementStatus,
        generateEngagementInsights
    };
} 