import React, { useState, useRef } from 'react';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FiUpload, FiFile, FiCheckCircle, FiX, FiDownload } from 'react-icons/fi';
import '../styles/UploadCSV.css';

function UploadCSV() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile);
      setResult(null);
    } else {
      toast.error('Please upload a CSV file');
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      const response = await api.post('/upload-csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
      toast.success('File uploaded successfully!');
    } catch (err) {
      toast.error('Upload failed. Check file format and backend connection.');
    } finally {
      setUploading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const sampleCSV = `date,amount,category,payment_mode,description
2026-01-05,450.00,Food,UPI,Groceries from supermarket
2026-01-07,1200.00,Shopping,Credit Card,New headphones
2026-01-10,300.00,Transport,UPI,Cab to office
2026-01-15,2500.00,Bills,Net Banking,Electricity bill
2026-01-18,800.00,Entertainment,Debit Card,Movie and dinner
2026-01-22,150.00,Food,Cash,Street food
2026-01-25,3000.00,Education,Net Banking,Online course subscription`;

  const downloadSample = () => {
    const blob = new Blob([sampleCSV], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_transactions.csv';
    a.click();
    URL.revokeObjectURL(url);
    toast.info('Sample CSV downloaded!');
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Upload CSV</h1>
        <p className="subtitle">Import your transaction data in bulk</p>
      </div>

      <div className="upload-layout">
        {/* Upload Area */}
        <div className="upload-card">
          <div
            className={`drop-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <input
              type="file"
              accept=".csv"
              ref={fileInputRef}
              onChange={handleFileSelect}
              hidden
            />

            {!file ? (
              <>
                <FiUpload size={48} className="upload-icon" />
                <h3>Drag & Drop your CSV file here</h3>
                <p>or click to browse</p>
                <span className="file-hint">Accepts .csv files only</span>
              </>
            ) : (
              <div className="file-preview">
                <FiFile size={40} className="file-icon" />
                <div className="file-details">
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
                <button className="clear-btn" onClick={(e) => { e.stopPropagation(); clearFile(); }}>
                  <FiX />
                </button>
              </div>
            )}
          </div>

          {file && (
            <button
              className="btn btn-primary btn-upload"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? (
                <>
                  <div className="spinner-small"></div> Uploading...
                </>
              ) : (
                <>
                  <FiUpload /> Upload & Process
                </>
              )}
            </button>
          )}

          {/* Result */}
          {result && (
            <div className="upload-result">
              <FiCheckCircle size={24} className="result-icon" />
              <div>
                <h4>Upload Successful!</h4>
                <p>{result.message}</p>
                <p>Total transactions in database: <strong>{result.total_transactions}</strong></p>
              </div>
            </div>
          )}
        </div>

        {/* Format Guide */}
        <div className="format-card">
          <h3>CSV Format Guide</h3>
          <p>Your CSV file should have the following columns:</p>

          <table className="format-table">
            <thead>
              <tr><th>Column</th><th>Type</th><th>Example</th></tr>
            </thead>
            <tbody>
              <tr><td><code>date</code></td><td>Date (YYYY-MM-DD)</td><td>2026-01-15</td></tr>
              <tr><td><code>amount</code></td><td>Number</td><td>1500.00</td></tr>
              <tr><td><code>category</code></td><td>Text</td><td>Food</td></tr>
              <tr><td><code>payment_mode</code></td><td>Text</td><td>UPI</td></tr>
              <tr><td><code>description</code></td><td>Text (optional)</td><td>Grocery shopping</td></tr>
            </tbody>
          </table>

          <h4>Valid Categories:</h4>
          <div className="tags-list">
            {['Food', 'Transport', 'Shopping', 'Bills', 'Entertainment', 'Healthcare', 'Education', 'Other'].map(cat => (
              <span key={cat} className="tag">{cat}</span>
            ))}
          </div>

          <h4>Valid Payment Modes:</h4>
          <div className="tags-list">
            {['Cash', 'UPI', 'Credit Card', 'Debit Card', 'Net Banking'].map(mode => (
              <span key={mode} className="tag tag-blue">{mode}</span>
            ))}
          </div>

          <button className="btn btn-outline btn-sample" onClick={downloadSample}>
            <FiDownload /> Download Sample CSV
          </button>
        </div>
      </div>
    </div>
  );
}

export default UploadCSV;
