import { Suspense } from "react";
import FilterBar from "./components/FilterBar";

interface Company {
  id: string;
  name: string;
  logo_url: string | null;
  industry: string;
  location: string;
}

interface Internship {
  id: string;
  title: string;
  slug: string;
  company: Company;
  location: string;
  work_type: string;
  work_type_display: string;
  education_level_display: string;
  salary_range: string;
  source: string;
  source_url: string;
  posted_at: string | null;
  deadline: string | null;
  relevant_majors: string[];
}

interface ApiResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Internship[];
}

async function getInternships(params: Record<string, string>): Promise<ApiResponse> {
  const query = new URLSearchParams(params).toString();
  const url = `http://backend:8000/api/v1/internships/${query ? "?" + query : ""}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Gagal mengambil data");
  return res.json();
}

function WorkTypeBadge({ type, label }: { type: string; label: string }) {
  const colors: Record<string, string> = {
    remote: "bg-green-100 text-green-800",
    hybrid: "bg-blue-100 text-blue-800",
    onsite: "bg-orange-100 text-orange-800",
    unknown: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`text-xs px-2 py-1 rounded-full font-medium ${colors[type] ?? colors.unknown}`}>
      {label}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  const colors: Record<string, string> = {
    glints: "bg-purple-100 text-purple-800",
    jobstreet: "bg-yellow-100 text-yellow-800",
    indeed: "bg-sky-100 text-sky-800",
  };
  return (
    <span className={`text-xs px-2 py-1 rounded-full font-medium ${colors[source] ?? "bg-gray-100 text-gray-600"}`}>
      {source.charAt(0).toUpperCase() + source.slice(1)}
    </span>
  );
}

function InternshipCard({ internship }: { internship: Internship }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-500 font-medium truncate">{internship.company.name}</p>
          <h2 className="text-base font-semibold text-gray-900 mt-0.5 leading-snug line-clamp-2">
            {internship.title}
          </h2>
        </div>
        <SourceBadge source={internship.source} />
      </div>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        {internship.location && (
          <span className="text-sm text-gray-500 truncate">
            {internship.location}
          </span>
        )}
        <WorkTypeBadge type={internship.work_type} label={internship.work_type_display} />
      </div>
      <p className="text-sm text-emerald-600 font-medium mb-3">{internship.salary_range}</p>
      {internship.relevant_majors.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {internship.relevant_majors.slice(0, 3).map((major) => (
            <span key={major} className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded">
              {major}
            </span>
          ))}
        </div>
      )}
      <div className="mt-auto">
        
          <a href={internship.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full text-center text-sm font-medium bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Lihat Lowongan
        </a>
      </div>
    </div>
  );
}

interface PageProps {
  searchParams: Promise<Record<string, string>>;
}

export default async function HomePage({ searchParams }: PageProps) {
  const params = await searchParams;

  const apiParams: Record<string, string> = {};
  if (params.search) apiParams.search = params.search;
  if (params.work_type) apiParams.work_type = params.work_type;
  if (params.education) apiParams.education = params.education;
  if (params.source) apiParams.source = params.source;
  if (params.page) apiParams.page = params.page;

  let data: ApiResponse;
  try {
    data = await getInternships(apiParams);
  } catch (error) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-red-500">Gagal memuat data. Pastikan backend berjalan.</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="bg-indigo-600 text-white py-10 px-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-1">Agregator Magang IT</h1>
          <p className="text-indigo-200">
            Lowongan magang untuk mahasiswa Teknologi Informasi dan jurusan serumpun
          </p>
        </div>
      </div>

      <Suspense>
        <FilterBar totalCount={data.count} />
      </Suspense>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {data.results.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-400 text-lg">Tidak ada lowongan yang sesuai filter.</p>
            <a href="/" className="text-indigo-600 text-sm mt-2 inline-block hover:underline">
              Reset filter
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.results.map((internship) => (
              <InternshipCard key={internship.id} internship={internship} />
            ))}
          </div>
        )}

        {/* Pagination */}
        <div className="flex justify-center gap-3 mt-8">
          {params.page && parseInt(params.page) > 1 && (
            
              <a href={`?${new URLSearchParams({ ...apiParams, page: String(parseInt(params.page) - 1) })}`}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              Sebelumnya
            </a>
          )}
          {data.next && (
            
              <a href={`?${new URLSearchParams({ ...apiParams, page: String(parseInt(params.page ?? "1") + 1) })}`}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
            >
              Berikutnya
            </a>
          )}
        </div>
      </div>
    </main>
  );
}