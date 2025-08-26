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
        
        // Get unique segments excluding the source segment
        const allSegments = [...new Set(nodes.map(d => d.segment))];
        const segments = allSegments.filter(s => s !== 'source');
        console.log('Unique segments found (excluding source):', segments);

        // Clear previous positions
        this.segmentPositions.clear();
        this.segmentColors.clear();

        // Add source position at center
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        this.segmentPositions.set('source', { x: centerX, y: centerY, angle: 0, index: -1 });
        this.segmentColors.set('source', '#E74C3C'); // Red color for source

        // Calculate positions for other segments in a circular layout
        const radius = Math.min(this.width, this.height) / 3; // Radius for segment centers

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
        
        const centerX = this.width / 2;
        const centerY = this.height / 2;

        nodes.forEach(node => {
            if (node.type === 'source' || node.segment === 'source') {
                // Place source node exactly in center
                node.x = centerX;
                node.y = centerY;
                // Pin the source node to prevent it from moving
                node.fx = centerX;
                node.fy = centerY;
                console.log(`Source node ${node.id} positioned at center: (${centerX}, ${centerY})`);
            } else {
                // Place other nodes based on segment
                const segmentPos = this.segmentPositions.get(node.segment);
                if (segmentPos) {
                    // Add some spread within segment area
                    const nodesInSegment = nodes.filter(n => n.segment === node.segment && n.type !== 'source');
                    const nodeIndex = nodesInSegment.findIndex(n => n.id === node.id);
                    const totalInSegment = nodesInSegment.length;
                    
                    if (totalInSegment === 1) {
                        // Single node - place at segment center
                        node.x = segmentPos.x;
                        node.y = segmentPos.y;
                    } else {
                        // Multiple nodes - create a fan pattern
                        const fanAngle = Math.PI / 4; // 45 degrees fan
                        const startAngle = segmentPos.angle - fanAngle / 2;
                        const angleStep = totalInSegment > 1 ? fanAngle / (totalInSegment - 1) : 0;
                        const nodeAngle = startAngle + (nodeIndex * angleStep);
                        
                        // Variable distance based on node index
                        const baseRadius = 80;
                        const radiusVariation = 40;
                        const radius = baseRadius + ((nodeIndex % 3) * radiusVariation / 2);
                        
                        node.x = segmentPos.x + radius * Math.cos(nodeAngle);
                        node.y = segmentPos.y + radius * Math.sin(nodeAngle);
                    }
                    console.log(`Node ${node.id} positioned in segment ${node.segment}: (${node.x.toFixed(1)}, ${node.y.toFixed(1)})`);
                } else {
                    // Fallback to position around center
                    const angle = Math.random() * 2 * Math.PI;
                    const radius = 200;
                    node.x = centerX + radius * Math.cos(angle);
                    node.y = centerY + radius * Math.sin(angle);
                    console.log(`Node ${node.id} fallback positioned: (${node.x.toFixed(1)}, ${node.y.toFixed(1)})`);
                }
            }
        });

        return nodes;
    }

    /**
     * Create custom force for segment clustering
     */
    createSegmentForce(alpha = 0.05) {
        let nodes;
        const segmentPositions = this.segmentPositions;
        
        function force() {
            if (!nodes) return;
            
            for (let i = 0; i < nodes.length; i++) {
                const node = nodes[i];
                // Never apply segment force to source nodes - they should stay pinned
                if (node.type !== 'source' && node.segment !== 'source' && !node.fx && !node.fy) {
                    const segmentPos = segmentPositions.get(node.segment);
                    if (segmentPos) {
                        const dx = segmentPos.x - node.x;
                        const dy = segmentPos.y - node.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        
                        // Apply weaker force when closer to segment center
                        const strength = Math.min(alpha, alpha * (distance / 200));
                        node.vx += dx * strength;
                        node.vy += dy * strength;
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
