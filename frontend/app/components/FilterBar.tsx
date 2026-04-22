"use client";

import { useState, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

export default function FilterBar({ totalCount }: { totalCount: number }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [search, setSearch] = useState(searchParams.get("search") ?? "");

  const updateFilter = useCallback(
    (key: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
      params.delete("page");
      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams]
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilter("search", search);
  };

  const handleReset = () => {
    setSearch("");
    router.push(pathname);
  };

  const activeFilters =
    searchParams.has("search") ||
    searchParams.has("work_type") ||
    searchParams.has("education") ||
    searchParams.has("location");

  return (
    <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          {/* Search input */}
          <div className="flex flex-1 gap-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari judul, perusahaan, atau lokasi..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              Cari
            </button>
          </div>

          {/* Filter: Tipe Kerja */}
          <select
            value={searchParams.get("work_type") ?? ""}
            onChange={(e) => updateFilter("work_type", e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="">Semua Tipe Kerja</option>
            <option value="onsite">On-site</option>
            <option value="remote">Remote</option>
            <option value="hybrid">Hybrid</option>
          </select>

          {/* Filter: Jenjang Pendidikan */}
          <select
            value={searchParams.get("education") ?? ""}
            onChange={(e) => updateFilter("education", e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="">Semua Jenjang</option>
            <option value="d3">D3</option>
            <option value="d4">D4</option>
            <option value="s1">S1</option>
          </select>

          {/* Filter: Sumber */}
          <select
            value={searchParams.get("source") ?? ""}
            onChange={(e) => updateFilter("source", e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          >
            <option value="">Semua Sumber</option>
            <option value="glints">Glints</option>
            <option value="jobstreet">Jobstreet</option>
            <option value="indeed">Indeed</option>
          </select>

          {/* Tombol reset */}
          {activeFilters && (
            <button
              type="button"
              onClick={handleReset}
              className="text-sm text-red-500 hover:text-red-700 px-2 whitespace-nowrap"
            >
              Reset Filter
            </button>
          )}
        </form>

        {/* Info hasil filter */}
        <p className="text-xs text-gray-400 mt-2">
          {totalCount} lowongan ditemukan
          {searchParams.get("search") && (
            <span> untuk <strong>{searchParams.get("search")}</strong></span>
          )}
        </p>
      </div>
    </div>
  );
}