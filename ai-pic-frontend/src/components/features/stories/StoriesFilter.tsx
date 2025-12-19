"use client";

import { GENRES, STATUSES } from "@/hooks/useStories";

interface StoriesFilterProps {
  selectedGenre: string;
  setSelectedGenre: (genre: string) => void;
  selectedStatus: string;
  setSelectedStatus: (status: string) => void;
}

export function StoriesFilter({
  selectedGenre,
  setSelectedGenre,
  selectedStatus,
  setSelectedStatus,
}: StoriesFilterProps) {
  return (
    <div className="mb-6 flex gap-4 flex-wrap">
      <select
        value={selectedGenre}
        onChange={(e) => setSelectedGenre(e.target.value)}
        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">全部类型</option>
        {GENRES.map((genre) => (
          <option key={genre.value} value={genre.value}>
            {genre.label}
          </option>
        ))}
      </select>

      <select
        value={selectedStatus}
        onChange={(e) => setSelectedStatus(e.target.value)}
        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {STATUSES.map((status) => (
          <option key={status.value} value={status.value}>
            {status.label}
          </option>
        ))}
      </select>
    </div>
  );
}
