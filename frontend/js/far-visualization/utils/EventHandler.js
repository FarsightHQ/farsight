/**
 * EventHandler - Manages UI events and interactions
 */
class EventHandler {
    constructor() {
        this.listeners = new Map();
        this.setupGlobalListeners();
    }

    /**
     * Setup global event listeners
     */
    setupGlobalListeners() {
        // Listen for custom events from other modules
        document.addEventListener('nodeClick', (event) => {
            this.handleNodeClick(event.detail);
        });

        document.addEventListener('dragStart', (event) => {
            this.handleDragStart(event.detail);
        });

        document.addEventListener('dragEnd', (event) => {
            this.handleDragEnd(event.detail);
        });
    }

    /**
     * Add event listener
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * Emit event
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Handle node click
     */
    handleNodeClick(detail) {
        const { node, event } = detail;
        console.log('Node clicked:', node.id);
        
        // Emit node click event
        this.emit('nodeClick', { node, event });
        
        // Update info panel if available
        this.updateInfoPanel(node);
    }

    /**
     * Handle drag start
     */
    handleDragStart(detail) {
        const { node, simulation } = detail;
        console.log('Drag started on node:', node.id);
        
        // Emit drag start event
        this.emit('dragStart', { node, simulation });
    }

    /**
     * Handle drag end
     */
    handleDragEnd(detail) {
        const { node } = detail;
        console.log('Drag ended on node:', node.id);
        
        // Emit drag end event
        this.emit('dragEnd', { node });
    }

    /**
     * Setup form event handlers
     */
    setupFormHandlers(visualization) {
        // IP input form
        const form = document.getElementById('ipForm');
        const input = document.getElementById('ipInput');
        const loadBtn = document.getElementById('loadBtn');
        const clearBtn = document.getElementById('clearBtn');

        if (form) {
            form.addEventListener('submit', (event) => {
                event.preventDefault();
                const ip = input.value.trim();
                if (ip && this.isValidIP(ip)) {
                    visualization.loadNetworkData(ip);
                } else {
                    this.showError('Please enter a valid IP address');
                }
            });
        }

        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                const ip = input.value.trim();
                if (ip && this.isValidIP(ip)) {
                    visualization.loadNetworkData(ip);
                } else {
                    this.showError('Please enter a valid IP address');
                }
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                visualization.clear();
                this.clearInfoPanel();
                this.clearError();
            });
        }

        // Filter controls
        this.setupFilterHandlers(visualization);
    }

    /**
     * Setup filter event handlers
     */
    setupFilterHandlers(visualization) {
        // Type filters
        const typeFilters = document.querySelectorAll('input[name="typeFilter"]');
        typeFilters.forEach(filter => {
            filter.addEventListener('change', () => {
                const selectedTypes = Array.from(typeFilters)
                    .filter(f => f.checked)
                    .map(f => f.value);
                this.emit('typeFilterChange', selectedTypes);
            });
        });

        // Segment filters
        const segmentFilters = document.querySelectorAll('input[name="segmentFilter"]');
        segmentFilters.forEach(filter => {
            filter.addEventListener('change', () => {
                const selectedSegments = Array.from(segmentFilters)
                    .filter(f => f.checked)
                    .map(f => f.value);
                this.emit('segmentFilterChange', selectedSegments);
            });
        });

        // Show/hide asset filter
        const assetFilter = document.getElementById('showAssetsOnly');
        if (assetFilter) {
            assetFilter.addEventListener('change', () => {
                this.emit('assetFilterChange', assetFilter.checked);
            });
        }
    }

    /**
     * Update info panel with node information
     */
    updateInfoPanel(node) {
        const infoPanel = document.getElementById('infoPanel');
        const selectedNodeInfo = document.getElementById('selectedNodeInfo');
        
        if (infoPanel && selectedNodeInfo) {
            selectedNodeInfo.innerHTML = `
                <h4>Selected Node: ${node.id}</h4>
                <p><strong>Type:</strong> ${node.type}</p>
                <p><strong>Segment:</strong> ${node.segment}</p>
                <p><strong>Has Asset:</strong> ${node.hasAsset ? 'Yes' : 'No'}</p>
                ${node.asset ? `
                    <p><strong>Hostname:</strong> ${node.asset.hostname || 'N/A'}</p>
                    <p><strong>OS:</strong> ${node.asset.os_name || 'N/A'} ${node.asset.os_version || ''}</p>
                    <p><strong>Environment:</strong> ${node.asset.environment || 'N/A'}</p>
                    <p><strong>Owner:</strong> ${node.asset.owner || 'N/A'}</p>
                ` : ''}
            `;
            infoPanel.style.display = 'block';
        }
    }

    /**
     * Clear info panel
     */
    clearInfoPanel() {
        const selectedNodeInfo = document.getElementById('selectedNodeInfo');
        if (selectedNodeInfo) {
            selectedNodeInfo.innerHTML = '<p>Click on a node to see details</p>';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorElement = document.getElementById('error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        } else {
            alert(message);
        }
    }

    /**
     * Clear error message
     */
    clearError() {
        const errorElement = document.getElementById('error');
        if (errorElement) {
            errorElement.style.display = 'none';
            errorElement.textContent = '';
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }

        const loadBtn = document.getElementById('loadBtn');
        if (loadBtn) {
            loadBtn.disabled = true;
            loadBtn.textContent = 'Loading...';
        }
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        const loadBtn = document.getElementById('loadBtn');
        if (loadBtn) {
            loadBtn.disabled = false;
            loadBtn.textContent = 'Load Network';
        }
    }

    /**
     * Validate IP address
     */
    isValidIP(ip) {
        const ipPattern = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipPattern.test(ip);
    }

    /**
     * Update legend
     */
    updateLegend(legendData) {
        const legend = document.getElementById('legend');
        if (legend && legendData) {
            legend.innerHTML = '<h4>Segments</h4>' + 
                legendData.map(item => `
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: ${item.color}"></span>
                        <span class="legend-label">${item.segment} (${item.stats.total})</span>
                    </div>
                `).join('');
        }
    }

    /**
     * Update statistics
     */
    updateStats(stats) {
        const statsElement = document.getElementById('stats');
        if (statsElement && stats) {
            statsElement.innerHTML = `
                <h4>Network Statistics</h4>
                <p>Total Nodes: ${stats.nodeCount || 0}</p>
                <p>Total Links: ${stats.linkCount || 0}</p>
                <p>Unique Segments: ${stats.segmentCount || 0}</p>
                <p>Nodes with Assets: ${stats.assetCount || 0}</p>
            `;
        }
    }

    /**
     * Cleanup event listeners
     */
    destroy() {
        this.listeners.clear();
        document.removeEventListener('nodeClick', this.handleNodeClick);
        document.removeEventListener('dragStart', this.handleDragStart);
        document.removeEventListener('dragEnd', this.handleDragEnd);
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EventHandler;
}
