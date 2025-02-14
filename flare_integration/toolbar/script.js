// Constants
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const queryBtn = document.getElementById('queryBtn');
const draftBtn = document.getElementById('draftBtn');
const reviewBtn = document.getElementById('reviewBtn');
const inputText = document.getElementById('inputText');
const responseArea = document.getElementById('responseArea');
const insertBtn = document.getElementById('insertBtn');
const clearBtn = document.getElementById('clearBtn');

// State
let currentResponse = null;

// API Calls
async function makeApiRequest(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        showError('Failed to communicate with the AI service. Please try again.');
        return null;
    }
}

// Event Handlers
queryBtn.addEventListener('click', async () => {
    const query = inputText.value.trim();
    if (!query) {
        showError('Please enter a question.');
        return;
    }

    showLoading();
    const response = await makeApiRequest('query', { query });
    if (response) {
        showResponse(response.response);
        currentResponse = response.response;
        enableInsertButton();
    }
});

draftBtn.addEventListener('click', async () => {
    const content = inputText.value.trim();
    if (!content) {
        showError('Please enter content requirements.');
        return;
    }

    showLoading();
    const response = await makeApiRequest('draft', { content });
    if (response) {
        showResponse(response.draft);
        currentResponse = response.draft;
        enableInsertButton();
    }
});

reviewBtn.addEventListener('click', async () => {
    const content = inputText.value.trim();
    if (!content) {
        showError('Please enter content to review.');
        return;
    }

    showLoading();
    const response = await makeApiRequest('review', { content });
    if (response) {
        showResponse(formatReviewResponse(response.review));
        currentResponse = response.review;
        enableInsertButton();
    }
});

insertBtn.addEventListener('click', () => {
    if (currentResponse) {
        insertIntoFlareDocument(currentResponse);
    }
});

clearBtn.addEventListener('click', () => {
    inputText.value = '';
    responseArea.innerHTML = '<p class="placeholder">AI response will appear here...</p>';
    currentResponse = null;
    disableInsertButton();
});

// Utility Functions
function showLoading() {
    responseArea.innerHTML = '<p>Processing request...</p>';
    disableInsertButton();
}

function showError(message) {
    responseArea.innerHTML = `<p style="color: red;">${message}</p>`;
    disableInsertButton();
}

function showResponse(response) {
    responseArea.innerHTML = `<p>${response}</p>`;
}

function formatReviewResponse(review) {
    if (typeof review === 'string') {
        return review;
    }
    
    let formattedResponse = '';
    if (review.suggestions) {
        formattedResponse += '<h3>Suggestions:</h3>';
        formattedResponse += '<ul>';
        review.suggestions.forEach(suggestion => {
            formattedResponse += `<li>${suggestion}</li>`;
        });
        formattedResponse += '</ul>';
    }
    return formattedResponse;
}

function enableInsertButton() {
    insertBtn.disabled = false;
}

function disableInsertButton() {
    insertBtn.disabled = true;
}

// Flare Integration
function insertIntoFlareDocument(content) {
    // TODO: Implement actual Flare integration
    // This will need to be implemented based on Flare's API
    console.log('Inserting into Flare document:', content);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    disableInsertButton();
}); 