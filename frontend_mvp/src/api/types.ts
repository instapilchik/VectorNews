// Auth
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  id: number
  username: string
  display_name: string
  role: 'user' | 'admin'
  is_active: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

// Admin user management
export interface UserCreateRequest {
  username: string
  display_name: string
  password: string
  role: 'user' | 'admin'
}

export interface UserUpdateRequest {
  display_name?: string
  password?: string
  role?: 'user' | 'admin'
  is_active?: boolean
}

// Chat
export interface ChatRequest {
  query: string
  chat_history?: ChatHistoryEntry[]
}

export interface ChatHistoryEntry {
  role: 'user' | 'assistant'
  content: string
}

export interface NewsSourceResponse {
  id: number
  tg_link: string
  summary: string
  source_channel: string
  published_at: string
}

export interface ChatResponse {
  answer: string
  sources: NewsSourceResponse[]
}

// Dashboards
export interface HotTopic {
  title: string
  news_count: number
  news_ids: number[]
}

export interface NewsCard {
  id: number
  title: string
  source_channel: string
  published_at: string
  tg_link: string
  importance_score: number | null
}

// News categories (mirror backend)
export type NewsCategory =
  | 'Геополитика'
  | 'Экономика'
  | 'Сырье'
  | 'Криптовалюты'
  | 'Корпоративное'
  | 'Макроэкономика'
  | 'Общее'

export const NEWS_CATEGORIES: NewsCategory[] = [
  'Геополитика',
  'Экономика',
  'Сырье',
  'Криптовалюты',
  'Корпоративное',
  'Макроэкономика',
  'Общее',
]

// Agent settings
export type InformationStyle = 'краткие сводки' | 'развернутые анализы' | 'только факты'
export type CommunicationTone = 'нейтральный' | 'с эмоциями' | 'технический'
export type AnalysisDepth = 'поверхностно' | 'детально' | 'экспертный уровень'

export interface AgentSettings {
  agent_name: string
  focus_interests: string[]
  information_style: InformationStyle
  communication_tone: CommunicationTone
  analysis_depth: AnalysisDepth
  historical_context_days: number
}

export const INFORMATION_STYLES: { value: InformationStyle; label: string }[] = [
  { value: 'краткие сводки', label: 'Краткие сводки' },
  { value: 'развернутые анализы', label: 'Развёрнутые анализы' },
  { value: 'только факты', label: 'Только факты' },
]

export const COMMUNICATION_TONES: { value: CommunicationTone; label: string }[] = [
  { value: 'нейтральный', label: 'Нейтральный' },
  { value: 'с эмоциями', label: 'С эмоциями' },
  { value: 'технический', label: 'Технический' },
]

export const ANALYSIS_DEPTHS: { value: AnalysisDepth; label: string }[] = [
  { value: 'поверхностно', label: 'Поверхностно' },
  { value: 'детально', label: 'Детально' },
  { value: 'экспертный уровень', label: 'Экспертный уровень' },
]
