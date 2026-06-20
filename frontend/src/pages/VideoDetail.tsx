import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Loader2,
  Clock,
  AlertCircle,
  Send,
  Film,
  TrendingUp,
  ExternalLink,
} from "lucide-react";
import { fetchVideo, fetchClips, publishClip } from "../lib/api";
import type { Clip } from "../lib/types";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const moodEmojis: Record<string, string> = {
  inspirational: "✨",
  humorous: "😂",
  controversial: "🔥",
  educational: "📚",
  emotional: "😢",
  shocking: "😱",
  tense: "😰",
  neutral: "💬",
};

const moodColors: Record<string, string> = {
  inspirational: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  humorous: "text-green-400 bg-green-500/10 border-green-500/20",
  controversial: "text-red-400 bg-red-500/10 border-red-500/20",
  educational: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
  emotional: "text-pink-400 bg-pink-500/10 border-pink-500/20",
  shocking: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  tense: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  neutral: "text-zinc-400 bg-zinc-500/10 border-zinc-500/20",
};

export function VideoDetail() {
  const { videoId } = useParams<{ videoId: string }>();
  const queryClient = useQueryClient();

  const { data: video, isLoading } = useQuery({
    queryKey: ["video", videoId],
    queryFn: () => fetchVideo(videoId!),
    enabled: !!videoId,
    refetchInterval: 3000,
  });

  const { data: clips = [] } = useQuery({
    queryKey: ["clips", videoId],
    queryFn: () => fetchClips(videoId!),
    enabled: !!videoId,
    refetchInterval: video?.status !== "completed" ? 5000 : false,
  });

  const publishMutation = useMutation({
    mutationFn: (clipId: string) => publishClip(clipId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clips", videoId] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-40">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-600" />
      </div>
    );
  }

  if (!video) {
    return (
      <div className="text-center py-40">
        <AlertCircle className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
        <h2 className="text-zinc-400 font-medium">Video not found</h2>
        <Link
          to="/"
          className="text-violet-400 text-sm mt-2 inline-block hover:underline"
        >
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="p-2 rounded-lg hover:bg-zinc-800 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-xl font-bold truncate">
            {video.title || "Untitled Video"}
          </h1>
          <a
            href={video.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors truncate block"
          >
            {video.youtube_url}
            <ExternalLink className="w-3 h-3 inline ml-1" />
          </a>
        </div>
        <StatusBadge status={video.status} />
      </div>

      {video.error_message && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 inline mr-2" />
          {video.error_message}
        </div>
      )}

      {clips.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Film className="w-5 h-5 text-violet-400" />
            <h2 className="font-semibold">
              Viral Clips ({clips.length})
            </h2>
          </div>

          <div className="space-y-4">
            {clips.map((clip) => (
              <ClipCard
                key={clip.id}
                clip={clip}
                onPublish={
                  clip.status === "completed"
                    ? () => publishMutation.mutate(clip.id)
                    : undefined
                }
                isPublishing={publishMutation.isPending}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    pending: { color: "text-amber-400 bg-amber-500/10 border-amber-500/20", label: "Pending" },
    downloading: { color: "text-blue-400 bg-blue-500/10 border-blue-500/20", label: "Downloading" },
    transcribing: { color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20", label: "Transcribing" },
    analyzing: { color: "text-violet-400 bg-violet-500/10 border-violet-500/20", label: "Analyzing" },
    editing: { color: "text-pink-400 bg-pink-500/10 border-pink-500/20", label: "Editing" },
    rendering: { color: "text-orange-400 bg-orange-500/10 border-orange-500/20", label: "Rendering" },
    publishing: { color: "text-green-400 bg-green-500/10 border-green-500/20", label: "Publishing" },
    completed: { color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", label: "Complete" },
    failed: { color: "text-red-400 bg-red-500/10 border-red-500/20", label: "Failed" },
  };

  const c = config[status] || config.pending;

  return (
    <span
      className={`text-xs px-2.5 py-1 rounded-full font-medium border ${c.color}`}
    >
      {c.label}
    </span>
  );
}

function ClipCard({
  clip,
  onPublish,
  isPublishing,
}: {
  clip: Clip;
  onPublish?: () => void;
  isPublishing?: boolean;
}) {
  const mood = clip.mood || "neutral";
  const moji = moodEmojis[mood] || "💬";
  const moodColor =
    moodColors[mood] || moodColors.neutral;

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 rounded-xl overflow-hidden transition-all">
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center shrink-0 text-lg">
              {clip.clip_index}
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                {clip.hook_text && (
                  <p className="font-medium text-sm truncate">
                    {clip.hook_text}
                  </p>
                )}
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-full border ${moodColor}`}
                >
                  {moji} {mood}
                </span>
              </div>

              {clip.caption && (
                <p className="text-xs text-zinc-500 mt-1 line-clamp-2">
                  {clip.caption}
                </p>
              )}

              <div className="flex items-center gap-3 mt-2 text-xs text-zinc-600">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTime(clip.start_time)} – {formatTime(clip.end_time)}{" "}
                  ({Math.round(clip.duration)}s)
                </span>
                {clip.virality_score != null && (
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    {clip.virality_score}% viral
                  </span>
                )}
              </div>

              {clip.hashtags && clip.hashtags.length > 0 && (
                <div className="flex items-center gap-1 mt-2 flex-wrap">
                  {clip.hashtags.slice(0, 8).map((tag) => (
                    <span
                      key={tag}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="shrink-0 flex flex-col items-end gap-2">
            <StatusBadge status={clip.status} />
            {onPublish && (
              <button
                onClick={onPublish}
                disabled={isPublishing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white text-xs rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
              >
                {isPublishing ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Send className="w-3 h-3" />
                )}
                Publish
              </button>
            )}
          </div>
        </div>
      </div>

      {clip.tiktok_url && (
        <div className="px-4 py-2 bg-emerald-500/10 border-t border-emerald-500/20">
          <a
            href={clip.tiktok_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-emerald-400 hover:underline flex items-center gap-1"
          >
            <ExternalLink className="w-3 h-3" />
            View on TikTok
          </a>
        </div>
      )}
    </div>
  );
}
