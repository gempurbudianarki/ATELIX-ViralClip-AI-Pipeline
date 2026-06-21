import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Video as VideoIcon,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  Trash2,
  ExternalLink,
  Sparkles,
  Globe,
} from "lucide-react";
import { fetchVideos, createVideo, deleteVideo } from "../lib/api";
import type { Video } from "../lib/types";

const statusConfig: Record<
  string,
  { icon: typeof Clock; color: string; bg: string; label: string }
> = {
  pending: {
    icon: Clock,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    label: "Pending",
  },
  downloading: {
    icon: Loader2,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    label: "Downloading",
  },
  transcribing: {
    icon: Loader2,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    label: "Transcribing",
  },
  analyzing: {
    icon: Loader2,
    color: "text-violet-400",
    bg: "bg-violet-500/10",
    label: "Analyzing",
  },
  editing: {
    icon: Loader2,
    color: "text-pink-400",
    bg: "bg-pink-500/10",
    label: "Editing",
  },
  rendering: {
    icon: Loader2,
    color: "text-orange-400",
    bg: "bg-orange-500/10",
    label: "Rendering",
  },
  publishing: {
    icon: Loader2,
    color: "text-green-400",
    bg: "bg-green-500/10",
    label: "Publishing",
  },
  completed: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    label: "Complete",
  },
  failed: {
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-500/10",
    label: "Failed",
  },
};

const inProgressStatuses = [
  "pending",
  "downloading",
  "transcribing",
  "analyzing",
  "editing",
  "rendering",
  "publishing",
];

function formatDuration(seconds?: number): string {
  if (!seconds) return "--:--";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function Dashboard() {
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState("auto");
  const queryClient = useQueryClient();

  const { data: videos = [], isLoading } = useQuery({
    queryKey: ["videos"],
    queryFn: () => fetchVideos(),
    refetchInterval: 5000,
  });

  const createMutation = useMutation({
    mutationFn: ({ youtubeUrl, lang }: { youtubeUrl: string; lang: string }) =>
      createVideo(youtubeUrl, lang),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["videos"] });
      setUrl("");
      setLanguage("auto");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (videoId: string) => deleteVideo(videoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["videos"] });
    },
  });

  const activeJobs = videos.filter((v) =>
    inProgressStatuses.includes(v.status)
  ).length;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    let normalizedUrl = url.trim();
    if (normalizedUrl.includes("youtube.com/watch")) {
      const u = new URL(normalizedUrl);
      normalizedUrl = `https://www.youtube.com/watch?v=${u.searchParams.get("v")}`;
    } else if (normalizedUrl.includes("youtu.be/")) {
      const id = normalizedUrl.split("youtu.be/")[1]?.split("?")[0];
      normalizedUrl = `https://www.youtube.com/watch?v=${id}`;
    }

    createMutation.mutate({ youtubeUrl: normalizedUrl, lang: language });
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            ViralClip Pipeline
          </h1>
          <p className="text-zinc-400 mt-1 text-sm">
            Transform long-form YouTube videos into viral short-form content
          </p>
        </div>
        {activeJobs > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            {activeJobs} job{activeJobs > 1 ? "s" : ""} running
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 md:space-y-0 md:flex md:gap-3">
        <div className="relative flex-1">
          <VideoIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste YouTube URL here... https://www.youtube.com/watch?v=..."
            className="w-full pl-10 pr-4 py-3 bg-zinc-900 border border-zinc-700 rounded-xl text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500 transition-colors text-sm"
          />
        </div>
        <div className="flex gap-3 shrink-0">
          <div className="relative">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="pl-4 pr-10 py-3 bg-zinc-900 border border-zinc-700 rounded-xl text-zinc-300 focus:outline-none focus:border-violet-500 transition-colors text-sm cursor-pointer appearance-none min-w-[180px]"
            >
              <option value="auto">🌐 Auto Detect</option>
              <option value="id">🇮🇩 Indonesian</option>
              <option value="en">🇺🇸 English</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-zinc-500">
              <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
              </svg>
            </div>
          </div>
          <button
            type="submit"
            disabled={!url.trim() || createMutation.isPending}
            className="px-6 py-3 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-xl font-medium text-sm transition-all flex items-center gap-2 disabled:cursor-not-allowed"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Clips
              </>
            )}
          </button>
        </div>
      </form>

      {createMutation.isError && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
          {(createMutation.error as Error)?.message || "Failed to create job"}
        </div>
      )}

      <div>
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-600" />
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-20">
            <VideoIcon className="w-12 h-12 text-zinc-800 mx-auto mb-4" />
            <h3 className="text-zinc-500 font-medium">No videos yet</h3>
            <p className="text-zinc-600 text-sm mt-1">
              Paste a YouTube URL above to start generating viral clips
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function VideoCard({
  video,
  onDelete,
}: {
  video: Video;
  onDelete: (id: string) => void;
}) {
  const config = statusConfig[video.status] || statusConfig.pending;
  const StatusIcon = config.icon;
  const isInProgress = inProgressStatuses.includes(video.status);

  return (
    <div className="group bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 rounded-xl p-4 transition-all">
      <div className="flex items-center justify-between gap-4">
        <Link
          to={`/video/${video.id}`}
          className="flex items-center gap-4 flex-1 min-w-0"
        >
          <div className={`p-2 rounded-lg ${config.bg} shrink-0`}>
            <StatusIcon
              className={`w-5 h-5 ${config.color} ${isInProgress ? "animate-spin" : ""}`}
            />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-medium truncate">
                {video.title || "Processing..."}
              </h3>
              <ExternalLink className="w-3 h-3 text-zinc-600 shrink-0" />
            </div>
            <div className="flex items-center gap-3 text-xs text-zinc-500 mt-1">
              <span>{formatDuration(video.duration_seconds)}</span>
              <span>·</span>
              <span>{formatDate(video.created_at)}</span>
              {video.clips && video.clips.length > 0 && (
                <>
                  <span>·</span>
                  <span>{video.clips.length} clips</span>
                </>
              )}
            </div>
          </div>
        </Link>

        <div className="flex items-center gap-3 shrink-0">
          <span
            className={`text-xs px-2.5 py-1 rounded-full font-medium ${config.bg} ${config.color}`}
          >
            {config.label}
          </span>
          <button
            onClick={(e) => {
              e.preventDefault();
              onDelete(video.id);
            }}
            className="p-2 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {video.error_message && (
        <div className="mt-3 p-3 bg-red-500/5 border border-red-500/10 rounded-lg text-red-400 text-xs">
          {video.error_message}
        </div>
      )}
    </div>
  );
}
