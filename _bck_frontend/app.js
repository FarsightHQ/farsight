// Minimal Farsight Frontend JavaScript
const API_BASE = 'http://localhost:8000/api/v1';

let currentRequestId = null;

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const csvFileInput = document.getElementById('csvFile');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');
const actionsDiv = document.getElementById('actions');

// Action buttons
const processBtn = document.getElementById('processBtn');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    uploadForm.addEventListener('submit', handleUpload);
    processBtn.addEventListener('click', () => processAll(currentRequestId));
});

// Handle file upload
async function handleUpload(e) {
    e.preventDefault();
    
    const title = document.getElementById('requestTitle').value;
    const externalId = document.getElementById('externalId').value;
    const file = csvFileInput.files[0];
    
    if (!file) {
        showStatus('Please select a CSV file');
        return;
    }
    
    // Build URL with query parameters
    const url = new URL(`${API_BASE}/requests`);
    url.searchParams.append('title', title);
    if (externalId) {
        url.searchParams.append('external_id', externalId);
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showStatus('Uploading...');
    
    try {
        const response = await fetch(url.toString(), {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        currentRequestId = result.id;
        
        showStatus(`Success! Request ID: ${result.id}`);
        showResults(result);
        enableActions();
        
    } catch (error) {
        showStatus(`Error: ${error.message}`);
        console.error('Upload error:', error);
    }
}

// Process All - CSV + All Facts
async function processAll(requestId) {
    if (!requestId) return;
    
    showStatus('Starting processing...');
    processBtn.disabled = true;
    
    try {
        // Step 1: Process CSV
        showStatus('Step 1/3: Processing CSV...');
        const ingestResponse = await fetch(`${API_BASE}/requests/${requestId}/ingest`, {
            method: 'POST'
        });
        
        if (!ingestResponse.ok) {
            const errorData = await ingestResponse.json();
            throw new Error(`CSV processing failed: ${errorData.detail || `HTTP ${ingestResponse.status}`}`);
        }
        
        const ingestResult = await ingestResponse.json();
        showResults(ingestResult);
        
        // Step 2: Compute Standard Facts
        showStatus('Step 2/3: Computing standard facts...');
        const factsResponse = await fetch(`${API_BASE}/requests/${requestId}/facts/compute`, {
            method: 'POST'
        });
        
        if (!factsResponse.ok) {
            const errorData = await factsResponse.json();
            throw new Error(`Facts computation failed: ${errorData.detail || `HTTP ${factsResponse.status}`}`);
        }
        
        const factsResult = await factsResponse.json();
        showResults(factsResult);
        
        // Step 3: Compute Hybrid Facts
        showStatus('Step 3/3: Computing hybrid facts...');
        const hybridResponse = await fetch(`${API_BASE}/requests/${requestId}/facts/compute-hybrid`, {
            method: 'POST'
        });
        
        if (!hybridResponse.ok) {
            const errorData = await hybridResponse.json();
            throw new Error(`Hybrid facts computation failed: ${errorData.detail || `HTTP ${hybridResponse.status}`}`);
        }
        
        const hybridResult = await hybridResponse.json();
        showResults(hybridResult);
        
        showStatus('✅ Processing completed successfully!');
        
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`);
        console.error('Process error:', error);
    } finally {
        processBtn.disabled = false;
    }
}

// Helper functions
function showStatus(message) {
    statusDiv.innerHTML = `<p><strong>Status:</strong> ${message}</p>`;
}

function showResults(data) {
    resultsDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

function enableActions() {
    actionsDiv.style.display = 'block';
    processBtn.disabled = false;
}
