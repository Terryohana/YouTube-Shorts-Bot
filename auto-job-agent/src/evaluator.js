require('dotenv').config();

/**
 * Evaluate a job description against Terry's profile matrix.
 * In a real scenario, this would call OpenAI/Gemini APIs.
 * We use a mock heuristic based on keyword density if API key is missing.
 */
async function evaluateJob(job) {
    const desc = (job.description || '').toLowerCase();
    const requiredSkills = ['salesforce', 'apex', 'lwc', 'flow', 'javascript', 'node.js', 'python', 'puppeteer', 'aws'];
    
    // Simple heuristic for mock mode
    let matchScore = 0;
    let matchedKeywords = [];
    
    requiredSkills.forEach(skill => {
        if (desc.includes(skill)) {
            matchScore += 15; // Assign some arbitrary weight
            matchedKeywords.push(skill);
        }
    });

    // Cap at 100
    matchScore = Math.min(matchScore, 100);

    // Apply strict filters from System Instruction Step 2:
    // "Reject junior positions"
    if (desc.includes('junior') || desc.includes('entry level')) {
        matchScore = 0;
    }

    // Must require Salesforce OR (Javascript/Python Data pipeline) OR (General IT/Fullstack)
    const hasSalesforce = desc.includes('salesforce') || desc.includes('apex') || desc.includes('lwc');
    const hasPipeline = (desc.includes('javascript') || desc.includes('python')) && desc.includes('pipeline');
    const hasFullStack = desc.includes('node.js') || desc.includes('react') || desc.includes('javascript') || desc.includes('python');
    
    if (!hasSalesforce && !hasPipeline && !hasFullStack) {
        matchScore = 0;
    }

    return {
        score: matchScore,
        reasons: `Matched keywords: ${matchedKeywords.join(', ')}`,
        isMatch: matchScore >= 75
    };
}

module.exports = { evaluateJob };
