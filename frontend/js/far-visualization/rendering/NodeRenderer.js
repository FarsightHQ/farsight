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

        // Merge enter and update selections
        const nodeUpdate = nodeEnter.merge(nodeSelection);

        // Add event handlers
        this.addEventHandlers(nodeUpdate);

        // Add labels separately after nodes are created
        this.addLabels(nodeUpdate);

        return nodeUpdate;
    }

    /**
     * Add labels to nodes
     */
    addLabels(nodeSelection) {
        // Remove existing labels
        nodeSelection.selectAll('text').remove();
        
        // Add IP address labels
        nodeSelection.append('text')
            .attr('class', 'ip-label')
            .attr('x', 0)
            .attr('y', d => this.getNodeRadius(d) + 18)
            .attr('text-anchor', 'middle')
            .attr('font-size', '10px')
            .attr('font-weight', 'normal')
            .attr('fill', '#000000')
            .style('pointer-events', 'none')
            .text(d => d.label || d.id);

        // Add VM display name labels
        nodeSelection.append('text')
            .attr('class', 'vm-label')
            .attr('x', 0)
            .attr('y', d => this.getNodeRadius(d) + 32)
            .attr('text-anchor', 'middle')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .attr('fill', '#000000')
            .style('pointer-events', 'none')
            .text(d => {
                const vmName = d.vm_display_name || 'Unknown Asset';
                console.log(`Adding label for ${d.id}: ${vmName}`);
                return this.truncateText(vmName, 20);
            });
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
        switch (d.type) {
            case 'source':
                return '#E74C3C'; // Red for source/main IP
            case 'incoming':
                return '#E74C3C'; // Red for incoming IPs
            case 'outgoing':
                return '#27AE60'; // Green for outgoing IPs
            case 'related':
                return '#95A5A6'; // Gray for related IPs
            default:
                return '#95A5A6'; // Default gray
        }
    }

    /**
     * Get node stroke color
     */
    getNodeStroke(d) {
        return '#000000'; // Always black border
    }

    /**
     * Get node stroke width
     */
    getNodeStrokeWidth(d) {
        return 1; // Always 1px border
    }

    /**
     * Truncate text to specified length
     */
    truncateText(text, maxLength) {
        if (!text || text === 'Unknown Asset' || text === null || text === undefined) {
            return text || 'Unknown Asset';
        }
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 2) + '..';
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
