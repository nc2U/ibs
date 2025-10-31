{{/*
Expand the name of the chart.
*/}}
{{- define "cnpg-postgres.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "cnpg-postgres.fullname" -}}
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
{{- define "cnpg-postgres.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "cnpg-postgres.labels" -}}
helm.sh/chart: {{ include "cnpg-postgres.chart" . }}
{{ include "cnpg-postgres.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "cnpg-postgres.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cnpg-postgres.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "cnpg-postgres.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "cnpg-postgres.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper PostgreSQL image name
*/}}
{{- define "cnpg-postgres.image" -}}
{{- $registryName := .Values.image.registry -}}
{{- $repositoryName := .Values.image.repository -}}
{{- $tag := .Values.image.tag | toString -}}
{{- if $registryName }}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- else }}
{{- printf "%s:%s" $repositoryName $tag -}}
{{- end }}
{{- end }}

{{/*
Return the cluster name
*/}}
{{- define "cnpg-postgres.clusterName" -}}
{{- include "cnpg-postgres.fullname" . }}
{{- end }}

{{/*
Return true if a secret object should be created
*/}}
{{- define "cnpg-postgres.createSecret" -}}
{{- if not .Values.auth.existingSecret }}
    {{- true -}}
{{- end }}
{{- end }}

{{/*
Return the name of the secret containing PostgreSQL credentials
*/}}
{{- define "cnpg-postgres.secretName" -}}
{{- if .Values.auth.existingSecret }}
    {{- .Values.auth.existingSecret }}
{{- else }}
    {{- include "cnpg-postgres.fullname" . }}
{{- end }}
{{- end }}

{{/*
Return PostgreSQL database name
*/}}
{{- define "cnpg-postgres.database" -}}
{{- .Values.auth.database | default "app" }}
{{- end }}

{{/*
Return PostgreSQL username
*/}}
{{- define "cnpg-postgres.username" -}}
{{- .Values.auth.username | default "app" }}
{{- end }}

{{/*
Return the backup destination path
*/}}
{{- define "cnpg-postgres.backupDestination" -}}
{{- if .Values.backup.s3.enabled }}
{{- printf "s3://%s/%s" .Values.backup.s3.bucket (include "cnpg-postgres.fullname" .) }}
{{- else }}
{{- .Values.backup.destinationPath | default "file:///var/lib/postgresql/backup" }}
{{- end }}
{{- end }}
