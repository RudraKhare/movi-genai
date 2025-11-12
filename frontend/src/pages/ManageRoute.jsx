import { useEffect, useState } from "react";
import Header from "../components/Header";
import StopList from "../components/StopList";
import PathCreator from "../components/PathCreator";
import RouteCreator from "../components/RouteCreator";
import { getManageContext } from "../api";

export default function ManageRoute() {
  const [data, setData] = useState({ stops: [], paths: [], routes: [] });
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await getManageContext();
      setData(res.data);
    } catch (err) {
      console.error("Failed to load context:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header summary={{ total_stops: data.stops?.length || 0, total_paths: data.paths?.length || 0, total_routes: data.routes?.length || 0 }} onRefresh={loadData} loading={loading} />
      <div className="p-6 max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          Manage Routes, Paths & Stops
        </h1>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading context...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StopList stops={data.stops || []} onRefresh={loadData} />
            <PathCreator
              stops={data.stops || []}
              paths={data.paths || []}
              onRefresh={loadData}
            />
            <RouteCreator
              paths={data.paths || []}
              routes={data.routes || []}
              onRefresh={loadData}
            />
          </div>
        )}
      </div>
    </div>
  );
}

