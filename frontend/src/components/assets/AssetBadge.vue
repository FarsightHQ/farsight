<template>
  <span
    v-if="asset"
    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-info-100 text-info-800 cursor-pointer hover:bg-info-200"
    :title="`Asset: ${asset.hostname || asset.ip_address} (${asset.segment || 'N/A'})`"
    @click.stop="handleClick"
  >
    <ServerIcon class="h-3 w-3 mr-1" />
    {{ asset.hostname || asset.ip_address }}
  </span>
  <span
    v-else-if="ipAddress && showUnknown"
    class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600"
    title="Not in asset registry"
  >
    {{ extractIp(ipAddress) }}
  </span>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ServerIcon } from '@heroicons/vue/24/outline'
import { assetsService } from '@/services/assets'

const props = defineProps({
  ipAddress: {
    type: String,
    default: '',
  },
  showUnknown: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const asset = ref(null)
const loading = ref(false)

const extractIp = cidr => {
  if (!cidr) return ''
  return cidr.split('/')[0]
}

const fetchAsset = async () => {
  if (!props.ipAddress) return

  try {
    loading.value = true
    const ip = extractIp(props.ipAddress)
    const response = await assetsService.getAssetByIp(ip)
    asset.value = response.data || response
  } catch (err) {
    // Asset not found - this is expected for many IPs
    asset.value = null
  } finally {
    loading.value = false
  }
}

const handleClick = () => {
  if (asset.value) {
    router.push(`/assets/${encodeURIComponent(asset.value.ip_address)}`)
  }
}

onMounted(() => {
  if (props.ipAddress) {
    fetchAsset()
  }
})
</script>
