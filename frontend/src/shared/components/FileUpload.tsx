import { useRef, useState } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

interface FileUploadProps {
  accept?: string
  multiple?: boolean
  maxSizeMB?: number
  label?: string
  onChange: (files: File[]) => void
  error?: string
}

export function FileUpload({
  accept = '.pdf',
  multiple = false,
  maxSizeMB = 50,
  label = 'Arraste ou clique para selecionar',
  onChange,
  error,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [files, setFiles] = useState<File[]>([])

  const handleFiles = (incoming: FileList | null) => {
    if (!incoming) return
    const arr = Array.from(incoming).filter(f => f.size <= maxSizeMB * 1024 * 1024)
    const next = multiple ? [...files, ...arr] : arr
    setFiles(next)
    onChange(next)
  }

  const removeFile = (idx: number) => {
    const next = files.filter((_, i) => i !== idx)
    setFiles(next)
    onChange(next)
  }

  return (
    <div className="space-y-3">
      <div
        className={cn(
          'fasi-upload-area',
          dragging && 'border-fasi-500 bg-fasi-50',
          error && 'border-red-300',
        )}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }}
      >
        <Upload className="w-8 h-8 mx-auto mb-2 text-fasi-400" />
        <p className="text-sm font-medium text-fasi-600">{label}</p>
        <p className="text-xs text-muted-foreground mt-1">
          {accept.toUpperCase().replace(/\./g, '')} • máx {maxSizeMB}MB
          {multiple && ' • múltiplos arquivos'}
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {/* Lista de arquivos */}
      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((f, i) => (
            <li key={i} className="flex items-center gap-3 rounded-lg border border-border bg-muted/40 px-3 py-2">
              <FileText className="w-4 h-4 text-fasi-500 shrink-0" />
              <span className="flex-1 text-sm truncate text-foreground">{f.name}</span>
              <span className="text-xs text-muted-foreground shrink-0">
                {(f.size / (1024 * 1024)).toFixed(1)} MB
              </span>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); removeFile(i) }}
                className="text-muted-foreground hover:text-red-500 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}
