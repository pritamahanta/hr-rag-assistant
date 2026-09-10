import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL;

function DocumentManager() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_URL}/documents/`);

      if (!response.ok) {
        throw new Error("Failed to load documents.");
      }

      const data = await response.json();
      setDocuments(data.documents);
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function handleUpload() {
    if (!file) {
      setStatus("Please choose a file.");
      return;
    }

    setLoading(true);
    setStatus("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/documents/upload`, {
        method: "POST",
        headers: {
          "X-User-Role": "admin",
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed.");
      }

      setStatus(`${data.filename} uploaded successfully.`);
      setFile(null);

      document.getElementById("policy-file-input").value = "";

      await loadDocuments();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(filename) {
    const confirmed = window.confirm(`Delete "${filename}"?`);

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/documents/${encodeURIComponent(filename)}`,
        {
          method: "DELETE",
          headers: {
            "X-User-Role": "admin",
          },
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to delete document.");
      }

      await loadDocuments();
    } catch (error) {
      setStatus(error.message);
    }
  }

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <section className="mt-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900">
        Manage Policies
      </h2>

      <div className="mt-4 flex gap-3">
        <input
          id="policy-file-input"
          type="file"
          accept=".md,.txt,.pdf"
          onChange={(event) => {
            setFile(event.target.files[0] || null);
          }}
          className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900"
        />

        <button
          type="button"
          onClick={handleUpload}
          disabled={loading}
          className="rounded-lg bg-gray-900 px-5 py-2 text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>

      {status && (
        <p className="mt-3 text-sm text-gray-600">
          {status}
        </p>
      )}

      <div className="mt-6">
        <h3 className="font-medium text-gray-900">Uploaded Policies</h3>

        {documents.length === 0 ? (
          <p className="mt-3 text-sm text-gray-500">
            No documents uploaded.
          </p>
        ) : (
          <div className="mt-3 space-y-2">
            {documents.map((document) => (
              <div
                key={document}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3"
              >
                <span className="text-gray-800">{document}</span>

                <button
                  type="button"
                  onClick={() => handleDelete(document)}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-red-600 hover:bg-gray-100"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default DocumentManager;