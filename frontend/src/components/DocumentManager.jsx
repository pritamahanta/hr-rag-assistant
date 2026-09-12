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

  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <section className="document-panel">
      <h2 className="panel-title">
        Manage Policies
      </h2>

      <div className="upload-row">
        <div className="file-picker">
          <input
            id="policy-file-input"
            type="file"
            accept=".md,.txt,.pdf"
            onChange={(event) => {
              setFile(event.target.files[0] || null);
            }}
            className="file-input"
          />
          <label htmlFor="policy-file-input" className="file-picker-control">
            <span className="file-picker-button">Choose File</span>
            <span className="file-picker-name">{file ? file.name : "No file selected"}</span>
          </label>
          <p className="file-helper">Supported formats: .md, .txt, .pdf <span aria-hidden="true">&#183;</span> Maximum size: 10 MB</p>
        </div>

        <button
          type="button"
          onClick={handleUpload}
          disabled={loading}
          className="upload-button"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>

      {status && (
        <p className="manager-status">
          {status}
        </p>
      )}

      <div className="uploaded-section">
        <h3 className="section-label">Uploaded Policies</h3>

        {documents.length === 0 ? (
          <p className="no-documents">
            No documents uploaded.
          </p>
        ) : (
          <div className="document-list">
            {documents.map((document) => (
              <div
                key={document}
                className="document-row"
              >
                <span className="document-name"><span className="file-mark">FILE</span>{document}</span>

                <button
                  type="button"
                  onClick={() => handleDelete(document)}
                  className="delete-button"
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