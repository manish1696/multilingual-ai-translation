import Header from "./Header";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <main className="bg-white h-screen">
      <div className="h-screen bg-gray-100 overflow-y-auto">
        <Header />
        <div className="max-w-full mx-auto py-6 sm:px-6 lg:px-6">
          <div className="px-4 py-6 sm:px-0 mt-10">{children}</div>
        </div>
      </div>
    </main>
  );
}
