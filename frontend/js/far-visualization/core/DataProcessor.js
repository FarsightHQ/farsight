/**
 * DataProcessor - Processes firewall rules and relationship data
 */
class DataProcessor {
    /**
     * Process firewall relationships to extract unique IPs and connection types
     */
    processFirewallRelationships(rulesData, sourceIpAddress) {
        const uniqueIPs = new Set([sourceIpAddress]);
        const ipTypes = new Map();
        const ruleRelationships = [];

        if (!rulesData.relationships || rulesData.relationships.length === 0) {
            console.log('No relationships found in rules data');
            return { uniqueIPs, ipTypes, ruleRelationships };
        }

        console.log(`Processing ${rulesData.relationships.length} firewall relationships`);

        rulesData.relationships.forEach(relationship => {
            const sourceIP = this.cleanIP(relationship.source_ip);
            const destIP = this.cleanIP(relationship.destination_ip);

            // Add IPs to unique set
            if (sourceIP && this.isValidIP(sourceIP)) {
                uniqueIPs.add(sourceIP);
            }
            if (destIP && this.isValidIP(destIP)) {
                uniqueIPs.add(destIP);
            }

            // Determine relationship type
            this.categorizeRelationship(sourceIP, destIP, sourceIpAddress, ipTypes);

            // Create rule relationship
            if (sourceIP && destIP && sourceIP !== destIP) {
                ruleRelationships.push({
                    source: sourceIP,
                    target: destIP,
                    type: this.getRelationshipType(sourceIP, destIP, sourceIpAddress),
                    rule: relationship,
                    direction: this.getDirection(sourceIP, destIP, sourceIpAddress),
                    label: `${relationship.protocol || 'ANY'}:${relationship.ports || 'ANY'}`
                });
            }
        });

        return { uniqueIPs, ipTypes, ruleRelationships };
    }

    /**
     * Clean IP address by removing CIDR notation
     */
    cleanIP(ip) {
        return ip ? ip.replace(/\/\d+$/, '') : null;
    }

    /**
     * Check if IP is valid (not 'any', 'ANY', etc.)
     */
    isValidIP(ip) {
        return ip && ip !== 'any' && ip !== 'ANY';
    }

    /**
     * Categorize relationship based on source IP role
     */
    categorizeRelationship(sourceIP, destIP, targetIP, ipTypes) {
        if (sourceIP === targetIP && destIP && destIP !== targetIP) {
            // Our IP is source -> outgoing connection
            if (!ipTypes.has(destIP)) {
                ipTypes.set(destIP, 'outgoing');
            }
        } else if (destIP === targetIP && sourceIP && sourceIP !== targetIP) {
            // Our IP is destination -> incoming connection
            if (!ipTypes.has(sourceIP)) {
                ipTypes.set(sourceIP, 'incoming');
            }
        } else {
            // Add any other IPs as related
            if (sourceIP && sourceIP !== targetIP && !ipTypes.has(sourceIP)) {
                ipTypes.set(sourceIP, 'related');
            }
            if (destIP && destIP !== targetIP && !ipTypes.has(destIP)) {
                ipTypes.set(destIP, 'related');
            }
        }
    }

    /**
     * Get relationship type for visualization
     */
    getRelationshipType(sourceIP, destIP, targetIP) {
        if (sourceIP === targetIP) return 'outbound';
        if (destIP === targetIP) return 'inbound';
        return 'related';
    }

    /**
     * Get direction for link
     */
    getDirection(sourceIP, destIP, targetIP) {
        if (sourceIP === targetIP) return 'outbound';
        if (destIP === targetIP) return 'inbound';
        return 'related';
    }

    /**
     * Create nodes from processed data
     */
    createNodes(sourceIpAddress, ipTypes, assetMap) {
        const nodes = [];

        // Add source IP node - always assign it to "source" segment
        const sourceAssetData = assetMap.get(sourceIpAddress);
        nodes.push({
            id: sourceIpAddress,
            label: sourceIpAddress,
            type: 'source',
            asset: sourceAssetData?.asset,
            hasAsset: sourceAssetData?.hasAsset || false,
            segment: 'source' // Always use 'source' segment for the main IP
        });

        // Add other IP nodes
        ipTypes.forEach((type, ip) => {
            const assetData = assetMap.get(ip);
            nodes.push({
                id: ip,
                label: ip,
                type: type,
                asset: assetData?.asset,
                hasAsset: assetData?.hasAsset || false,
                segment: assetData?.asset?.segment || type // Use type as fallback segment
            });
        });

        return nodes;
    }

    /**
     * Create links from rule relationships
     */
    createLinks(ruleRelationships) {
        return ruleRelationships.map(rel => ({
            source: rel.source,
            target: rel.target,
            type: rel.type,
            direction: rel.direction,
            rule: rel.rule,
            label: rel.label
        }));
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataProcessor;
}
