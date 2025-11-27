import { useState } from 'react';
import { FileUp, BookOpen, Brain, CheckCircle2, XCircle, FileText, ExternalLink } from 'lucide-react';
import UploadSection from './components/UploadSection';
import QuizSection from './components/QuizSection';
import SummarySection from './components/SummarySection';
import { ProcessedData, QuizTab } from './types';

function App() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('');
  const [data, setData] = useState<ProcessedData | null>(null);
  const [activeTab, setActiveTab] = useState<QuizTab>('basic');

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);
    setStatus('PDF 분석 및 문제 생성 중...');

    const formData = new FormData();
    formData.append('pdf', file);

    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!result.ok) {
        throw new Error(result.error || '처리 실패');
      }

      setData(result);
      setStatus('완료! 생성된 문제와 요약을 확인하세요.');

      setTimeout(() => setStatus(''), 3000);
    } catch (error) {
      setStatus(`오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-emerald-950">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(16,185,129,0.1),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(16,185,129,0.08),transparent_50%)]" />

      <div className="relative max-w-7xl mx-auto px-4 py-8 md:py-12">
        <header className="mb-8 md:mb-12">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl shadow-lg shadow-emerald-500/20">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-white to-emerald-400 bg-clip-text text-transparent">
                  PDF 학습 도우미
                </h1>
                <p className="text-sm text-gray-400 mt-1">AI 기반 요약 및 문제 생성 서비스</p>
              </div>
            </div>

            <nav className="flex gap-3 text-sm">
              <a
                href="/problems"
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-800/50 border border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-emerald-500/50 hover:text-emerald-400 transition-all"
              >
                <FileText className="w-4 h-4" />
                저장된 문제
              </a>
              <a
                href="/summaries"
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-800/50 border border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-emerald-500/50 hover:text-emerald-400 transition-all"
              >
                <BookOpen className="w-4 h-4" />
                저장된 요약
              </a>
            </nav>
          </div>
        </header>

        <UploadSection
          onUpload={handleFileUpload}
          isProcessing={isProcessing}
          status={status}
        />

        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <QuizSection
              key={activeTab}
              problems={data.problems}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />
            <div className="text-white">
              <SummarySection
                summaryHtml={data.summary_html}
                summaryUrl={data.summary_url}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;