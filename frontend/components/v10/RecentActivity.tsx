"use client";

interface RecentActivityItem {
  id: string;
  message: string;
  time: string;
}

interface RecentActivityProps {
  activities: RecentActivityItem[];
  loading?: boolean;
}

export default function RecentActivity({
  activities,
  loading = false,
}: RecentActivityProps) {
  if (loading && activities.length === 0) {
    return (
      <div className="mt-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">최근 활동</h3>
        <div className="flex flex-col gap-3">
          {[1, 2].map((i) => (
            <div key={i} className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex flex-col items-start gap-2">
              <div className="h-3.5 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 bg-[length:200%_100%] animate-loading rounded w-[80%]" />
              <div className="h-3.5 bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 bg-[length:200%_100%] animate-loading rounded w-[40%]" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">최근 활동</h3>
      <div className="flex flex-col gap-3">
        {activities.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>최근 활동이 없습니다</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div key={activity.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex justify-between items-center transition-all hover:bg-gray-100 hover:border-gray-300">
              <p className="text-sm text-gray-800 font-medium">{activity.message}</p>
              <span className="text-xs text-gray-500">{activity.time}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
