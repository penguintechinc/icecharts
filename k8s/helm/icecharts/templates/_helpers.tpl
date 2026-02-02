{{/*
Expand the name of the chart.
*/}}
{{- define "icecharts.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "icecharts.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "icecharts.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "icecharts.labels" -}}
helm.sh/chart: {{ include "icecharts.chart" . }}
{{ include "icecharts.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.global.labels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "icecharts.selectorLabels" -}}
app.kubernetes.io/name: {{ include "icecharts.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
PostgreSQL fullname
*/}}
{{- define "icecharts.postgres.fullname" -}}
{{- printf "%s-postgres" (include "icecharts.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
PostgreSQL labels
*/}}
{{- define "icecharts.postgres.labels" -}}
{{ include "icecharts.labels" . }}
app.kubernetes.io/component: database
{{- end }}

{{/*
PostgreSQL selector labels
*/}}
{{- define "icecharts.postgres.selectorLabels" -}}
{{ include "icecharts.selectorLabels" . }}
app.kubernetes.io/component: database
app.kubernetes.io/name: {{ include "icecharts.name" . }}-postgres
{{- end }}

{{/*
Redis fullname
*/}}
{{- define "icecharts.redis.fullname" -}}
{{- printf "%s-redis" (include "icecharts.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Redis labels
*/}}
{{- define "icecharts.redis.labels" -}}
{{ include "icecharts.labels" . }}
app.kubernetes.io/component: cache
{{- end }}

{{/*
Redis selector labels
*/}}
{{- define "icecharts.redis.selectorLabels" -}}
{{ include "icecharts.selectorLabels" . }}
app.kubernetes.io/component: cache
app.kubernetes.io/name: {{ include "icecharts.name" . }}-redis
{{- end }}

{{/*
MinIO fullname
*/}}
{{- define "icecharts.minio.fullname" -}}
{{- printf "%s-minio" (include "icecharts.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
MinIO labels
*/}}
{{- define "icecharts.minio.labels" -}}
{{ include "icecharts.labels" . }}
app.kubernetes.io/component: storage
{{- end }}

{{/*
MinIO selector labels
*/}}
{{- define "icecharts.minio.selectorLabels" -}}
{{ include "icecharts.selectorLabels" . }}
app.kubernetes.io/component: storage
app.kubernetes.io/name: {{ include "icecharts.name" . }}-minio
{{- end }}

{{/*
API fullname
*/}}
{{- define "icecharts.api.fullname" -}}
{{- printf "%s-api" (include "icecharts.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
API labels
*/}}
{{- define "icecharts.api.labels" -}}
{{ include "icecharts.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
API selector labels
*/}}
{{- define "icecharts.api.selectorLabels" -}}
{{ include "icecharts.selectorLabels" . }}
app.kubernetes.io/component: backend
app.kubernetes.io/name: {{ include "icecharts.name" . }}-api
{{- end }}

{{/*
Web fullname
*/}}
{{- define "icecharts.web.fullname" -}}
{{- printf "%s-web" (include "icecharts.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Web labels
*/}}
{{- define "icecharts.web.labels" -}}
{{ include "icecharts.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Web selector labels
*/}}
{{- define "icecharts.web.selectorLabels" -}}
{{ include "icecharts.selectorLabels" . }}
app.kubernetes.io/component: frontend
app.kubernetes.io/name: {{ include "icecharts.name" . }}-web
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "icecharts.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "icecharts.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper image name for PostgreSQL
*/}}
{{- define "icecharts.postgres.image" -}}
{{- $registry := .Values.postgres.image.registry | default .Values.global.imageRegistry }}
{{- $repository := .Values.postgres.image.repository }}
{{- $tag := .Values.postgres.image.tag | toString }}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper image name for Redis
*/}}
{{- define "icecharts.redis.image" -}}
{{- $registry := .Values.redis.image.registry | default .Values.global.imageRegistry }}
{{- $repository := .Values.redis.image.repository }}
{{- $tag := .Values.redis.image.tag | toString }}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper image name for MinIO
*/}}
{{- define "icecharts.minio.image" -}}
{{- $registry := .Values.minio.image.registry | default .Values.global.imageRegistry }}
{{- $repository := .Values.minio.image.repository }}
{{- $tag := .Values.minio.image.tag | toString }}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper image name for API
*/}}
{{- define "icecharts.api.image" -}}
{{- $registry := .Values.api.image.registry | default .Values.global.imageRegistry }}
{{- $repository := .Values.api.image.repository }}
{{- $tag := .Values.api.image.tag | toString }}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper image name for Web
*/}}
{{- define "icecharts.web.image" -}}
{{- $registry := .Values.web.image.registry | default .Values.global.imageRegistry }}
{{- $repository := .Values.web.image.repository }}
{{- $tag := .Values.web.image.tag | toString }}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper image pull policy
*/}}
{{- define "icecharts.imagePullPolicy" -}}
{{- if .tag }}
{{- if eq .tag "latest" }}
{{- print "Always" }}
{{- else }}
{{- print "IfNotPresent" }}
{{- end }}
{{- else }}
{{- print "IfNotPresent" }}
{{- end }}
{{- end }}

{{/*
Return the storage class name
*/}}
{{- define "icecharts.storageClass" -}}
{{- $storageClass := .storageClass }}
{{- if .global }}
{{- if .global.storageClass }}
{{- $storageClass = .global.storageClass }}
{{- end }}
{{- end }}
{{- if $storageClass }}
{{- printf "%s" $storageClass }}
{{- end }}
{{- end }}

{{/*
Return the secret name for credentials
*/}}
{{- define "icecharts.secretName" -}}
{{- if eq .Values.secrets.provider "kubernetes" }}
{{- printf "%s-secrets" (include "icecharts.fullname" .) }}
{{- else }}
{{- printf "%s-external-secrets" (include "icecharts.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Return the Postgres connection details
*/}}
{{- define "icecharts.postgres.host" -}}
{{- printf "%s-service" (include "icecharts.postgres.fullname" .) }}
{{- end }}

{{- define "icecharts.postgres.port" -}}
{{- .Values.postgres.service.port }}
{{- end }}

{{/*
Return the Redis connection details
*/}}
{{- define "icecharts.redis.host" -}}
{{- printf "%s-service" (include "icecharts.redis.fullname" .) }}
{{- end }}

{{- define "icecharts.redis.port" -}}
{{- .Values.redis.service.port }}
{{- end }}

{{/*
Return the MinIO connection details
*/}}
{{- define "icecharts.minio.host" -}}
{{- printf "%s-service" (include "icecharts.minio.fullname" .) }}
{{- end }}

{{- define "icecharts.minio.apiPort" -}}
{{- .Values.minio.service.apiPort }}
{{- end }}

{{- define "icecharts.minio.consolePort" -}}
{{- .Values.minio.service.consolePort }}
{{- end }}

{{/*
Return the MinIO endpoint URL
*/}}
{{- define "icecharts.minio.endpoint" -}}
{{- printf "%s:%d" (include "icecharts.minio.host" .) (int .Values.minio.service.apiPort) }}
{{- end }}

{{/*
Return the API URL for frontend configuration
*/}}
{{- define "icecharts.api.url" -}}
{{- if .Values.ingress.enabled }}
{{- if .Values.ingress.tls.enabled }}
{{- printf "https://%s" .Values.ingress.host }}
{{- else }}
{{- printf "http://%s" .Values.ingress.host }}
{{- end }}
{{- else }}
{{- printf "http://%s-service" (include "icecharts.api.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Validate ingress configuration
*/}}
{{- define "icecharts.validateIngress" -}}
{{- if .Values.ingress.enabled }}
{{- if not (has .Values.ingress.className (list "traefik" "alb" "gce" "azure/application-gateway")) }}
{{- fail "ingress.className must be one of: traefik, alb, gce, azure/application-gateway" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Validate secrets configuration
*/}}
{{- define "icecharts.validateSecrets" -}}
{{- if not (has .Values.secrets.provider (list "kubernetes" "external-secrets")) }}
{{- fail "secrets.provider must be either 'kubernetes' or 'external-secrets'" }}
{{- end }}
{{- if eq .Values.secrets.provider "external-secrets" }}
{{- if not (has .Values.secrets.externalSecrets.backend (list "aws" "gcp" "azure" "infisical")) }}
{{- fail "secrets.externalSecrets.backend must be one of: aws, gcp, azure, infisical" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Prometheus service monitor name
*/}}
{{- define "icecharts.prometheus.fullname" -}}
{{- printf "%s-prometheus" (include "icecharts.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Grafana fullname
*/}}
{{- define "icecharts.grafana.fullname" -}}
{{- printf "%s-grafana" (include "icecharts.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Namespace to use
*/}}
{{- define "icecharts.namespace" -}}
{{- if .Values.namespace.create }}
{{- .Values.namespace.name }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}
