/**
 * Quality Risk Insight Helper - Frontend JavaScript
 */

// Character counter
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('observationText');
    const charCount = document.getElementById('charCount');
    
    textarea.addEventListener('input', function() {
        charCount.textContent = this.value.length;
    });
    
    // Form submission
    document.getElementById('insightForm').addEventListener('submit', function(e) {
        e.preventDefault();
        getQualityInsight();
    });
});

function fillExample(text) {
    const textarea = document.getElementById('observationText');
    const examples = {
        'Humidity drift': 'Humidity slightly high in Zone C. Minor particle alert earlier. No visible defects observed.',
        'Particle alert': 'Particle count increased briefly in cleanroom. Returned to normal levels after 10 minutes.',
        'Tool vibration': 'Equipment showed unusual vibration during operation. No immediate impact on output quality.',
        'Packaging scratch': 'Noticed minor scratch on packaging material. Contents appear unaffected.'
    };
    
    textarea.value = examples[text] || text;
    textarea.dispatchEvent(new Event('input'));
    textarea.focus();
}

async function getQualityInsight() {
    const observationText = document.getElementById('observationText').value.trim();
    const context = document.getElementById('context').value;
    const submitBtn = document.getElementById('submitBtn');
    const loadingState = document.getElementById('loadingState');
    const resultsPanel = document.getElementById('resultsPanel');
    const errorMessage = document.getElementById('errorMessage');
    
    // Validation
    if (observationText.length < 20) {
        showError('Observation must be at least 20 characters long.');
        return;
    }
    
    if (observationText.length > 1000) {
        showError('Observation must be at most 1000 characters long.');
        return;
    }
    
    // Hide previous results/errors
    resultsPanel.classList.add('d-none');
    errorMessage.classList.add('d-none');
    
    // Show loading state
    loadingState.classList.remove('d-none');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    
    try {
        const response = await fetch('/api/quality-insight', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                observationText: observationText,
                context: context
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({error: 'Unknown error'}));
            throw new Error(errorData.error || 'Failed to get insight');
        }
        
        const data = await response.json();
        
        // Hide loading, show results
        loadingState.classList.add('d-none');
        displayResults(data);
        resultsPanel.classList.remove('d-none');
        
    } catch (error) {
        loadingState.classList.add('d-none');
        showError(error.message || 'An error occurred while processing your request.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-search me-2"></i>Get Quality Insight';
    }
}

function displayResults(data) {
    // Risk Level Badge
    const riskBadge = document.getElementById('riskBadge');
    riskBadge.textContent = data.riskLevel || 'MEDIUM';
    riskBadge.className = `risk-badge risk-${(data.riskLevel || 'MEDIUM').toUpperCase()}`;
    
    // Risk Interpretation
    document.getElementById('riskInterpretation').textContent = data.riskInterpretation || 'No interpretation available.';
    
    // Key Points
    const keyPointsList = document.getElementById('keyPoints');
    keyPointsList.innerHTML = '';
    if (data.keyPoints && Array.isArray(data.keyPoints)) {
        data.keyPoints.forEach(point => {
            const li = document.createElement('li');
            li.textContent = point;
            keyPointsList.appendChild(li);
        });
    }
    
    // Actions
    const actionsList = document.getElementById('actions');
    actionsList.innerHTML = '';
    if (data.actions && Array.isArray(data.actions)) {
        data.actions.forEach(action => {
            const li = document.createElement('li');
            li.textContent = action;
            actionsList.appendChild(li);
        });
    }
    
    // Clarifying Questions
    const clarifyingCard = document.getElementById('clarifyingQuestionsCard');
    const clarifyingList = document.getElementById('clarifyingQuestions');
    clarifyingList.innerHTML = '';
    
    if (data.clarifyingQuestions && Array.isArray(data.clarifyingQuestions) && data.clarifyingQuestions.length > 0) {
        data.clarifyingQuestions.forEach(question => {
            const li = document.createElement('li');
            li.textContent = question;
            clarifyingList.appendChild(li);
        });
        clarifyingCard.classList.remove('d-none');
    } else {
        clarifyingCard.classList.add('d-none');
    }
    
    // Disclaimer
    document.getElementById('disclaimer').textContent = data.disclaimer || 'This insight is general guidance and not a technical or engineering assessment.';
    
    // Scroll to results
    resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    errorText.textContent = message;
    errorMessage.classList.remove('d-none');
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

