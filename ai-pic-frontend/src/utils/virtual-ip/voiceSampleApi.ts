import { httpClient, type HttpResponse } from '@/utils/api/client'

export interface VirtualIPVoiceSampleResult {
  sample_url: string
  sample_source_url: string
  voice_config: Record<string, unknown>
}

interface SaveVirtualIPVoiceSampleArgs {
  businessId?: string
  virtualIpId?: number
  sourceUrl: string
  previewText?: string
}

export async function saveVirtualIPVoiceSample({
  businessId,
  virtualIpId,
  sourceUrl,
  previewText,
}: SaveVirtualIPVoiceSampleArgs): Promise<HttpResponse<VirtualIPVoiceSampleResult>> {
  if (!businessId && !virtualIpId) {
    return { success: false, error: '缺少虚拟IP标识' }
  }

  const endpoint = businessId
    ? `/api/v1/virtual-ips/business/${businessId}/voice-sample`
    : `/api/v1/virtual-ips/${virtualIpId}/voice-sample`

  return httpClient<VirtualIPVoiceSampleResult>(endpoint, {
    method: 'POST',
    body: JSON.stringify({
      source_url: sourceUrl,
      preview_text: previewText,
    }),
  })
}
