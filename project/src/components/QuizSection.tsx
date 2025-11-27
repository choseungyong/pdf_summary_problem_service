import { useState } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { Problems, QuizTab, QuizQuestion } from '../types';

interface QuizSectionProps {
  problems: Problems;
  activeTab: QuizTab;
  onTabChange: (tab: QuizTab) => void;
}

interface QuizItemProps {
  question: QuizQuestion;
  index: number;
}

function QuizItem({ question, index }: QuizItemProps) {
  const [selectedChoice, setSelectedChoice] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  const handleChoiceSelect = (choiceIndex: number) => {
    setSelectedChoice(choiceIndex);
    setShowExplanation(true);
  };

  const isCorrect = selectedChoice === question.answer_index;

  return (
    <div className="bg-gradient-to-br from-gray-800/80 to-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-5 transition-all hover:border-emerald-500/30">
      <div className="flex gap-4">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-white font-semibold text-sm shadow-lg shadow-emerald-500/20">
          {index + 1}
        </div>

        <div className="flex-grow space-y-4">
          <p className="text-white font-medium leading-relaxed">{question.question}</p>

          <div className="space-y-2">
            {question.choices.map((choice, choiceIndex) => {
              const isSelected = selectedChoice === choiceIndex;
              const isAnswer = choiceIndex === question.answer_index;
              const showResult = showExplanation && isSelected;

              return (
                <button
                  key={choiceIndex}
                  onClick={() => handleChoiceSelect(choiceIndex)}
                  disabled={showExplanation}
                  className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                    showResult
                      ? isCorrect
                        ? 'border-emerald-500 bg-emerald-500/10'
                        : 'border-red-500 bg-red-500/10'
                      : isSelected
                      ? 'border-emerald-500/50 bg-gray-700/50'
                      : 'border-gray-600/50 bg-gray-800/30 hover:border-emerald-500/40 hover:bg-gray-700/40'
                  } ${showExplanation ? 'cursor-default' : 'cursor-pointer'}`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-medium ${
                        showResult
                          ? isCorrect
                            ? 'border-emerald-500 bg-emerald-500 text-white'
                            : 'border-red-500 bg-red-500 text-white'
                          : 'border-gray-500 text-gray-400'
                      }`}
                    >
                      {String.fromCharCode(65 + choiceIndex)}
                    </span>
                    <span className={showResult ? (isCorrect ? 'text-emerald-200' : 'text-red-200') : 'text-gray-200'}>
                      {choice}
                    </span>
                    {showResult && (
                      <div className="ml-auto">
                        {isCorrect ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-400" />
                        )}
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {showExplanation && (
            <div
              className={`p-4 rounded-xl border ${
                isCorrect
                  ? 'bg-emerald-500/10 border-emerald-500/30'
                  : 'bg-red-500/10 border-red-500/30'
              }`}
            >
              <div className="flex items-start gap-2">
                {isCorrect ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <p className={`font-semibold mb-1 ${isCorrect ? 'text-emerald-400' : 'text-red-400'}`}>
                    {isCorrect ? '정답입니다!' : '오답입니다.'}
                  </p>
                  <p className={`text-sm ${isCorrect ? 'text-emerald-200' : 'text-red-200'}`}>
                    {question.explanation}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QuizSection({ problems, activeTab, onTabChange }: QuizSectionProps) {
  const currentProblems = problems[activeTab] || [];

  return (
    <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-sm rounded-3xl shadow-2xl border border-gray-700/50 p-6 md:p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span className="text-emerald-400">💡</span> 문제 풀기
        </h2>

        <div className="inline-flex rounded-xl bg-gray-800/50 p-1 border border-gray-700/50">
          <button
            onClick={() => onTabChange('basic')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              activeTab === 'basic'
                ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-lg shadow-emerald-500/20'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            기초
          </button>
          <button
            onClick={() => onTabChange('advanced')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              activeTab === 'advanced'
                ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-lg shadow-emerald-500/20'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            심화
          </button>
        </div>
      </div>

      <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2 custom-scrollbar">
        {currentProblems.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">PDF를 업로드하여 문제를 생성하세요.</p>
          </div>
        ) : (
          currentProblems.map((question, index) => (
            <QuizItem key={index} question={question} index={index} />
          ))
        )}
      </div>
    </div>
  );
}

export default QuizSection;
