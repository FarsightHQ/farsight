/**
 * NodeRenderer - Handles node rendering, styling, and interactions
 */
class NodeRenderer {
    constructor(svg, tooltip, assetManager, width, height) {
        this.svg = svg;
        this.tooltip = tooltip;
        this.assetManager = assetManager;
        this.width = width;
        this.height = height;
        this.nodeGroup = null;
        this.nodes = [];
    }

    /**
     * Initialize node group
     */
    init() {
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
    }

    /**
     * Render nodes
     */
    render(nodes) {
        this.nodes = nodes;
        
        const nodeSelection = this.nodeGroup
            .selectAll('.node')
            .data(nodes, d => d.id);

        // Remove old nodes
        nodeSelection.exit().remove();

        // Create new nodes
        const nodeEnter = nodeSelection.enter()
            .append('g')
            .attr('class', 'node');

        // Add circles
        nodeEnter.append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', d => this.getNodeStroke(d))
            .attr('stroke-width', d => this.getNodeStrokeWidth(d));

        // Add labels
        nodeEnter.append('text')
            .attr('dx', 0)
            .attr('dy', d => this.getNodeRadius(d) + 15)
            .attr('text-anchor', 'middle')
            .attr('font-size', '10px')
            .attr('fill', '#333')
            .text(d => d.label);

        // Merge enter and update selections
        const nodeUpdate = nodeEnter.merge(nodeSelection);

        // Add event handlers
        this.addEventHandlers(nodeUpdate);

        return nodeUpdate;
    }

    /**
     * Get node radius based on type
     */
    getNodeRadius(d) {
        switch (d.type) {
            case 'source': return 12;
            case 'incoming': return 8;
            case 'outgoing': return 8;
            default: return 6;
        }
    }

    /**
     * Get node color based on type and asset status
     */
    getNodeColor(d) {
        if (d.type === 'source') {
            return d.hasAsset ? '#2E86AB' : '#A23B72';
        }
        
        const baseColors = {
            'incoming': d.hasAsset ? '#F18F01' : '#FFBA08',
            'outgoing': d.hasAsset ? '#C73E1D' : '#FF6B35',
            'related': d.hasAsset ? '#6A994E' : '#A7C957'
        };

        return baseColors[d.type] || '#95A5A6';
    }

    /**
     * Get node stroke color
     */
    getNodeStroke(d) {
        return d.hasAsset ? '#2C3E50' : '#7F8C8D';
    }

    /**
     * Get node stroke width
     */
    getNodeStrokeWidth(d) {
        return d.type === 'source' ? 3 : 2;
    }

    /**
     * Add event handlers to nodes
     */
    addEventHandlers(nodeSelection) {
        nodeSelection
            .on('mouseover', (event, d) => this.handleMouseOver(event, d))
            .on('mouseout', () => this.handleMouseOut())
            .on('click', (event, d) => this.handleClick(event, d))
            .call(d3.drag()
                .on('start', (event, d) => this.handleDragStart(event, d))
                .on('drag', (event, d) => this.handleDrag(event, d))
                .on('end', (event, d) => this.handleDragEnd(event, d)));
    }

    /**
     * Handle mouse over event
     */
    handleMouseOver(event, d) {
        // Show tooltip
        const tooltipData = this.assetManager.getAssetTooltipData(d.id);
        
        this.tooltip.transition()
            .duration(200)
            .style('opacity', .9);
            
        this.tooltip.html(tooltipData.content)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');

        // Highlight node
        d3.select(event.currentTarget)
            .select('circle')
            .attr('stroke-width', this.getNodeStrokeWidth(d) + 2)
            .attr('filter', 'url(#glow)');
    }

    /**
     * Handle mouse out event
     */
    handleMouseOut() {
        // Hide tooltip
        this.tooltip.transition()
            .duration(500)
            .style('opacity', 0);

        // Remove highlight
        this.nodeGroup.selectAll('circle')
            .attr('stroke-width', d => this.getNodeStrokeWidth(d))
            .attr('filter', null);
    }

    /**
     * Handle click event
     */
    handleClick(event, d) {
        // Dispatch custom event for node click
        const customEvent = new CustomEvent('nodeClick', {
            detail: { node: d, event: event }
        });
        document.dispatchEvent(customEvent);
    }

    /**
     * Handle drag start
     */
    handleDragStart(event, d) {
        if (!event.active) {
            // Notify simulation of drag start
            const customEvent = new CustomEvent('dragStart', {
                detail: { node: d, simulation: event.subject }
            });
            document.dispatchEvent(customEvent);
        }
        d.fx = d.x;
        d.fy = d.y;
    }

    /**
     * Handle drag
     */
    handleDrag(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    /**
     * Handle drag end
     */
    handleDragEnd(event, d) {
        if (!event.active) {
            // Notify simulation of drag end
            const customEvent = new CustomEvent('dragEnd', {
                detail: { node: d }
            });
            document.dispatchEvent(customEvent);
        }
        d.fx = null;
        d.fy = null;
    }

    /**
     * Update node positions
     */
    updatePositions() {
        this.nodeGroup.selectAll('.node')
            .attr('transform', d => {
                // Add boundary checking to ensure nodes stay within viewport
                const x = Math.max(20, Math.min(d.x || 0, this.width - 20));
                const y = Math.max(20, Math.min(d.y || 0, this.height - 20));
                return `translate(${x},${y})`;
            });
    }

    /**
     * Update dimensions
     */
    updateDimensions(width, height) {
        this.width = width;
        this.height = height;
    }

    /**
     * Get nodes by type
     */
    getNodesByType(type) {
        return this.nodes.filter(node => node.type === type);
    }

    /**
     * Get source node
     */
    getSourceNode() {
        return this.nodes.find(node => node.type === 'source');
    }

    /**
     * Clear all nodes
     */
    clear() {
        if (this.nodeGroup) {
            this.nodeGroup.selectAll('*').remove();
        }
        this.nodes = [];
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NodeRenderer;
}
