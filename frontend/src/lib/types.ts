export interface Video {
  id: string;
  youtube_url: string;
  title?: string;
  duration_seconds?: number;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  clips?: Clip[];
}

export interface Clip {
  id: string;
  clip_index: number;
  start_time: number;
  end_time: number;
  duration: number;
  virality_score?: number;
  hook_text?: string;
  caption?: string;
  hashtags?: string[];
  mood?: string;
  output_path?: string;
  tiktok_url?: string;
  status: string;
}

export interface PipelineStatus {
  video_id: string;
  status: string;
  progress: number;
  current_stage?: string;
  error_message?: string;
  clips_count: number;
}
