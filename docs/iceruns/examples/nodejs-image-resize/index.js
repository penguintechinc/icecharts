/**
 * IceRuns Example: Node.js Image Resize
 *
 * This example demonstrates image processing with Node.js.
 *
 * Handler: index.handler
 * Entrypoint: index.js
 */

const sharp = require('sharp');
const https = require('https');
const { URL } = require('url');

/**
 * Resize an image from a URL
 *
 * @param {Object} event - Input data
 * @param {string} event.image_url - URL of image to resize
 * @param {number} event.width - Target width in pixels
 * @param {number} event.height - Target height in pixels (optional)
 * @returns {Promise<Object>} Result with resized image info
 */
exports.handler = async (event) => {
  try {
    // Validate input
    const imageUrl = event.image_url || event.url;
    const width = event.width || 800;
    const height = event.height || width;

    if (!imageUrl) {
      return {
        error: 'image_url parameter required',
        success: false
      };
    }

    // Download image from URL
    const imageBuffer = await downloadImage(imageUrl);

    // Resize with sharp
    const resized = await sharp(imageBuffer)
      .resize(width, height, {
        fit: 'cover',
        position: 'center'
      })
      .toBuffer();

    return {
      message: 'Image resized successfully',
      original_size: imageBuffer.length,
      resized_size: resized.length,
      dimensions: {
        width: width,
        height: height
      },
      success: true
    };
  } catch (error) {
    return {
      error: error.message,
      success: false
    };
  }
};

/**
 * Download image from URL
 *
 * @param {string} url - Image URL
 * @returns {Promise<Buffer>} Image data
 */
function downloadImage(url) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const protocol = parsedUrl.protocol === 'https:' ? https : require('http');

    protocol.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`HTTP ${response.statusCode}`));
        return;
      }

      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => resolve(Buffer.concat(chunks)));
    }).on('error', reject);
  });
}
