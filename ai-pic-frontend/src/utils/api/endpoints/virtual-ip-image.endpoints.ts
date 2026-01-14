/**
 * Virtual IP Image Management API endpoints.
 */

export * from './virtual-ip-image/crud.endpoints';
export * from './virtual-ip-image/generation.endpoints';
export * from './virtual-ip-image/variants.endpoints';

import {
  deleteVirtualIPImage,
  getVirtualIPImage,
  getVirtualIPImageCategories,
  getVirtualIPImages,
  setDefaultVirtualIPImage,
  updateVirtualIPImage,
  uploadVirtualIPImage,
} from './virtual-ip-image/crud.endpoints';
import {
  generateVirtualIPImage,
  generateVirtualIPImageAsync,
} from './virtual-ip-image/generation.endpoints';
import {
  generateVariantAndSave,
  generateVariantAndSaveAsync,
  generateVariantFromImage,
} from './virtual-ip-image/variants.endpoints';

/**
 * Virtual IP Image API namespace.
 */
export const virtualIPImageAPI = {
  getImages: (virtualIPId: number, category?: string) =>
    getVirtualIPImages(virtualIPId, { category }),
  getImage: getVirtualIPImage,
  uploadImage: (
    virtualIPId: number,
    file: File,
    category: string = 'portrait',
    tags: string = '',
    isDefault: boolean = false
  ) => {
    const normalizedTags = tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
      .join(',');
    return uploadVirtualIPImage(virtualIPId, file, {
      category,
      tags: normalizedTags,
      is_default: isDefault,
    });
  },
  generateImage: generateVirtualIPImage,
  generateImageAsync: generateVirtualIPImageAsync,
  generateVariantFromImage,
  generateVariantAndSave,
  generateVariantAndSaveAsync,
  updateImage: updateVirtualIPImage,
  deleteImage: deleteVirtualIPImage,
  setDefaultImage: setDefaultVirtualIPImage,
  getCategories: getVirtualIPImageCategories,
};
