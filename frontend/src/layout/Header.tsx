import { useState } from "react";
import { NavLink } from "react-router-dom";
import { Languages, Upload } from "lucide-react";
import UploadModal from "../components/UploadModal";

export default function Header() {
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium px-2 py-1 ${
      isActive
        ? "text-[#5b0428] border-b-2 border-[#5b0428]"
        : "text-gray-700 hover:text-[#5b0428]"
    }`;

  return (
    <div className="bg-white shadow-sm border-b fixed w-full z-10">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#5b0428] text-white"
              aria-label="Multilingual AI"
            >
              <Languages className="h-5 w-5" />
            </div>
            <div className="h-6 w-px bg-gray-300"></div>
            <h1 className="text-lg font-semibold text-[#5b0428] my-2">
              Multilingual AI Translator
            </h1>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <NavLink to="/" end className={navLinkClass}>
              Translate
            </NavLink>
            <NavLink to="/results" className={navLinkClass}>
              Results
            </NavLink>

            <button
              type="button"
              onClick={() => setIsUploadOpen(true)}
              className="flex items-center space-x-1.5 bg-[#5b0428] text-white px-4 py-2 rounded-md hover:bg-[#7b0538] transition-colors text-sm ml-8"
            >
              <Upload className="w-4 h-4" />
              <span>Upload</span>
            </button>
          </div>
        </div>
      </div>

      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
      />
    </div>
  );
}
