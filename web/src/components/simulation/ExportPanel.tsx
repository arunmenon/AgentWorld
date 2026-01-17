import { memo, useState, useEffect } from 'react'
import {
  Download,
  FileJson,
  FileText,
  Filter,
  Loader2,
  Check,
  AlertCircle,
} from 'lucide-react'
import { Button, Badge, Card, Input } from '@/components/ui'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ExportPanelProps {
  simulationId: string
  className?: string
}

interface ExportFormat {
  id: string
  name: string
  description: string
  icon: typeof FileJson
  requiresEvaluations?: boolean
}

const EXPORT_FORMATS: ExportFormat[] = [
  {
    id: 'jsonl',
    name: 'JSONL',
    description: 'Raw messages as JSON Lines',
    icon: FileJson,
  },
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'OpenAI fine-tuning format',
    icon: FileText,
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Anthropic fine-tuning format',
    icon: FileText,
  },
  {
    id: 'sharegpt',
    name: 'ShareGPT',
    description: 'ShareGPT format for open-source models',
    icon: FileText,
  },
  {
    id: 'alpaca',
    name: 'Alpaca',
    description: 'Alpaca instruction tuning format',
    icon: FileText,
  },
  {
    id: 'dpo',
    name: 'DPO Pairs',
    description: 'Preference pairs for DPO training',
    icon: FileText,
    requiresEvaluations: true,
  },
]

const REDACTION_PROFILES = [
  { id: 'none', name: 'None', description: 'No redaction (internal use only)' },
  { id: 'basic', name: 'Basic', description: 'Remove debug traces and system prompts' },
  { id: 'strict', name: 'Strict', description: 'Anonymize names, redact PII' },
]

export const ExportPanel = memo(function ExportPanel({
  simulationId,
  className,
}: ExportPanelProps) {
  const [selectedFormat, setSelectedFormat] = useState<string>('jsonl')
  const [redactionProfile, setRedactionProfile] = useState<string>('basic')
  const [anonymize, setAnonymize] = useState(false)
  const [minScore, setMinScore] = useState<string>('')
  const [isExporting, setIsExporting] = useState(false)
  const [exportResult, setExportResult] = useState<{
    success: boolean
    message: string
    recordCount?: number
  } | null>(null)
  const [formatInfo, setFormatInfo] = useState<{
    available_formats: string[]
    message_count: number
    has_evaluations: boolean
  } | null>(null)

  useEffect(() => {
    const loadFormatInfo = async () => {
      try {
        const info = await api.getExportFormats(simulationId)
        setFormatInfo(info)
      } catch (error) {
        console.error('Failed to load export formats:', error)
      }
    }
    loadFormatInfo()
  }, [simulationId])

  const handleExport = async () => {
    setIsExporting(true)
    setExportResult(null)

    try {
      const blob = await api.downloadExport(simulationId, selectedFormat, {
        redaction: redactionProfile,
        anonymize,
        min_score: minScore ? parseFloat(minScore) : undefined,
      })

      // Create download link
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${simulationId}_${selectedFormat}.jsonl`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      setExportResult({
        success: true,
        message: 'Export downloaded successfully',
      })
    } catch (error) {
      setExportResult({
        success: false,
        message: error instanceof Error ? error.message : 'Export failed',
      })
    } finally {
      setIsExporting(false)
    }
  }

  const handlePreview = async () => {
    setIsExporting(true)
    setExportResult(null)

    try {
      const result = await api.exportSimulation(simulationId, {
        format: selectedFormat,
        redaction: redactionProfile,
        anonymize,
        min_score: minScore ? parseFloat(minScore) : undefined,
        inline: true,
      })

      setExportResult({
        success: true,
        message: `Preview: ${result.record_count} records`,
        recordCount: result.record_count,
      })
    } catch (error) {
      setExportResult({
        success: false,
        message: error instanceof Error ? error.message : 'Preview failed',
      })
    } finally {
      setIsExporting(false)
    }
  }

  const selectedFormatInfo = EXPORT_FORMATS.find(f => f.id === selectedFormat)
  const canExport = selectedFormatInfo && (
    !selectedFormatInfo.requiresEvaluations ||
    (formatInfo?.has_evaluations ?? false)
  )

  return (
    <Card className={cn('p-4 space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Export Data</h3>
        {formatInfo && (
          <Badge variant="default">{formatInfo.message_count} messages</Badge>
        )}
      </div>

      {/* Format Selection */}
      <div className="space-y-2">
        <label className="text-sm text-foreground-secondary">Format</label>
        <div className="grid grid-cols-2 gap-2">
          {EXPORT_FORMATS.map((format) => {
            const FormatIcon = format.icon
            const disabled = format.requiresEvaluations && !formatInfo?.has_evaluations
            return (
              <button
                key={format.id}
                onClick={() => setSelectedFormat(format.id)}
                disabled={disabled}
                className={cn(
                  'p-3 rounded-lg border text-left transition-colors',
                  selectedFormat === format.id
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-border-hover',
                  disabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <FormatIcon className="h-4 w-4" />
                  <span className="font-medium text-sm">{format.name}</span>
                </div>
                <p className="text-xs text-foreground-muted">{format.description}</p>
                {format.requiresEvaluations && !formatInfo?.has_evaluations && (
                  <p className="text-xs text-warning mt-1">Requires evaluations</p>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Redaction Profile */}
      <div className="space-y-2">
        <label className="text-sm text-foreground-secondary">Redaction Profile</label>
        <div className="flex gap-2">
          {REDACTION_PROFILES.map((profile) => (
            <button
              key={profile.id}
              onClick={() => setRedactionProfile(profile.id)}
              className={cn(
                'px-3 py-2 rounded-lg border text-sm transition-colors',
                redactionProfile === profile.id
                  ? 'border-primary bg-primary/10'
                  : 'border-border hover:border-border-hover'
              )}
              title={profile.description}
            >
              {profile.name}
            </button>
          ))}
        </div>
      </div>

      {/* Filter Options */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-foreground-muted" />
          <span className="text-sm text-foreground-secondary">Filters</span>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={anonymize}
              onChange={(e) => setAnonymize(e.target.checked)}
              className="rounded border-border"
            />
            Anonymize agents
          </label>

          <div className="flex items-center gap-2">
            <label className="text-sm">Min score:</label>
            <Input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
              placeholder="0.0"
              className="w-20 h-8"
            />
          </div>
        </div>
      </div>

      {/* Result Message */}
      {exportResult && (
        <div
          className={cn(
            'p-3 rounded-lg flex items-center gap-2 text-sm',
            exportResult.success
              ? 'bg-success/10 text-success'
              : 'bg-error/10 text-error'
          )}
        >
          {exportResult.success ? (
            <Check className="h-4 w-4" />
          ) : (
            <AlertCircle className="h-4 w-4" />
          )}
          {exportResult.message}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        <Button
          onClick={handlePreview}
          variant="outline"
          disabled={isExporting || !canExport}
          className="flex-1"
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <FileJson className="h-4 w-4 mr-2" />
          )}
          Preview
        </Button>
        <Button
          onClick={handleExport}
          disabled={isExporting || !canExport}
          className="flex-1"
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          Download
        </Button>
      </div>
    </Card>
  )
})

export default ExportPanel
