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
Chart label helper
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
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "icecharts.selectorLabels" -}}
app.kubernetes.io/name: {{ include "icecharts.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Namespace helper
*/}}
{{- define "icecharts.namespace" -}}
{{- default .Release.Namespace .Values.namespace }}
{{- end }}

{{/*
Image helper for web
*/}}
{{- define "icecharts.web.image" -}}
{{- $tag := default .Values.image.tag .Values.web.image.tag -}}
{{- printf "%s/%s:%s" .Values.image.registry .Values.web.image.repository $tag -}}
{{- end }}

{{/*
Image helper for api
*/}}
{{- define "icecharts.api.image" -}}
{{- $tag := default .Values.image.tag .Values.api.image.tag -}}
{{- printf "%s/%s:%s" .Values.image.registry .Values.api.image.repository $tag -}}
{{- end }}

{{/*
DB host helper - constructs FQDN from namespace
*/}}
{{- define "icecharts.dbHost" -}}
{{- printf "postgres.%s.svc.cluster.local" (include "icecharts.namespace" .) -}}
{{- end }}

{{/*
Redis host helper
*/}}
{{- define "icecharts.redisHost" -}}
{{- printf "redis.%s.svc.cluster.local" (include "icecharts.namespace" .) -}}
{{- end }}

{{/*
MinIO endpoint helper
*/}}
{{- define "icecharts.minioEndpoint" -}}
{{- printf "minio.%s.svc.cluster.local:%d" (include "icecharts.namespace" .) (int .Values.minio.ports.api) -}}
{{- end }}
