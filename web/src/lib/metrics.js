/**
 * Prometheus metrics integration using prom-client
 */

import client from 'prom-client';

export function createPrometheusMetrics() {
  const register = new client.Registry();

  register.setDefaultLabels({
    app: process.env.APP_NAME || 'icecharts',
  });

  client.collectDefaultMetrics({ register });

  const httpRequestDuration = new client.Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'route', 'status_code'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10],
    registers: [register],
  });

  const httpRequestsTotal = new client.Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status_code'],
    registers: [register],
  });

  return {
    register,
    httpRequestDuration,
    httpRequestsTotal,
  };
}

export default createPrometheusMetrics;
