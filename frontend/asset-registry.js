const API_BASE = 'http://localhost:8000/api/v1';

// File input handling
function initializeFileUpload() {
    const fileInput = document.getElementById('csvFile');
    const uploadBtn = document.getElementById('uploadBtn');
    
    uploadBtn.addEventListener('click', uploadCSV);
    
    // Load analytics on page load
    loadAnalytics();
}

async function uploadCSV() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('Please select a CSV file first.', 'error');
        return;
    }
    
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showStatus('Please select a valid CSV file.', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    document.getElementById('loading').style.display = 'block';
    document.getElementById('uploadBtn').disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/assets/upload-csv?uploaded_by=user`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        showUploadResults(result);
        
        // Refresh analytics after successful upload
        setTimeout(loadAnalytics, 1000);
        
    } catch (error) {
        showStatus(`Upload failed: ${error.message}`, 'error');
        console.error('Upload error:', error);
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('uploadBtn').disabled = false;
    }
}

function showUploadResults(result) {
    const summary = result.summary;
    const statusMessage = result.message;
    
    const resultsHTML = `
        <div class="status success">
            ${statusMessage}
        </div>
        <div class="results">
            <p><strong>Total Rows:</strong> ${summary.total_rows}</p>
            <p><strong>Created:</strong> ${summary.created_assets}</p>
            <p><strong>Updated:</strong> ${summary.updated_assets}</p>
            <p><strong>Errors:</strong> ${summary.error_rows}</p>
            <p><strong>Batch ID:</strong> ${result.batch_id}</p>
            <p><strong>Processing Time:</strong> ${summary.processing_time_ms}ms</p>
        </div>
    `;
    
    document.getElementById('results').innerHTML = resultsHTML;
}

async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const analytics = await response.json();
        showAnalytics(analytics);
        
    } catch (error) {
        document.getElementById('analytics-content').innerHTML = `
            <div class="status error">Failed to load analytics: ${error.message}</div>
        `;
    }
}

function showAnalytics(analytics) {
    let analyticsHTML = `
        <h3>Asset Statistics</h3>
        <p><strong>Total Assets:</strong> ${analytics.total_assets}</p>
        <p><strong>Active Assets:</strong> ${analytics.active_assets}</p>
        <p><strong>Total vCPU:</strong> ${analytics.total_vcpu || 0}</p>
        <p><strong>Total Memory:</strong> ${analytics.total_memory_gb ? Math.round(analytics.total_memory_gb) : 0} GB</p>
    `;
    
    // Environments
    if (Object.keys(analytics.environments || {}).length > 0) {
        analyticsHTML += '<h4>Environments:</h4><ul>';
        Object.entries(analytics.environments).forEach(([env, count]) => {
            analyticsHTML += `<li>${env}: ${count}</li>`;
        });
        analyticsHTML += '</ul>';
    }
    
    // Operating Systems
    if (Object.keys(analytics.operating_systems || {}).length > 0) {
        analyticsHTML += '<h4>Operating Systems:</h4><ul>';
        Object.entries(analytics.operating_systems).forEach(([os, count]) => {
            analyticsHTML += `<li>${os}: ${count}</li>`;
        });
        analyticsHTML += '</ul>';
    }
    
    // Business Units
    if (Object.keys(analytics.business_units || {}).length > 0) {
        analyticsHTML += '<h4>Business Units:</h4><ul>';
        Object.entries(analytics.business_units).forEach(([bu, count]) => {
            analyticsHTML += `<li>${bu}: ${count}</li>`;
        });
        analyticsHTML += '</ul>';
    }
    
    analyticsHTML += `<p><small>Last updated: ${new Date(analytics.last_updated).toLocaleString()}</small></p>`;
    
    document.getElementById('analytics-content').innerHTML = analyticsHTML;
}

function showStatus(message, type) {
    document.getElementById('results').innerHTML = `
        <div class="status ${type}">${message}</div>
    `;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeFileUpload);
