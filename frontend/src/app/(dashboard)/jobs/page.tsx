"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Briefcase, Plus, RotateCw } from "lucide-react";
import { Header } from "@/components/layout/header";
import { JobProgressCard } from "@/components/jobs/job-progress-card";
import { useDiscoveryJobs, useDiscoveryJob } from "@/hooks/use-jobs";

function JobsContent() {
  const searchParams = useSearchParams();
  const activeJobId = searchParams.get("active");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useDiscoveryJobs(page, 10);
  const { data: activeJob } = useDiscoveryJob(activeJobId || "");

  return (
    <div className="space-y-5 sm:space-y-6 max-w-6xl mx-auto w-full min-w-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <Header
            title="Search &amp; Discovery Jobs"
            subtitle="Track asynchronous lead discovery pipelines, rate limits, and deduplication progress."
          />
        </div>
        <Link
          href="/search"
          className="w-full sm:w-auto px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center justify-center space-x-1.5 shrink-0 min-h-[40px] touch-manipulation"
        >
          <Plus className="w-4 h-4 shrink-0" />
          <span>New Discovery Search</span>
        </Link>
      </div>

      {/* Active Job Highlight Banner if launched just now */}
      {activeJob && (
        <div className="space-y-2">
          <div className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
            <RotateCw className="w-3.5 h-3.5 text-blue-600 animate-spin shrink-0" />
            <span>Active Job in Focus</span>
          </div>
          <JobProgressCard job={activeJob} />
        </div>
      )}

      {/* Jobs List */}
      <div className="space-y-4">
        <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Job History ({data?.total || 0})
        </h2>

        {isLoading ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent mb-2"></div>
            <div>Loading discovery jobs...</div>
          </div>
        ) : data?.items && data.items.length > 0 ? (
          data.items.map((job) => (
            <JobProgressCard key={job.id} job={job} />
          ))
        ) : (
          <div className="bg-white p-8 sm:p-12 rounded-xl border border-slate-200 text-center text-slate-500">
            <Briefcase className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <div className="font-semibold text-sm text-slate-800">No search jobs yet</div>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto mb-4">
              Enter a location and category to launch your first automated lead discovery pipeline.
            </p>
            <Link
              href="/search"
              className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold touch-manipulation"
            >
              Start Search
            </Link>
          </div>
        )}

        {/* Pagination Controls */}
        {data && data.total_pages > 1 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-200 text-xs">
            <div className="text-slate-500 text-center sm:text-left">
              Page {data.page} of {data.total_pages} ({data.total} total jobs)
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 font-medium transition touch-manipulation"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page >= data.total_pages}
                className="px-3 py-1.5 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 font-medium transition touch-manipulation"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function JobsPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-xs text-slate-400">Loading jobs...</div>}>
      <JobsContent />
    </Suspense>
  );
}
