export type QuizTab = 'basic' | 'advanced';

export interface QuizQuestion {
  question: string;
  choices: string[];
  answer_index: number;
  explanation: string;
}

export interface Problems {
  basic: QuizQuestion[];
  advanced: QuizQuestion[];
}

export interface ProcessedData {
  ok: boolean;
  problems: Problems;
  summary_html: string;
  summary_url?: string;
  problems_url?: string;
}
