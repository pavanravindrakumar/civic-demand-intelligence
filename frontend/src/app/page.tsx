import CopilotChat from "../components/CopilotChat";
import AnalyticsOverview from "../components/AnalyticsOverview";
import HotspotMap from "../components/HotspotMap";
import DemoPanel from "../components/DemoPanel";
import { VillageProvider } from "../components/VillageContext";
import WorkspaceSelection from "../components/WorkspaceSelection";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-slate-100 font-sans text-slate-900">
      {/* Dashboard Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Civic Demand Intelligence</h1>
            <p className="text-xs text-slate-500">Policymaker Dashboard</p>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <VillageProvider>
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main Workspace (Left 3 cols) */}
          <div className="xl:col-span-3 flex flex-col gap-6">
            <AnalyticsOverview />
            <HotspotMap />
            <WorkspaceSelection />
          </div>

          {/* Sidebar (Right 1 col) */}
          <div className="xl:col-span-1 flex flex-col gap-6">
            <CopilotChat />
            <DemoPanel />
          </div>
        </main>
      </VillageProvider>
    </div>
  );
}
