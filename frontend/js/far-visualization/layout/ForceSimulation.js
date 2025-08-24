/**
 * ForceSimulation - Handles D3 force simulation setup and management
 */
class ForceSimulation {
    constructor(width, height, segmentLayout) {
        this.width = width;
        this.height = height;
        this.segmentLayout = segmentLayout;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
    }

    /**
     * Initialize the force simulation
     */
    init() {
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(120).strength(0.2))
            .force('charge', d3.forceManyBody().strength(-100))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2).strength(0.03))
            .force('collision', d3.forceCollide().radius(25))
            .force('x', d3.forceX(this.width / 2).strength(0.02))
            .force('y', d3.forceY(this.height / 2).strength(0.02));

        // Add segment clustering force if segment layout is available
        if (this.segmentLayout) {
            this.simulation.force('segment', this.segmentLayout.createSegmentForce(0.3));
        }

        return this.simulation;
    }

    /**
     * Update simulation with new data
     */
    update(nodes, links) {
        this.nodes = nodes;
        this.links = links;

        if (!this.simulation) {
            this.init();
        }

        // Apply segment positioning to nodes
        if (this.segmentLayout) {
            this.segmentLayout.calculateSegmentPositions(nodes);
            this.segmentLayout.applySegmentPositioning(nodes);
        }

        // Update simulation
        this.simulation
            .nodes(nodes)
            .force('link').links(links);

        return this.simulation;
    }

    /**
     * Start simulation
     */
    start() {
        if (this.simulation) {
            this.simulation.alpha(1).restart();
        }
    }

    /**
     * Stop simulation
     */
    stop() {
        if (this.simulation) {
            this.simulation.stop();
        }
    }

    /**
     * Set tick handler
     */
    onTick(callback) {
        if (this.simulation) {
            this.simulation.on('tick', callback);
        }
    }

    /**
     * Set end handler
     */
    onEnd(callback) {
        if (this.simulation) {
            this.simulation.on('end', callback);
        }
    }

    /**
     * Get current alpha (simulation energy)
     */
    getAlpha() {
        return this.simulation ? this.simulation.alpha() : 0;
    }

    /**
     * Set alpha
     */
    setAlpha(alpha) {
        if (this.simulation) {
            this.simulation.alpha(alpha);
        }
    }

    /**
     * Restart simulation with new alpha
     */
    restart(alpha = 1) {
        if (this.simulation) {
            this.simulation.alpha(alpha).restart();
        }
    }

    /**
     * Update force strengths
     */
    updateForces(options = {}) {
        if (!this.simulation) return;

        const {
            linkDistance = 100,
            linkStrength = 0.3,
            chargeStrength = -200,
            collisionRadius = 20,
            centerStrength = 0.05,
            segmentStrength = 0.1
        } = options;

        this.simulation
            .force('link')
            .distance(linkDistance)
            .strength(linkStrength);

        this.simulation
            .force('charge')
            .strength(chargeStrength);

        this.simulation
            .force('collision')
            .radius(collisionRadius);

        this.simulation
            .force('x')
            .strength(centerStrength);

        this.simulation
            .force('y')
            .strength(centerStrength);

        // Update segment force if available
        if (this.segmentLayout) {
            this.simulation.force('segment', this.segmentLayout.createSegmentForce(segmentStrength));
        }
    }

    /**
     * Add custom force
     */
    addForce(name, force) {
        if (this.simulation) {
            this.simulation.force(name, force);
        }
    }

    /**
     * Remove force
     */
    removeForce(name) {
        if (this.simulation) {
            this.simulation.force(name, null);
        }
    }

    /**
     * Pin node at position
     */
    pinNode(node, x, y) {
        node.fx = x;
        node.fy = y;
        if (this.simulation) {
            this.simulation.alpha(0.3).restart();
        }
    }

    /**
     * Unpin node
     */
    unpinNode(node) {
        node.fx = null;
        node.fy = null;
        if (this.simulation) {
            this.simulation.alpha(0.3).restart();
        }
    }

    /**
     * Get simulation statistics
     */
    getStats() {
        if (!this.simulation) return null;

        return {
            alpha: this.simulation.alpha(),
            alphaMin: this.simulation.alphaMin(),
            alphaDecay: this.simulation.alphaDecay(),
            alphaTarget: this.simulation.alphaTarget(),
            nodeCount: this.nodes.length,
            linkCount: this.links.length
        };
    }

    /**
     * Update dimensions
     */
    updateDimensions(width, height) {
        this.width = width;
        this.height = height;
        
        if (this.segmentLayout) {
            this.segmentLayout.updateDimensions(width, height);
        }

        if (this.simulation) {
            this.simulation
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('x', d3.forceX(width / 2))
                .force('y', d3.forceY(height / 2));
        }
    }

    /**
     * Destroy simulation
     */
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
            this.simulation = null;
        }
        this.nodes = [];
        this.links = [];
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ForceSimulation;
}
