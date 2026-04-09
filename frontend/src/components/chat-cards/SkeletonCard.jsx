export default function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden animate-pulse"
      style={{ boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
      {/* Header skeleton */}
      <div className="px-5 py-4 bg-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-300 rounded-full" />
          <div className="space-y-2">
            <div className="h-4 w-32 bg-gray-300 rounded" />
            <div className="h-3 w-20 bg-gray-300 rounded" />
          </div>
        </div>
      </div>
      {/* Body skeleton */}
      <div className="p-5 space-y-3">
        <div className="h-3 w-full bg-gray-100 rounded" />
        <div className="h-3 w-5/6 bg-gray-100 rounded" />
        <div className="h-3 w-4/6 bg-gray-100 rounded" />
        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="h-16 bg-gray-100 rounded-xl" />
          <div className="h-16 bg-gray-100 rounded-xl" />
          <div className="h-16 bg-gray-100 rounded-xl" />
        </div>
      </div>
    </div>
  );
}
