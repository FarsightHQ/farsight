/**
 * FARNetworkViz - Main orchestrator for FAR Network Visualization
 * Coordinates all modules and provides the main interface
 */
class FARNetworkViz {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            throw new Error(`Container with id '${containerId}' not found`);
        }

        // Configuration
        this.config = {
            width: options.width || 1200,
            height: options.height || 800,
            margin: options.margin || { top: 20, right: 20, bottom: 20, left: 20 },
            apiBaseUrl: options.apiBaseUrl || '/api/v1',
            ...options
        };

        // Initialize modules
        this.networkLoader = new NetworkLoader(this.config.apiBaseUrl);
        this.assetManager = new AssetManager();
        this.dataProcessor = new DataProcessor();
        this.eventHandler = new EventHandler();
        
        // Initialize layout and rendering components
        this.segmentLayout = new SegmentLayout(this.config.width, this.config.height);
        this.forceSimulation = new ForceSimulation(this.config.width, this.config.height, this.segmentLayout);
        
        // Will be initialized after SVG creation
        this.nodeRenderer = null;
        this.linkRenderer = null;
        
        // Data storage
        this.currentData = {
            sourceIp: null,
            nodes: [],
            links: [],
            rulesData: null,
            assetData: []
        };

        // State
        this.isInitialized = false;
        
        this.init();
    }

    /**
     * Initialize the visualization
     */
    init() {
        try {
            this.createSVG();
            this.initializeRenderers();
            this.setupEventHandlers();
            this.isInitialized = true;
            console.log('FARNetworkViz initialized successfully');
        } catch (error) {
            console.error('Failed to initialize FARNetworkViz:', error);
            throw error;
        }
    }

    /**
     * Create SVG container
     */
    createSVG() {
        // Clear existing content
        this.container.innerHTML = '';

        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.config.width)
            .attr('height', this.config.height)
            .attr('viewBox', `0 0 ${this.config.width} ${this.config.height}`)
            .style('border', '1px solid #ccc')
            .style('background-color', '#f9f9f9');

        // Create tooltip
        this.tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('text-align', 'left')
            .style('padding', '10px')
            .style('font', '12px sans-serif')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('border-radius', '8px')
            .style('pointer-events', 'none')
            .style('opacity', 0);
    }

    /**
     * Initialize rendering components
     */
    initializeRenderers() {
        this.nodeRenderer = new NodeRenderer(this.svg, this.tooltip, this.assetManager, this.config.width, this.config.height);
        this.linkRenderer = new LinkRenderer(this.svg);
        
        this.nodeRenderer.init();
        this.linkRenderer.init();
        
        this.forceSimulation.init();
        
        // Add debug group for segment visualization
        this.debugGroup = this.svg.append('g').attr('class', 'debug-layer');
    }

    /**
     * Setup event handlers
     */
    setupEventHandlers() {
        // Setup form handlers
        this.eventHandler.setupFormHandlers(this);

        // Listen for custom events
        this.eventHandler.on('nodeClick', (data) => {
            console.log('Node clicked:', data.node.id);
        });

        this.eventHandler.on('typeFilterChange', (selectedTypes) => {
            this.applyFilters();
        });

        this.eventHandler.on('segmentFilterChange', (selectedSegments) => {
            this.applyFilters();
        });

        this.eventHandler.on('assetFilterChange', (showAssetsOnly) => {
            this.applyFilters();
        });

        // Listen for debug toggle
        window.addEventListener('keydown', (event) => {
            if (event.key === 'd' && event.ctrlKey) {
                event.preventDefault();
                this.toggleDebugMode();
            }
        });

        // Setup simulation tick handler
        this.forceSimulation.onTick(() => {
            this.nodeRenderer.updatePositions();
            this.linkRenderer.updatePositions();
        });
        
        // Add simulation end handler for debugging
        this.forceSimulation.onEnd(() => {
            console.log('Force simulation ended');
            const stats = this.forceSimulation.getStats();
            console.log('Final simulation stats:', stats);
        });
    }

    /**
     * Load network data for a given IP
     */
    async loadNetworkData(ipAddress) {
        if (!this.isInitialized) {
            throw new Error('Visualization not initialized');
        }

        try {
            this.eventHandler.showLoading();
            this.eventHandler.clearError();
            
            console.log(`Loading network data for IP: ${ipAddress}`);
            this.currentData.sourceIp = ipAddress;

            // Load firewall rules
            console.log('Fetching firewall rules...');
            this.currentData.rulesData = await this.networkLoader.fetchFirewallRules(ipAddress);
            
            // Process relationships to get unique IPs
            const { uniqueIPs } = this.dataProcessor.processFirewallRelationships(
                this.currentData.rulesData, 
                ipAddress
            );

            // Load asset data for all IPs
            console.log(`Fetching asset data for ${uniqueIPs.size} IPs...`);
            console.log('IPs to lookup:', Array.from(uniqueIPs));
            this.currentData.assetData = await this.networkLoader.fetchMultipleAssets(Array.from(uniqueIPs));
            console.log('Asset data received:', this.currentData.assetData);
            
            // Create asset map directly from the NetworkLoader results
            this.assetManager.assetMap = this.networkLoader.createAssetMap(this.currentData.assetData);
            console.log('Asset map after processing:', Object.fromEntries(this.assetManager.assetMap));
            
            // Render the network with enriched data
            this.render();
            
        } catch (error) {
            console.error('Error loading network data:', error);
            this.eventHandler.showError(`Failed to load network data: ${error.message}`);
        } finally {
            this.eventHandler.hideLoading();
        }
    }

    /**
     * Render the network visualization
     */
    render() {
        try {
            if (!this.currentData.rulesData || !this.currentData.sourceIp) {
                console.log('No data to render');
                return;
            }

            // Process firewall relationships
            const { uniqueIPs, ipTypes, ruleRelationships } = this.dataProcessor.processFirewallRelationships(
                this.currentData.rulesData,
                this.currentData.sourceIp
            );

            // Create asset map
            const assetMap = this.assetManager.assetMap;

            // Create nodes and links
            this.currentData.nodes = this.dataProcessor.createNodes(this.currentData.sourceIp, ipTypes, assetMap);
            this.currentData.links = this.dataProcessor.createLinks(ruleRelationships);

            console.log(`Rendering ${this.currentData.nodes.length} nodes and ${this.currentData.links.length} links`);
            console.log('Nodes with segments:', this.currentData.nodes.map(n => `${n.id} (type: ${n.type}, segment: ${n.segment})`));
            
            // Check for source node
            const sourceNode = this.currentData.nodes.find(n => n.type === 'source');
            if (sourceNode) {
                console.log('Source node found:', sourceNode);
            } else {
                console.error('No source node found in nodes array!');
            }

            // Update simulation with reduced initial energy
            this.forceSimulation.update(this.currentData.nodes, this.currentData.links);

            // Render nodes and links
            this.nodeRenderer.render(this.currentData.nodes);
            this.linkRenderer.render(this.currentData.links);
            
            // Add debug visualization for segments
            this.renderSegmentDebugInfo();

            // Start simulation with higher alpha and gradually reduce
            this.forceSimulation.setAlpha(0.8);
            this.forceSimulation.start();
            
            // Apply cooling schedule for better stabilization
            setTimeout(() => {
                if (this.forceSimulation.getAlpha() > 0.1) {
                    this.forceSimulation.setAlpha(0.3);
                }
            }, 1000);
            
            setTimeout(() => {
                if (this.forceSimulation.getAlpha() > 0.05) {
                    this.forceSimulation.setAlpha(0.1);
                }
            }, 3000);

            // Update UI components
            this.updateLegend();
            this.updateStatistics();

        } catch (error) {
            console.error('Error rendering network:', error);
            this.eventHandler.showError(`Failed to render network: ${error.message}`);
        }
    }

    /**
     * Update legend
     */
    updateLegend() {
        const legendData = this.segmentLayout.createLegendData(this.currentData.nodes);
        this.eventHandler.updateLegend(legendData);
    }

    /**
     * Update statistics
     */
    updateStatistics() {
        const stats = {
            nodeCount: this.currentData.nodes.length,
            linkCount: this.currentData.links.length,
            segmentCount: this.segmentLayout.getAllSegments().length,
            assetCount: this.currentData.nodes.filter(n => n.hasAsset).length
        };
        this.eventHandler.updateStats(stats);
    }

    /**
     * Render debug information for segments
     */
    renderSegmentDebugInfo() {
        if (!this.debugGroup) return;
        
        // Clear previous debug info
        this.debugGroup.selectAll('*').remove();
        
        // Get all segment positions
        const segments = this.segmentLayout.getAllSegments();
        
        segments.forEach(segment => {
            const pos = this.segmentLayout.getSegmentPosition(segment);
            const color = this.segmentLayout.getSegmentColor(segment);
            
            if (pos && segment !== 'source') { // Don't draw debug circle for source
                // Draw segment circle
                this.debugGroup.append('circle')
                    .attr('cx', pos.x)
                    .attr('cy', pos.y)
                    .attr('r', 80)
                    .attr('fill', 'none')
                    .attr('stroke', color)
                    .attr('stroke-width', 2)
                    .attr('stroke-dasharray', '5,5')
                    .attr('opacity', 0.3);
                
                // Add segment label
                this.debugGroup.append('text')
                    .attr('x', pos.x)
                    .attr('y', pos.y - 90)
                    .attr('text-anchor', 'middle')
                    .attr('font-size', '12px')
                    .attr('font-weight', 'bold')
                    .attr('fill', color)
                    .text(segment || 'Unknown');
            }
        });
        
        // Add center marker for source
        this.debugGroup.append('circle')
            .attr('cx', this.config.width / 2)
            .attr('cy', this.config.height / 2)
            .attr('r', 5)
            .attr('fill', '#E74C3C')
            .attr('opacity', 0.7);
        
        this.debugGroup.append('text')
            .attr('x', this.config.width / 2)
            .attr('y', this.config.height / 2 - 15)
            .attr('text-anchor', 'middle')
            .attr('font-size', '10px')
            .attr('font-weight', 'bold')
            .attr('fill', '#E74C3C')
            .text('SOURCE');
    }

    /**
     * Toggle debug mode
     */
    toggleDebugMode() {
        if (!this.debugGroup) return;
        
        const isVisible = this.debugGroup.style('display') !== 'none';
        this.debugGroup.style('display', isVisible ? 'none' : 'block');
        console.log(`Debug mode ${isVisible ? 'disabled' : 'enabled'}. Press Ctrl+D to toggle.`);
    }

    /**
     * Apply filters to the visualization
     */
    applyFilters() {
        // Implementation for filtering based on UI controls
        // This would filter nodes and links based on selected criteria
        console.log('Applying filters...');
        // TODO: Implement filtering logic
    }

    /**
     * Clear the visualization
     */
    clear() {
        console.log('Clearing visualization');
        
        // Clear data
        this.currentData = {
            sourceIp: null,
            nodes: [],
            links: [],
            rulesData: null,
            assetData: []
        };

        // Clear renderers
        if (this.nodeRenderer) this.nodeRenderer.clear();
        if (this.linkRenderer) this.linkRenderer.clear();

        // Stop simulation
        if (this.forceSimulation) this.forceSimulation.stop();

        // Clear asset manager
        this.assetManager.clear();

        // Clear UI
        this.eventHandler.clearInfoPanel();
        this.eventHandler.clearError();

        // Clear IP input
        const ipInput = document.getElementById('ipInput');
        if (ipInput) ipInput.value = '';

        console.log('Visualization cleared');
    }

    /**
     * Resize the visualization
     */
    resize(width, height) {
        this.config.width = width;
        this.config.height = height;

        // Update SVG
        this.svg
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`);

        // Update renderers
        if (this.nodeRenderer) {
            this.nodeRenderer.updateDimensions(width, height);
        }

        // Update layout and simulation
        this.segmentLayout.updateDimensions(width, height);
        this.forceSimulation.updateDimensions(width, height);

        // Restart simulation
        if (this.currentData.nodes.length > 0) {
            this.forceSimulation.restart(0.3);
        }
    }

    /**
     * Get current visualization state
     */
    getState() {
        return {
            sourceIp: this.currentData.sourceIp,
            nodeCount: this.currentData.nodes.length,
            linkCount: this.currentData.links.length,
            segments: this.segmentLayout.getAllSegments(),
            isLoaded: this.currentData.sourceIp !== null,
            simulationStats: this.forceSimulation.getStats()
        };
    }

    /**
     * Export visualization data
     */
    exportData() {
        return {
            sourceIp: this.currentData.sourceIp,
            nodes: this.currentData.nodes,
            links: this.currentData.links,
            assetData: this.currentData.assetData,
            rulesData: this.currentData.rulesData
        };
    }

    /**
     * Destroy the visualization and cleanup
     */
    destroy() {
        console.log('Destroying FARNetworkViz');
        
        // Stop simulation
        if (this.forceSimulation) {
            this.forceSimulation.destroy();
        }

        // Remove tooltip
        if (this.tooltip) {
            this.tooltip.remove();
        }

        // Clear container
        if (this.container) {
            this.container.innerHTML = '';
        }

        // Cleanup event handlers
        if (this.eventHandler) {
            this.eventHandler.destroy();
        }

        // Clear references
        this.svg = null;
        this.tooltip = null;
        this.nodeRenderer = null;
        this.linkRenderer = null;
        this.forceSimulation = null;
        this.segmentLayout = null;
        this.assetManager = null;
        this.dataProcessor = null;
        this.eventHandler = null;
        this.networkLoader = null;

        this.isInitialized = false;
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FARNetworkViz;
}
