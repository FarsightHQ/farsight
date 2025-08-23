// Simple FAR Network Visualization
class FARNetworkViz {
    constructor() {
        this.width = 1360;
        this.height = 700;
        this.nodes = [];
        this.links = [];
    }

    async loadNetworkData(ipAddress) {
        console.log(`Loading data for IP: ${ipAddress}`);
        
        try {
            // Get firewall rules for the IP
            const response = await fetch(`http://localhost:8000/api/v1/ip/${ipAddress}/rules`);
            const data = await response.json();
            
            console.log('API Response:', data);
            
            // Clear previous data
            this.nodes = [];
            this.links = [];
            
            // Add the source IP as center node
            this.nodes.push({
                id: ipAddress,
                label: ipAddress,
                type: 'source'
            });
            
            // Process relationships if they exist
            if (data.relationships && data.relationships.length > 0) {
                const addedIPs = new Set([ipAddress]);
                
                data.relationships.forEach(rel => {
                    const sourceIP = rel.source_ip ? rel.source_ip.replace(/\/\d+$/, '') : null;
                    const destIP = rel.destination_ip ? rel.destination_ip.replace(/\/\d+$/, '') : null;
                    
                    // Add source IP if not already added
                    if (sourceIP && !addedIPs.has(sourceIP)) {
                        this.nodes.push({
                            id: sourceIP,
                            label: sourceIP,
                            type: 'connected'
                        });
                        addedIPs.add(sourceIP);
                    }
                    
                    // Add destination IP if not already added
                    if (destIP && !addedIPs.has(destIP)) {
                        this.nodes.push({
                            id: destIP,
                            label: destIP,
                            type: 'connected'
                        });
                        addedIPs.add(destIP);
                    }
                    
                    // Add link if both IPs exist and are different
                    if (sourceIP && destIP && sourceIP !== destIP) {
                        this.links.push({
                            source: sourceIP,
                            target: destIP,
                            protocol: rel.protocol || 'ANY',
                            port: rel.ports || 'ANY'
                        });
                    }
                });
            }
            
            console.log('Nodes:', this.nodes);
            console.log('Links:', this.links);
            
        } catch (error) {
            console.error('Error loading data:', error);
            // Show just the single IP if there's an error
            this.nodes = [{
                id: ipAddress,
                label: ipAddress,
                type: 'source'
            }];
            this.links = [];
        }
    }

    render() {
        // Clear previous visualization
        d3.select('#networkSvg').selectAll('*').remove();
        
        // Create SVG
        const svg = d3.select('#networkSvg');
        
        // Create simulation
        const simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2));
        
        // Create links
        const link = svg.append('g')
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', '#999')
            .attr('stroke-width', 2);
        
        // Create nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(this.nodes)
            .join('circle')
            .attr('r', d => d.type === 'source' ? 15 : 10)
            .attr('fill', d => d.type === 'source' ? '#ff6b6b' : '#4ecdc4')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);
        
        // Add labels
        const label = svg.append('g')
            .selectAll('text')
            .data(this.nodes)
            .join('text')
            .text(d => d.label)
            .attr('x', 12)
            .attr('y', 3)
            .style('font-size', '12px')
            .style('fill', '#333');
        
        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            label
                .attr('x', d => d.x + 12)
                .attr('y', d => d.y + 3);
        });
    }

    clear() {
        d3.select('#networkSvg').selectAll('*').remove();
        this.nodes = [];
        this.links = [];
    }
}

// Initialize
const viz = new FARNetworkViz();

// Functions called by HTML buttons
async function loadVisualization() {
    const ip = document.getElementById('ipInput').value.trim();
    
    if (!ip) {
        alert('Please enter an IP address');
        return;
    }
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    
    try {
        await viz.loadNetworkData(ip);
        viz.render();
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('error').textContent = 'Error loading network data';
        document.getElementById('error').style.display = 'block';
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function clearVisualization() {
    viz.clear();
    document.getElementById('ipInput').value = '';
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}
