// Simple FAR Network Visualization

// Check if D3 is loaded
if (typeof d3 === 'undefined') {
    console.error('D3.js is not loaded! Please check your internet connection.');
    alert('D3.js library failed to load. Please check your internet connection and refresh the page.');
}

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
                const ipTypes = new Map(); // Track IP types
                
                data.relationships.forEach(rel => {
                    const sourceIP = rel.source_ip ? rel.source_ip.replace(/\/\d+$/, '') : null;
                    const destIP = rel.destination_ip ? rel.destination_ip.replace(/\/\d+$/, '') : null;
                    
                    // Determine the relationship type based on our target IP
                    if (sourceIP === ipAddress && destIP && destIP !== ipAddress) {
                        // Our IP is source -> this is an outgoing connection
                        if (!addedIPs.has(destIP)) {
                            ipTypes.set(destIP, 'outgoing');
                            addedIPs.add(destIP);
                        }
                    } else if (destIP === ipAddress && sourceIP && sourceIP !== ipAddress) {
                        // Our IP is destination -> this is an incoming connection
                        if (!addedIPs.has(sourceIP)) {
                            ipTypes.set(sourceIP, 'incoming');
                            addedIPs.add(sourceIP);
                        }
                    } else {
                        // Add any other IPs as related
                        if (sourceIP && sourceIP !== ipAddress && !addedIPs.has(sourceIP)) {
                            ipTypes.set(sourceIP, 'related');
                            addedIPs.add(sourceIP);
                        }
                        if (destIP && destIP !== ipAddress && !addedIPs.has(destIP)) {
                            ipTypes.set(destIP, 'related');
                            addedIPs.add(destIP);
                        }
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
                
                // Fetch asset registry data for all IPs to get segment information
                const ipArray = Array.from(ipTypes.keys());
                ipArray.push(ipAddress); // Include source IP
                
                console.log('Fetching asset data for IPs:', ipArray);
                
                const assetPromises = ipArray.map(async ip => {
                    try {
                        const response = await fetch(`http://localhost:8000/api/v1/assets/${ip}`);
                        if (response.ok) {
                            const asset = await response.json();
                            return { ip, asset, hasAsset: true };
                        }
                    } catch (error) {
                        console.log(`No asset data for ${ip}`);
                    }
                    return { ip, asset: null, hasAsset: false };
                });
                
                const assetResults = await Promise.all(assetPromises);
                console.log('Asset results:', assetResults);
                
                // Create a map of IP to asset data
                const assetMap = new Map();
                assetResults.forEach(({ ip, asset, hasAsset }) => {
                    assetMap.set(ip, { asset, hasAsset });
                });
                
                // Add source IP node with asset data
                const sourceAssetData = assetMap.get(ipAddress);
                this.nodes.push({
                    id: ipAddress,
                    label: ipAddress,
                    type: 'source',
                    asset: sourceAssetData?.asset,
                    hasAsset: sourceAssetData?.hasAsset || false,
                    segment: sourceAssetData?.asset?.segment || 'Unknown'
                });
                
                // Add all the processed IPs as nodes with their determined types and asset data
                ipTypes.forEach((type, ip) => {
                    const assetData = assetMap.get(ip);
                    this.nodes.push({
                        id: ip,
                        label: ip,
                        type: type,
                        asset: assetData?.asset,
                        hasAsset: assetData?.hasAsset || false,
                        segment: assetData?.asset?.segment || 'Unknown'
                    });
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
        
        // Group nodes by segment for positioning
        const segments = [...new Set(this.nodes.map(d => d.segment))];
        const segmentColors = this.getSegmentColors(segments);
        
        console.log('Segments found:', segments);
        
        // Create segment-based positioning
        const segmentPositions = this.calculateSegmentPositions(segments);
        
        // Create simulation with segment-based forces
        const simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('segment', d3.forceRadial(d => {
                if (d.type === 'source') return 0; // Keep source at center
                const segmentPos = segmentPositions[d.segment];
                return segmentPos ? segmentPos.radius : 200;
            }, this.width / 2, this.height / 2).strength(0.1))
            .force('segmentX', d3.forceX(d => {
                if (d.type === 'source') return this.width / 2;
                const segmentPos = segmentPositions[d.segment];
                return segmentPos ? segmentPos.x : this.width / 2;
            }).strength(0.3))
            .force('segmentY', d3.forceY(d => {
                if (d.type === 'source') return this.height / 2;
                const segmentPos = segmentPositions[d.segment];
                return segmentPos ? segmentPos.y : this.height / 2;
            }).strength(0.3));
        
        // Create segment groups (background circles)
        const segmentGroup = svg.append('g').attr('class', 'segments');
        Object.entries(segmentPositions).forEach(([segment, pos]) => {
            if (segment !== 'Unknown') {
                segmentGroup.append('circle')
                    .attr('cx', pos.x)
                    .attr('cy', pos.y)
                    .attr('r', pos.radius + 20)
                    .attr('fill', segmentColors[segment])
                    .attr('fill-opacity', 0.1)
                    .attr('stroke', segmentColors[segment])
                    .attr('stroke-width', 2)
                    .attr('stroke-dasharray', '5,5');
                
                segmentGroup.append('text')
                    .attr('x', pos.x)
                    .attr('y', pos.y - pos.radius - 30)
                    .attr('text-anchor', 'middle')
                    .style('font-size', '14px')
                    .style('font-weight', 'bold')
                    .style('fill', segmentColors[segment])
                    .text(segment);
            }
        });
        
        // Create links
        const link = svg.append('g')
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', '#999')
            .attr('stroke-width', 2);
        
        // Create nodes with segment-aware coloring
        const node = svg.append('g')
            .selectAll('circle')
            .data(this.nodes)
            .join('circle')
            .attr('r', d => d.type === 'source' ? 15 : 10)
            .attr('fill', d => {
                if (d.type === 'source') return '#ff6b6b'; // Always red for source
                
                // Use segment color with type-based brightness
                const segmentColor = segmentColors[d.segment] || '#95a5a6';
                return this.adjustColorForType(segmentColor, d.type);
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .on('mouseover', (event, d) => this.showNodeInfo(event, d))
            .on('mouseout', () => this.hideNodeInfo());
        
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

    getSegmentColors(segments) {
        const colors = [
            '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', 
            '#1abc9c', '#e67e22', '#34495e', '#e91e63', '#00bcd4'
        ];
        const segmentColors = {};
        segments.forEach((segment, index) => {
            segmentColors[segment] = colors[index % colors.length];
        });
        return segmentColors;
    }

    calculateSegmentPositions(segments) {
        const positions = {};
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const baseRadius = 200;
        
        segments.forEach((segment, index) => {
            if (segment === 'Unknown') {
                positions[segment] = { x: centerX, y: centerY, radius: 100 };
            } else {
                const angle = (index * 2 * Math.PI) / (segments.length - 1); // -1 to exclude 'Unknown'
                const x = centerX + Math.cos(angle) * baseRadius;
                const y = centerY + Math.sin(angle) * baseRadius;
                positions[segment] = { x, y, radius: 80 };
            }
        });
        
        return positions;
    }

    adjustColorForType(baseColor, type) {
        const color = d3.color(baseColor);
        if (!color) return baseColor;
        
        switch(type) {
            case 'outgoing':
                return color.darker(0.5).toString(); // Darker for outgoing
            case 'incoming':
                return color.brighter(0.5).toString(); // Brighter for incoming
            case 'related':
                return color.toString(); // Normal for related
            default:
                return color.toString();
        }
    }

    showNodeInfo(event, node) {
        // Enhanced node info showing segment information
        const info = d3.select('#nodeInfo') || d3.select('body').append('div').attr('id', 'nodeInfo');
        
        let content = `<strong>IP:</strong> ${node.ip}<br>`;
        content += `<strong>Segment:</strong> ${node.segment}<br>`;
        content += `<strong>Type:</strong> ${node.type}<br>`;
        
        if (node.hasAsset && node.asset) {
            content += `<strong>Hostname:</strong> ${node.asset.hostname || 'N/A'}<br>`;
            content += `<strong>OS:</strong> ${node.asset.operating_system || 'N/A'}<br>`;
            content += `<strong>Environment:</strong> ${node.asset.environment || 'N/A'}<br>`;
            content += `<strong>VLAN:</strong> ${node.asset.vlan || 'N/A'}<br>`;
            content += `<strong>Location:</strong> ${node.asset.location || 'N/A'}<br>`;
        } else {
            content += `<strong>Asset Info:</strong> Not in registry<br>`;
        }
        
        info.html(content)
            .style('display', 'block')
            .style('position', 'absolute')
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px')
            .style('background', 'white')
            .style('border', '1px solid #ccc')
            .style('padding', '10px')
            .style('border-radius', '5px')
            .style('box-shadow', '0 2px 5px rgba(0,0,0,0.2)')
            .style('font-size', '12px')
            .style('z-index', '1000');
    }

    hideNodeInfo() {
        d3.select('#nodeInfo').style('display', 'none');
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
