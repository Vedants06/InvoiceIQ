import { useRef, useState, type ReactNode } from 'react'
import { CheckCircle2, FileText, Trash2, UploadCloud } from 'lucide-react'
import { cn } from '../../lib/utils'

interface Props {
  label: string
  accept: string
  hint: string
  required?: boolean
  file: File | null
  onFile: (file: File | null) => void
  disabled?: boolean
  icon?: ReactNode
}

export default function FileDropzone({
  label,
  accept,
  hint,
  required,
  file,
  onFile,
  disabled,
  icon,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  function handleFiles(files: FileList | null) {
    if (files && files.length > 0) onFile(files[0])
  }

  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-[13px] font-semibold text-stone-800">
          <span className="text-stone-400">{icon ?? <FileText className="h-3.5 w-3.5" />}</span>
          {label}
          {required ? (
            <span className="text-[#96231b]">*</span>
          ) : (
            <span className="text-[11px] font-normal text-stone-400">optional</span>
          )}
        </p>
        {file && !disabled && (
          <button
            type="button"
            onClick={() => onFile(null)}
            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-stone-400 transition-colors hover:text-[#96231b]"
          >
            <Trash2 className="h-3 w-3" strokeWidth={1.75} />
            Remove
          </button>
        )}
      </div>

      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          if (!disabled) handleFiles(e.dataTransfer.files)
        }}
        aria-label={file ? `Replace ${label} file` : `Upload ${label}`}
        className={cn(
          'flex w-full flex-col items-center justify-center gap-2 rounded border border-dashed px-6 py-7 text-center transition-colors duration-150',
          dragging
            ? 'border-accent-600 bg-accent-50/70'
            : file
              ? 'border-[#a8cbb6] bg-[#f1f7f3]/50 hover:border-[#6f9f84]'
              : 'border-paper-400 bg-paper-100/50 hover:border-accent-600 hover:bg-accent-50/30',
          disabled && 'cursor-not-allowed opacity-60',
        )}
      >
        {file ? (
          <>
            <span className="flex h-9 w-9 items-center justify-center rounded border border-[#cfe3d7] bg-[#e3efe7] text-[#2f6b47]">
              <CheckCircle2 className="h-4 w-4" strokeWidth={1.75} />
            </span>
            <span className="max-w-full truncate text-[13.5px] font-semibold text-stone-900">
              {file.name}
            </span>
            <span className="tabular text-[11.5px] text-stone-500">
              {(file.size / 1024).toFixed(0)} KB · click to replace
            </span>
          </>
        ) : (
          <>
            <span
              className={cn(
                'flex h-9 w-9 items-center justify-center rounded border border-paper-300 bg-paper-50 text-stone-400',
                dragging && 'border-accent-600 text-accent-700',
              )}
            >
              <UploadCloud className="h-4 w-4" strokeWidth={1.75} />
            </span>
            <span className="text-[13.5px] text-stone-600">
              Drop a file here or{' '}
              <span className="font-medium text-accent-800 underline underline-offset-2">
                browse
              </span>
            </span>
            <span className="flex items-center gap-1 text-[11.5px] text-stone-400">
              <FileText className="h-3 w-3" strokeWidth={1.75} />
              {hint}
            </span>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </button>
    </div>
  )
}
