import { useState, useRef } from 'react';
import { FileUp, Loader2, AlertCircle } from 'lucide-react';

interface UploadSectionProps {
  onUpload: (file: File) => void;
  isProcessing: boolean;
  status: string;
}

function UploadSection({ onUpload, isProcessing, status }: UploadSectionProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setSelectedFile(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile && !isProcessing) {
      onUpload(selectedFile);
    }
  };

  return (
    <section className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-sm rounded-3xl shadow-2xl border border-gray-700/50 p-6 md:p-8">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div
          className={`relative border-2 border-dashed rounded-2xl p-8 md:p-12 text-center transition-all ${
            dragActive
              ? 'border-emerald-500 bg-emerald-500/10'
              : 'border-gray-600 hover:border-emerald-500/50 bg-gray-800/30'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="hidden"
            disabled={isProcessing}
          />

          <div className="flex flex-col items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 rounded-2xl">
              <FileUp className="w-12 h-12 text-emerald-400" />
            </div>

            <div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {selectedFile ? selectedFile.name : 'PDF 파일을 업로드하세요'}
              </h3>
              <p className="text-sm text-gray-400">
                파일을 드래그 앤 드롭하거나{' '}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-emerald-400 hover:text-emerald-300 underline transition-colors"
                  disabled={isProcessing}
                >
                  클릭하여 선택
                </button>
              </p>
            </div>

            {selectedFile && (
              <button
                type="submit"
                disabled={isProcessing}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-medium rounded-xl shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    처리 중...
                  </>
                ) : (
                  <>
                    <FileUp className="w-5 h-5" />
                    문제 생성하기
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {status && (
          <div
            className={`flex items-center gap-3 p-4 rounded-xl ${
              status.includes('오류')
                ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                : status.includes('완료')
                ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                : 'bg-gray-700/30 border border-gray-600/30 text-gray-300'
            }`}
          >
            {status.includes('오류') ? (
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
            ) : isProcessing ? (
              <Loader2 className="w-5 h-5 flex-shrink-0 animate-spin" />
            ) : (
              <FileUp className="w-5 h-5 flex-shrink-0" />
            )}
            <p className="text-sm">{status}</p>
          </div>
        )}

        <div className="flex items-start gap-2 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl">
          <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-amber-200">
            <strong>중요:</strong> OPENAI_API_KEY 환경변수가 설정되어 있어야 합니다.
            OpenAI API 사용 요금이 발생할 수 있습니다.
          </p>
        </div>
      </form>
    </section>
  );
}

export default UploadSection;
