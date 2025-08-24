/**
 * SegmentLayout - Handles segment-based node positioning and layout
 */
class SegmentLayout {
    constructor(width, height) {
        this.width = width;
        this.height = height;
        this.segmentPositions = new Map();
        this.segmentColors = new Map();
        this.colorScale = d3.scaleOrdinal(d3.schemeCategory10);
    }

    /**
     * Calculate segment positions based on nodes
     */
    calculateSegmentPositions(nodes) {
        if (!Array.isArray(nodes)) {
            console.warn('calculateSegmentPositions: nodes is not an array:', nodes);
            return this.segmentPositions;
        }
        
        // Get unique segments
        const segments = [...new Set(nodes.map(d => d.segment))];
        console.log('Unique segments found:', segments);

        // Clear previous positions
        this.segmentPositions.clear();
        this.segmentColors.clear();

        // Calculate positions for segments in a circular layout
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const radius = Math.min(this.width, this.height) / 4; // Increased radius for better spread

        segments.forEach((segment, index) => {
            const angle = (index * 2 * Math.PI) / segments.length;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            
            this.segmentPositions.set(segment, { x, y, angle, index });
            this.segmentColors.set(segment, this.colorScale(index));
        });

        console.log('Segment positions calculated:', Object.fromEntries(this.segmentPositions));
        return this.segmentPositions;
    }

    /**
     * Apply segment-based initial positioning to nodes
     */
    applySegmentPositioning(nodes) {
        if (!Array.isArray(nodes)) {
            console.warn('applySegmentPositioning: nodes is not an array:', nodes);
            return nodes;
        }
        
        const sourceNode = nodes.find(n => n.type === 'source');
        const centerX = this.width / 2;
        const centerY = this.height / 2;

        nodes.forEach(node => {
            if (node.type === 'source') {
                // Place source node in center
                node.x = centerX;
                node.y = centerY;
            } else {
                // Place other nodes based on segment
                const segmentPos = this.segmentPositions.get(node.segment);
                if (segmentPos) {
                    // Add some spread within segment area with less randomness
                    const offsetRadius = 40;
                    const nodeIndex = nodes.filter(n => n.segment === node.segment && n !== node).length;
                    const angle = segmentPos.angle + (nodeIndex * 0.3); // More predictable positioning
                    const radius = 20 + (nodeIndex * 15); // Radial spread
                    
                    node.x = segmentPos.x + radius * Math.cos(angle);
                    node.y = segmentPos.y + radius * Math.sin(angle);
                } else {
                    // Fallback to position around center
                    const angle = Math.random() * 2 * Math.PI;
                    const radius = 100;
                    node.x = centerX + radius * Math.cos(angle);
                    node.y = centerY + radius * Math.sin(angle);
                }
            }
        });

        return nodes;
    }

    /**
     * Create custom force for segment clustering
     */
    createSegmentForce(alpha = 0.1) {
        let nodes;
        const segmentPositions = this.segmentPositions;
        
        function force() {
            if (!nodes) return;
            
            for (let i = 0; i < nodes.length; i++) {
                const node = nodes[i];
                if (node.type !== 'source') {
                    const segmentPos = segmentPositions.get(node.segment);
                    if (segmentPos) {
                        const dx = segmentPos.x - node.x;
                        const dy = segmentPos.y - node.y;
                        node.vx += dx * alpha;
                        node.vy += dy * alpha;
                    }
                }
            }
        }
        
        force.initialize = function(_nodes) {
            nodes = _nodes;
        };
        
        return force;
    }

    /**
     * Get segment position
     */
    getSegmentPosition(segment) {
        return this.segmentPositions.get(segment);
    }

    /**
     * Get segment color
     */
    getSegmentColor(segment) {
        return this.segmentColors.get(segment) || '#95A5A6';
    }

    /**
     * Get all segments
     */
    getAllSegments() {
        return Array.from(this.segmentPositions.keys());
    }

    /**
     * Get segment statistics
     */
    getSegmentStats(nodes) {
        const stats = new Map();
        
        if (!Array.isArray(nodes)) {
            console.warn('getSegmentStats: nodes is not an array:', nodes);
            return {};
        }
        
        nodes.forEach(node => {
            const segment = node.segment;
            const current = stats.get(segment) || { total: 0, hasAsset: 0, types: new Set() };
            current.total++;
            if (node.hasAsset) current.hasAsset++;
            current.types.add(node.type);
            stats.set(segment, current);
        });

        return Object.fromEntries(stats);
    }

    /**
     * Create segment legend data
     */
    createLegendData(nodes) {
        if (!Array.isArray(nodes)) {
            console.warn('createLegendData: nodes is not an array:', nodes);
            return [];
        }
        
        const segmentStats = this.getSegmentStats(nodes);
        
        return this.getAllSegments().map(segment => ({
            segment: segment,
            color: this.getSegmentColor(segment),
            position: this.getSegmentPosition(segment),
            stats: segmentStats[segment] || { total: 0, hasAsset: 0, types: new Set() }
        }));
    }

    /**
     * Update dimensions
     */
    updateDimensions(width, height) {
        this.width = width;
        this.height = height;
    }

    /**
     * Get nodes in segment
     */
    getNodesInSegment(nodes, segment) {
        if (!Array.isArray(nodes)) {
            console.warn('getNodesInSegment: nodes is not an array:', nodes);
            return [];
        }
        return nodes.filter(node => node.segment === segment);
    }

    /**
     * Calculate segment boundaries for visualization
     */
    getSegmentBoundaries(nodes) {
        if (!Array.isArray(nodes)) {
            console.warn('getSegmentBoundaries: nodes is not an array:', nodes);
            return new Map();
        }
        
        const boundaries = new Map();
        
        this.getAllSegments().forEach(segment => {
            const segmentNodes = this.getNodesInSegment(nodes, segment);
            if (segmentNodes.length > 0) {
                const xs = segmentNodes.map(n => n.x);
                const ys = segmentNodes.map(n => n.y);
                
                boundaries.set(segment, {
                    minX: Math.min(...xs),
                    maxX: Math.max(...xs),
                    minY: Math.min(...ys),
                    maxY: Math.max(...ys),
                    centerX: xs.reduce((a, b) => a + b, 0) / xs.length,
                    centerY: ys.reduce((a, b) => a + b, 0) / ys.length
                });
            }
        });

        return boundaries;
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SegmentLayout;
}
