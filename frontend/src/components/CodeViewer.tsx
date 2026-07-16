import { useState, useEffect } from "react";
import { FolderCode, FileText, Check, Copy, Download } from "lucide-react";

interface PythonFile {
  path: string;
  name: string;
  content: string;
}

export default function CodeViewer() {
  const [files, setFiles] = useState<PythonFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<PythonFile | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/files")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setFiles(data);
          // Default select room.py or main.py
          const defaultFile = data.find((f) => f.name === "room.py") || data[0];
          setSelectedFile(defaultFile);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load files from server: ", err);
        setLoading(false);
      });
  }, []);

  const handleCopy = () => {
    if (!selectedFile) return;
    navigator.clipboard.writeText(selectedFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadFile = () => {
    if (!selectedFile) return;
    const blob = new Blob([selectedFile.content], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", selectedFile.name);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <div className="w-full flex items-center justify-center p-10 bg-[#0f172a]/70 border border-slate-800 rounded-xl">
        <span className="text-cyan-400 font-mono text-xs animate-pulse">Scanning Python workspace tree...</span>
      </div>
    );
  }

  return (
    <div className="w-full grid grid-cols-1 md:grid-cols-4 gap-4 bg-[#0f172a]/70 border border-slate-800 rounded-xl p-5 shadow-xl text-xs backdrop-blur-md">
      
      {/* Sidebar: File Tree */}
      <div className="flex flex-col gap-2 border-r border-slate-800/80 pr-4 md:col-span-1">
        <h4 className="font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider mb-2 border-b border-slate-800 pb-1.5">
          <FolderCode className="w-4 h-4 text-cyan-400" />
          Workspace Files
        </h4>
        <div className="flex flex-col gap-1 max-h-[350px] overflow-y-auto pr-1">
          {files.map((file) => (
            <button
              key={file.path}
              onClick={() => setSelectedFile(file)}
              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md text-left transition-all ${
                selectedFile?.path === file.path
                  ? "bg-slate-950/80 border-l-2 border-cyan-500 text-cyan-400 font-bold"
                  : "text-slate-400 hover:bg-slate-950/40 hover:text-slate-200"
              }`}
            >
              <FileText className={`w-3.5 h-3.5 ${selectedFile?.path === file.path ? "text-cyan-400" : "text-slate-500"}`} />
              <div className="truncate flex flex-col">
                <span className="text-slate-200 font-semibold">{file.name}</span>
                <span className="text-[9px] text-slate-500 truncate">{file.path}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Editor Main Code Block */}
      <div className="flex flex-col gap-2 md:col-span-3">
        {selectedFile ? (
          <>
            <div className="flex justify-between items-center bg-slate-950/80 px-4 py-2 border border-slate-800 rounded-t-lg">
              <div className="flex flex-col">
                <span className="text-xs font-mono text-slate-200 font-bold">{selectedFile.name}</span>
                <span className="text-[10px] font-mono text-slate-500">{selectedFile.path}</span>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white transition text-xs font-bold"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? "Copied" : "Copy"}</span>
                </button>
                <button
                  onClick={handleDownloadFile}
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#0f172a] text-cyan-400 border border-cyan-500/30 hover:border-cyan-500/60 transition text-xs font-bold"
                >
                  <Download className="w-3.5 h-3.5 animate-pulse" />
                  <span>Download</span>
                </button>
              </div>
            </div>

            <div className="w-full max-h-[380px] overflow-auto border border-t-0 border-slate-800 bg-slate-950 rounded-b-lg p-4 shadow-inner">
              <pre className="font-mono text-[10.5px] leading-relaxed text-slate-300 whitespace-pre text-left">
                <code>{selectedFile.content}</code>
              </pre>
            </div>
          </>
        ) : (
          <div className="w-full flex items-center justify-center h-[350px] border border-dashed border-slate-800 rounded-lg">
            <span className="text-slate-500 font-mono">Select a file to inspect code.</span>
          </div>
        )}
      </div>

    </div>
  );
}
