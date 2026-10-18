import { apiClient } from './api-client';
import { API_BASE_URL } from './api-config';

// Resume type (should match backend)
export interface Resume {
  id: number;
  title: string;
  file_name: string;
}

// Types matching backend models
export interface InterviewStartRequest {
  session_type: 'technical' | 'behavioral' | 'mixed' | 'job-specific';
  job_role: string;
  difficulty_level: 'junior' | 'mid' | 'senior';
  num_questions: number;
  resume_id?: number;
}

export interface InterviewStartResponse {
  session_id: number;
  message: string;
  first_question: Question;
}

export interface Question {
  question_id: number;
  question_number: number;
  total_questions: number;
  question_text: string;
  question_type: string;
}

export interface AnswerRequest {
  session_id: number;
  question_id: number;
  answer: string;
  time_taken_seconds?: number;
}

export interface AnswerResponse {
  question_number: number;
  feedback: AnswerFeedback;
  scores: AnswerScores;
  has_more_questions: boolean;
  next_question?: Question;
}

export interface AnswerFeedback {
  strengths: string[];
  weaknesses: string[];
  missing_points: string[];
  suggestions: string[];
}

export interface AnswerScores {
  overall: number;
  relevance: number;
  completeness: number;
  clarity: number;
  technical_accuracy: number;
}

export interface SessionDetailResponse {
  session_id: number;
  job_role: string;
  session_type: string;
  difficulty_level: string;
  total_questions: number;
  questions_answered: number;
  average_scores: {
    overall: number;
    relevance: number;
    completeness: number;
    clarity: number;
    technical_accuracy: number;
    communication: number;
  } | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  questions_and_answers: QuestionAnswer[];
  feedback?: {
    strengths: string[];
    areas_to_improve: string[];
    recommended_resources: string[];
    preparation_tips: string;
    practice_recommendations: string;
  } | null;
}

export interface QuestionAnswer {
  question_number: number;
  question_text: string;
  question_type: string;
  user_answer: string | null;
  time_taken_seconds: number | null;
  feedback: AnswerFeedback | null;
  scores: AnswerScores | null;
  sentiment: string | null;
}

export interface SessionListResponse {
  sessions: SessionListItem[];
  total_count: number;
}

export interface SessionListItem {
  id: number;  // Backend returns 'id', not 'session_id'
  job_role: string;
  session_type: string;
  difficulty_level: string;
  total_questions: number;
  questions_answered: number;
  average_score: number | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  overall_performance?: string | null;
  technical_rating?: number | null;
  communication_rating?: number | null;
  confidence_rating?: number | null;
}

export interface SessionCompletionResponse {
  session_id: number;
  completed: boolean;
  questions_answered: number;
  total_time_seconds: number;
  average_scores: {
    overall: number;
    relevance: number;
    completeness: number;
    clarity: number;
    technical_accuracy: number;
    communication: number;
  };
  performance: string;
  ratings: {
    technical: number;
    communication: number;
    confidence: number;
  };
  feedback: {
    strengths: string[];
    areas_to_improve: string[];
    recommended_resources: string[];
    preparation_tips: string;
    practice_recommendations: string;
  };
  message: string;
}

class InterviewService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE_URL}/interview`;
  }

  /**
   * Start a new interview session
   */
  async startSession(request: InterviewStartRequest): Promise<InterviewStartResponse> {
    try {
      const response = await apiClient.post<InterviewStartResponse>(`${this.baseURL}/start`, request);
      return response;
    } catch (error: any) {
      console.error('Error starting interview session:', error);
      throw error;
    }
  }

  /**
   * Submit an answer to the current question
   */
  async submitAnswer(request: AnswerRequest): Promise<AnswerResponse> {
    try {
      const response = await apiClient.post<AnswerResponse>(`${this.baseURL}/answer`, request);
      return response;
    } catch (error: any) {
      console.error('Error submitting answer:', error);
      throw error;
    }
  }

  /**
   * Get the next question in the session
   */
  async getNextQuestion(sessionId: number): Promise<Question> {
    try {
      const response = await apiClient.get<Question>(`${this.baseURL}/${sessionId}/question`);
      return response;
    } catch (error: any) {
      console.error('Error getting next question:', error);
      throw error;
    }
  }

  /**
   * Get detailed information about a specific session
   */
  async getSessionDetails(sessionId: number): Promise<SessionDetailResponse> {
    try {
      const response = await apiClient.get<SessionDetailResponse>(`${this.baseURL}/${sessionId}`);
      return response;
    } catch (error: any) {
      console.error('Error getting session details:', error);
      throw error;
    }
  }

  /**
   * List all interview sessions for the current user
   */
  async listSessions(): Promise<SessionListResponse> {
    try {
      const response = await apiClient.get<SessionListResponse>(`${this.baseURL}/sessions`);
      return response;
    } catch (error: any) {
      console.error('Error listing sessions:', error);
      throw error;
    }
  }

  /**
   * Complete an interview session and generate final report
   */
  async completeSession(sessionId: number): Promise<SessionCompletionResponse> {
    try {
      const response = await apiClient.post<SessionCompletionResponse>(`${this.baseURL}/${sessionId}/complete`);
      return response;
    } catch (error: any) {
      console.error('Error completing session:', error);
      throw error;
    }
  }

  /**
   * Cancel an active interview session
   * Note: Backend endpoint not implemented yet
   */
  async cancelSession(sessionId: number): Promise<{ message: string }> {
    try {
      // TODO: Backend endpoint /api/v1/interview/{session_id}/cancel needs to be implemented
      throw new Error('Cancel endpoint not implemented in backend');
    } catch (error: any) {
      console.error('Error cancelling session:', error);
      throw error;
    }
  }

  /**
   * Delete an interview session
   */
  async deleteSession(sessionId: number): Promise<{ message: string }> {
    try {
      console.log(`[DELETE] Deleting session ${sessionId} at ${this.baseURL}/${sessionId}`);
      const response = await apiClient.delete<{ message: string }>(`${this.baseURL}/${sessionId}`);
      console.log('[DELETE] Delete response:', response);
      return response;
    } catch (error: any) {
      console.error('[DELETE] Error deleting session:', error);
      console.error('[DELETE] Error response:', error.response);
      throw error;
    }
  }

  /**
   * Get user statistics overview
   * Note: Returns overview stats, not per-session stats
   */
  async getSessionStats(): Promise<any> {
    try {
      const response = await apiClient.get<any>(`${this.baseURL}/stats/overview`);
      return response;
    } catch (error: any) {
      console.error('Error getting session stats:', error);
      throw error;
    }
  }
}

export const interviewService = new InterviewService();
export default interviewService;
