/**
 * LinkRenderer - Handles link rendering, styling, and interactions
 */
class LinkRenderer {
    constructor(svg) {
        this.svg = svg;
        this.linkGroup = null;
        this.links = [];
    }

    /**
     * Initialize link group with arrow markers
     */
    init() {
        // Create defs for arrow markers
        const defs = this.svg.append('defs');
        
        // Create arrow marker for outbound links
        defs.append('marker')
            .attr('id', 'arrow-outbound')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#C73E1D');

        // Create arrow marker for inbound links
        defs.append('marker')
            .attr('id', 'arrow-inbound')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#F18F01');

        // Create arrow marker for related links
        defs.append('marker')
            .attr('id', 'arrow-related')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#6A994E');

        // Create glow filter
        const filter = defs.append('filter')
            .attr('id', 'glow');
        
        filter.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'coloredBlur');
        
        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        this.linkGroup = this.svg.append('g').attr('class', 'links');
    }

    /**
     * Render links
     */
    render(links) {
        this.links = links;
        
        const linkSelection = this.linkGroup
            .selectAll('.link')
            .data(links, d => `${d.source.id || d.source}-${d.target.id || d.target}`);

        // Remove old links
        linkSelection.exit().remove();

        // Create new links
        const linkEnter = linkSelection.enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', d => this.getLinkColor(d))
            .attr('stroke-width', d => this.getLinkWidth(d))
            .attr('stroke-opacity', 0.8)
            .attr('marker-end', d => this.getLinkMarker(d));

        // Merge enter and update selections
        const linkUpdate = linkEnter.merge(linkSelection);

        // Add event handlers
        this.addEventHandlers(linkUpdate);

        return linkUpdate;
    }

    /**
     * Get link color based on direction
     */
    getLinkColor(d) {
        switch (d.direction) {
            case 'outbound': return '#C73E1D';
            case 'inbound': return '#F18F01';
            case 'related': return '#6A994E';
            default: return '#95A5A6';
        }
    }

    /**
     * Get link width based on type
     */
    getLinkWidth(d) {
        return 2;
    }

    /**
     * Get link marker based on direction
     */
    getLinkMarker(d) {
        switch (d.direction) {
            case 'outbound': return 'url(#arrow-outbound)';
            case 'inbound': return 'url(#arrow-inbound)';
            case 'related': return 'url(#arrow-related)';
            default: return null;
        }
    }

    /**
     * Add event handlers to links
     */
    addEventHandlers(linkSelection) {
        linkSelection
            .on('mouseover', (event, d) => this.handleMouseOver(event, d))
            .on('mouseout', (event, d) => this.handleMouseOut(event, d));
    }

    /**
     * Handle mouse over event
     */
    handleMouseOver(event, d) {
        // Highlight link
        d3.select(event.currentTarget)
            .attr('stroke-width', this.getLinkWidth(d) + 2)
            .attr('stroke-opacity', 1)
            .attr('filter', 'url(#glow)');

        // Show link info (could be extended with tooltip)
        console.log('Link:', d.label, 'Direction:', d.direction);
    }

    /**
     * Handle mouse out event
     */
    handleMouseOut(event, d) {
        // Remove highlight
        d3.select(event.currentTarget)
            .attr('stroke-width', this.getLinkWidth(d))
            .attr('stroke-opacity', 0.8)
            .attr('filter', null);
    }

    /**
     * Update link positions
     */
    updatePositions() {
        this.linkGroup.selectAll('.link')
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
    }

    /**
     * Get links by direction
     */
    getLinksByDirection(direction) {
        return this.links.filter(link => link.direction === direction);
    }

    /**
     * Get links connected to a node
     */
    getLinksForNode(nodeId) {
        return this.links.filter(link => 
            (link.source.id || link.source) === nodeId || 
            (link.target.id || link.target) === nodeId
        );
    }

    /**
     * Clear all links
     */
    clear() {
        if (this.linkGroup) {
            this.linkGroup.selectAll('*').remove();
        }
        this.links = [];
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LinkRenderer;
}
