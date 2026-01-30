/**
 * PenguinTech License Server JavaScript Client
 *
 * Provides a JS client for integrating with the PenguinTech License Server
 * to validate licenses and check feature entitlements.
 */

import axios from 'axios';

const DEFAULT_BASE_URL = 'https://license.penguintech.io';
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

class PenguinTechLicenseClient {
  constructor(licenseKey, product, baseUrl = null, timeout = 30000) {
    this.licenseKey = licenseKey;
    this.product = product;
    this.baseUrl = baseUrl || DEFAULT_BASE_URL;
    this.serverId = null;

    this.http = axios.create({
      baseURL: this.baseUrl,
      timeout,
      headers: {
        Authorization: `Bearer ${licenseKey}`,
        'Content-Type': 'application/json',
      },
    });

    // Feature cache
    this._featureCache = {};
    this._cacheTimestamp = null;
  }

  async validate() {
    const response = await this.http.post('/api/v2/validate', {
      product: this.product,
    });

    const data = response.data;

    if (!data.valid) {
      throw new Error(`License validation failed: ${data.message}`);
    }

    if (data.metadata && data.metadata.server_id) {
      this.serverId = data.metadata.server_id;
    }

    this._updateFeatureCache(data.features || []);

    return data;
  }

  async checkFeature(feature, useCache = true) {
    if (useCache && this._isCacheValid()) {
      const cached = this._featureCache[feature];
      if (cached !== undefined) {
        return cached;
      }
    }

    try {
      const response = await this.http.post('/api/v2/features', {
        product: this.product,
        feature,
      });

      const features = response.data.features || [];

      if (features.length > 0) {
        const entitled = features[0].entitled || false;
        this._featureCache[feature] = entitled;
        this._cacheTimestamp = Date.now();
        return entitled;
      }

      return false;
    } catch (error) {
      console.error(`Feature check failed for ${feature}:`, error.message);
      return false;
    }
  }

  async keepalive(usageData = null) {
    if (!this.serverId) {
      const validation = await this.validate();
      if (!validation.valid) {
        throw new Error('Failed to validate license for keepalive');
      }
    }

    const payload = {
      product: this.product,
      server_id: this.serverId,
    };

    if (usageData) {
      Object.assign(payload, usageData);
    }

    const response = await this.http.post('/api/v2/keepalive', payload);
    return response.data;
  }

  async getAllFeatures() {
    if (!this._isCacheValid()) {
      try {
        await this.validate();
      } catch (error) {
        console.error('Failed to refresh feature cache:', error.message);
      }
    }

    return { ...this._featureCache };
  }

  _updateFeatureCache(features) {
    this._featureCache = {};
    for (const feature of features) {
      if (feature.name) {
        this._featureCache[feature.name] = feature.entitled || false;
      }
    }
    this._cacheTimestamp = Date.now();
  }

  _isCacheValid() {
    if (this._cacheTimestamp === null) {
      return false;
    }
    return Date.now() - this._cacheTimestamp < CACHE_TTL_MS;
  }

  static isValidLicenseKey(key) {
    if (!key || key.length !== 29) {
      return false;
    }
    if (!key.startsWith('PENG-')) {
      return false;
    }
    return (key.match(/-/g) || []).length === 5;
  }
}

// Global client instance
let _globalClient = null;

export function getClient() {
  if (!_globalClient) {
    _globalClient = createClientFromEnv();
  }
  return _globalClient;
}

function createClientFromEnv() {
  const licenseKey = process.env.LICENSE_KEY;
  const product = process.env.PRODUCT_NAME;
  const baseUrl = process.env.LICENSE_SERVER_URL;

  if (!licenseKey || !product) {
    console.warn('LICENSE_KEY and PRODUCT_NAME environment variables required');
    return null;
  }

  return new PenguinTechLicenseClient(licenseKey, product, baseUrl);
}

export async function initializeLicensing(licenseKey = null, product = null) {
  const key = licenseKey || process.env.LICENSE_KEY;
  const prod = product || process.env.PRODUCT_NAME;

  if (!key || !prod) {
    throw new Error('LICENSE_KEY and PRODUCT_NAME are required');
  }

  _globalClient = new PenguinTechLicenseClient(key, prod);
  const validation = await _globalClient.validate();

  console.log(`License valid for ${validation.customer} (${validation.tier} tier)`);

  for (const feature of validation.features || []) {
    if (feature.entitled) {
      console.log(`Feature enabled: ${feature.name}`);
    }
  }

  return validation;
}

export async function checkFeature(feature) {
  const client = getClient();
  if (!client) {
    return false;
  }
  return client.checkFeature(feature);
}

export async function getAllFeatures() {
  const client = getClient();
  if (!client) {
    return {};
  }
  return client.getAllFeatures();
}

export async function keepalive(usageData = null) {
  const client = getClient();
  if (!client) {
    return false;
  }

  try {
    await client.keepalive(usageData);
    return true;
  } catch (error) {
    console.error('Failed to send keepalive:', error.message);
    return false;
  }
}

export { PenguinTechLicenseClient };
export default PenguinTechLicenseClient;
