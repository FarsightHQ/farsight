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
        // Get unique segments
        const segments = [...new Set(nodes.map(d => d.segment))];
        console.log('Unique segments found:', segments);

        // Clear previous positions
        this.segmentPositions.clear();
        this.segmentColors.clear();

        // Calculate positions for segments in a circular layout
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const radius = Math.min(this.width, this.height) / 3;

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
                    // Add some randomness within segment area
                    const offsetRadius = 50;
                    const randomAngle = Math.random() * 2 * Math.PI;
                    const randomRadius = Math.random() * offsetRadius;
                    
                    node.x = segmentPos.x + randomRadius * Math.cos(randomAngle);
                    node.y = segmentPos.y + randomRadius * Math.sin(randomAngle);
                } else {
                    // Fallback to random position
                    node.x = Math.random() * this.width;
                    node.y = Math.random() * this.height;
                }
            }
        });

        return nodes;
    }

    /**
     * Create custom force for segment clustering
     */
    createSegmentForce(alpha = 0.1) {
        return (nodes) => {
            nodes.forEach(node => {
                if (node.type !== 'source') {
                    const segmentPos = this.segmentPositions.get(node.segment);
                    if (segmentPos) {
                        const dx = segmentPos.x - node.x;
                        const dy = segmentPos.y - node.y;
                        node.vx += dx * alpha;
                        node.vy += dy * alpha;
                    }
                }
            });
        };
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
        return nodes.filter(node => node.segment === segment);
    }

    /**
     * Calculate segment boundaries for visualization
     */
    getSegmentBoundaries(nodes) {
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
