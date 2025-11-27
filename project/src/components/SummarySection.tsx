import { ExternalLink } from 'lucide-react';

interface SummarySectionProps {
  summaryHtml: string;
  summaryUrl?: string;
}

function SummarySection({ summaryHtml, summaryUrl }: SummarySectionProps) {
  return (
    <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-sm rounded-3xl shadow-2xl border border-gray-700/50 p-6 md:p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span className="text-emerald-400">📚</span> 요약 정리
        </h2>

        {summaryUrl && (
          <a
            href={summaryUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-emerald-400 hover:text-emerald-300 border border-emerald-500/30 hover:border-emerald-500/50 rounded-lg transition-all"
          >
            <ExternalLink className="w-4 h-4" />
            원문 보기
          </a>
        )}
      </div>

      <div className="max-h-[800px] overflow-y-auto pr-2 custom-scrollbar">
        {summaryHtml ? (
          <article
            className="prose prose-invert prose-emerald max-w-none
              prose-headings:text-emerald-400 prose-headings:font-bold
              prose-h2:text-2xl prose-h2:mb-4 prose-h2:mt-6
              prose-h3:text-xl prose-h3:mb-3 prose-h3:mt-4
              prose-p:text-gray-300 prose-p:leading-relaxed
              prose-a:text-emerald-400 prose-a:no-underline hover:prose-a:underline
              prose-strong:text-white prose-strong:font-semibold
              prose-code:text-emerald-300 prose-code:bg-gray-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
              prose-pre:bg-gray-800 prose-pre:border prose-pre:border-gray-700
              prose-ul:text-gray-300 prose-ol:text-gray-300
              prose-li:marker:text-emerald-400
              prose-blockquote:border-l-emerald-500 prose-blockquote:text-gray-400
              prose-table:border-collapse prose-table:w-full
              prose-thead:border-b prose-thead:border-gray-700
              prose-th:text-emerald-400 prose-th:font-semibold prose-th:p-3 prose-th:text-left
              prose-td:text-gray-300 prose-td:p-3 prose-td:border-t prose-td:border-gray-700"
            dangerouslySetInnerHTML={{ __html: summaryHtml }}
          />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-400">요약 내용이 여기에 표시됩니다.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default SummarySection;
