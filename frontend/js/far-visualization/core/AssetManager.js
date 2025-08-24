/**
 * AssetManager - Manages asset data and provides metadata operations
 */
class AssetManager {
    constructor() {
        this.assetMap = new Map();
        this.segmentStats = new Map();
    }

    /**
     * Process asset data and create asset maps
     */
    processAssetData(assetData) {
        this.assetMap.clear();
        this.segmentStats.clear();

        if (!assetData || !Array.isArray(assetData)) {
            console.log('No asset data provided');
            return;
        }

        console.log(`Processing ${assetData.length} asset records`);
        
        assetData.forEach(asset => {
            if (asset.ip_address) {
                const cleanIP = this.cleanAssetIP(asset.ip_address);
                this.assetMap.set(cleanIP, {
                    asset: asset,
                    hasAsset: true
                });

                // Update segment stats
                const segment = asset.segment || 'Unknown';
                this.segmentStats.set(segment, (this.segmentStats.get(segment) || 0) + 1);
            }
        });

        console.log(`Asset map created with ${this.assetMap.size} entries`);
        console.log('Segment distribution:', Object.fromEntries(this.segmentStats));
    }

    /**
     * Clean asset IP address
     */
    cleanAssetIP(ip) {
        return ip ? ip.replace(/\/\d+$/, '') : null;
    }

    /**
     * Get asset data for an IP
     */
    getAssetData(ip) {
        return this.assetMap.get(ip) || { asset: null, hasAsset: false };
    }

    /**
     * Get all assets
     */
    getAllAssets() {
        return Array.from(this.assetMap.values()).map(entry => entry.asset);
    }

    /**
     * Get assets by segment
     */
    getAssetsBySegment(segment) {
        return Array.from(this.assetMap.values())
            .filter(entry => entry.asset && entry.asset.segment === segment)
            .map(entry => entry.asset);
    }

    /**
     * Get unique segments
     */
    getUniqueSegments() {
        return Array.from(this.segmentStats.keys()).sort();
    }

    /**
     * Get segment statistics
     */
    getSegmentStats() {
        return Object.fromEntries(this.segmentStats);
    }

    /**
     * Check if IP has asset data
     */
    hasAssetData(ip) {
        const assetData = this.assetMap.get(ip);
        return assetData && assetData.hasAsset;
    }

    /**
     * Get asset metadata for tooltip
     */
    getAssetTooltipData(ip) {
        const assetData = this.getAssetData(ip);
        
        if (!assetData.hasAsset) {
            return {
                hasAsset: false,
                content: `IP: ${ip}<br>Asset: No asset data available`
            };
        }

        const asset = assetData.asset;
        const tooltipContent = [
            `IP: ${ip}`,
            `Hostname: ${asset.hostname || 'N/A'}`,
            `OS: ${asset.os_name || 'N/A'} ${asset.os_version || ''}`,
            `Segment: ${asset.segment || 'Unknown'}`,
            `Environment: ${asset.environment || 'N/A'}`,
            `Owner: ${asset.owner || 'N/A'}`,
            `Location: ${asset.location || 'N/A'}`,
            `Status: ${asset.status || 'N/A'}`
        ].filter(line => line && !line.includes('N/A N/A'));

        return {
            hasAsset: true,
            content: tooltipContent.join('<br>'),
            asset: asset
        };
    }

    /**
     * Get asset summary for info panel
     */
    getAssetSummary(ip) {
        const assetData = this.getAssetData(ip);
        
        if (!assetData.hasAsset) {
            return null;
        }

        const asset = assetData.asset;
        return {
            ip: ip,
            hostname: asset.hostname,
            os: `${asset.os_name || 'Unknown'} ${asset.os_version || ''}`.trim(),
            segment: asset.segment || 'Unknown',
            environment: asset.environment,
            owner: asset.owner,
            location: asset.location,
            status: asset.status,
            gateway: asset.gateway,
            subnet_mask: asset.subnet_mask,
            memory: asset.memory,
            cpu: asset.cpu,
            storage: asset.storage,
            created_at: asset.created_at,
            updated_at: asset.updated_at
        };
    }

    /**
     * Clear all asset data
     */
    clear() {
        this.assetMap.clear();
        this.segmentStats.clear();
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AssetManager;
}
