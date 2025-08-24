/**
 * NetworkLoader - Handles API calls and data fetching
 */
class NetworkLoader {
    constructor(apiBase = 'http://localhost:8000/api/v1') {
        this.apiBase = apiBase;
    }

    /**
     * Fetch firewall rules for an IP address
     */
    async fetchFirewallRules(ipAddress) {
        try {
            const response = await fetch(`${this.apiBase}/ip/${ipAddress}/rules`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            console.log('Firewall rules data:', data);
            return data;
        } catch (error) {
            console.error('Error fetching firewall rules:', error);
            throw error;
        }
    }

    /**
     * Fetch asset registry data for an IP address
     */
    async fetchAssetData(ipAddress) {
        try {
            const response = await fetch(`${this.apiBase}/assets/${ipAddress}`);
            if (response.ok) {
                const asset = await response.json();
                return { ip: ipAddress, asset, hasAsset: true };
            }
        } catch (error) {
            console.log(`No asset data for ${ipAddress}`);
        }
        return { ip: ipAddress, asset: null, hasAsset: false };
    }

    /**
     * Fetch asset data for multiple IP addresses
     */
    async fetchMultipleAssets(ipAddresses) {
        console.log('Fetching asset data for IPs:', ipAddresses);
        
        const assetPromises = ipAddresses.map(ip => this.fetchAssetData(ip));
        const results = await Promise.all(assetPromises);
        
        console.log('Asset results:', results);
        return results;
    }

    /**
     * Create a map of IP to asset data for quick lookup
     */
    createAssetMap(assetResults) {
        const assetMap = new Map();
        assetResults.forEach(({ ip, asset, hasAsset }) => {
            assetMap.set(ip, { asset, hasAsset });
        });
        return assetMap;
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NetworkLoader;
}
