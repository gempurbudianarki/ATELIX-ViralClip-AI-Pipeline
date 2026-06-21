import { apiClient } from "./client";
import type { Video, PipelineStatus, Clip } from "./types";

export async function fetchVideos(status?: string): Promise<Video[]> {
  const params = status ? { status } : {};
  const res = await apiClient.get<Video[]>("/api/v1/videos/", { params });
  return res.data;
}

export async function fetchVideo(videoId: string): Promise<Video> {
  const res = await apiClient.get<Video>(`/api/v1/videos/${videoId}`);
  return res.data;
}

export async function fetchVideoStatus(videoId: string): Promise<PipelineStatus> {
  const res = await apiClient.get<PipelineStatus>(
    `/api/v1/videos/${videoId}/status`
  );
  return res.data;
}

export async function fetchClips(videoId: string): Promise<Clip[]> {
  const res = await apiClient.get<Clip[]>(`/api/v1/pipeline/clips/${videoId}`);
  return res.data;
}

export async function createVideo(youtubeUrl: string, language?: string): Promise<Video> {
  const res = await apiClient.post<Video>("/api/v1/videos/", {
    youtube_url: youtubeUrl,
    language: language === "auto" ? null : language,
  });
  return res.data;
}

export async function publishClip(clipId: string): Promise<void> {
  await apiClient.post("/api/v1/pipeline/publish", { clip_id: clipId });
}

export async function deleteVideo(videoId: string): Promise<void> {
  await apiClient.delete(`/api/v1/videos/${videoId}`);
}
