import { useState } from 'react';
import { BugSubmission as BugSubmissionType } from '../types';
import { Upload, FileText, X, AlertCircle, Loader2 } from 'lucide-react';

interface BugSubmissionProps {
  onSubmit: (submission: BugSubmissionType) => void;
  isLoading: boolean;
}

const ALLOWED_EXTENSIONS = ['.txt', '.log', '.md', '.json', '.csv'];

export default function BugSubmission({ onSubmit, isLoading }: BugSubmissionProps) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    stackTrace: '',
    errorLogs: '',
    environment: '',
  });
  const [files, setFiles] = useState<{ name: string; size: number; content: string }[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!form.title.trim()) newErrors.title = 'Bug title is required';
    if (!form.description.trim()) newErrors.description = 'Description is required';
    if (form.title.length < 5) newErrors.title = 'Title must be at least 5 characters';
    if (form.description.length < 10) newErrors.description = 'Description must be at least 10 characters';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    onSubmit({
      ...form,
      files: files.map(f => ({ name: f.name, type: 'text/plain', size: f.size, content: f.content }))
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = e.target.files;
    if (!uploadedFiles) return;

    for (const file of Array.from(uploadedFiles)) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setErrors(prev => ({ ...prev, files: `File type ${ext} not allowed. Use: ${ALLOWED_EXTENSIONS.join(', ')}` }));
        continue;
      }

      const content = await file.text();
      setFiles(prev => [...prev, { name: file.name, size: file.size, content }]);
      setErrors(prev => { const { files, ...rest } = prev; return rest; });
    }
    e.target.value = '';
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-white">Submit Bug Report</h2>
        <p className="text-sm text-gray-400 mt-1">Provide detailed information for AI-powered defect analysis</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Bug Title <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={form.title}
            onChange={e => setForm(prev => ({ ...prev, title: e.target.value }))}
            className={`w-full px-4 py-2.5 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 ${errors.title ? 'border-red-500' : 'border-gray-700'}`}
            placeholder="e.g., NullPointerException in UserService when processing null email"
          />
          {errors.title && <p className="text-xs text-red-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.title}</p>}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Description <span className="text-red-400">*</span>
          </label>
          <textarea
            value={form.description}
            onChange={e => setForm(prev => ({ ...prev, description: e.target.value }))}
            rows={4}
            className={`w-full px-4 py-2.5 bg-gray-900 border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-y ${errors.description ? 'border-red-500' : 'border-gray-700'}`}
            placeholder="Describe the bug behavior, expected vs actual results, and steps to reproduce..."
          />
          {errors.description && <p className="text-xs text-red-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.description}</p>}
        </div>

        {/* Stack Trace */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Stack Trace
          </label>
          <textarea
            value={form.stackTrace}
            onChange={e => setForm(prev => ({ ...prev, stackTrace: e.target.value }))}
            rows={4}
            className="w-full px-4 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-y font-mono text-xs"
            placeholder="java.lang.NullPointerException&#10;  at com.app.service.UserService.processEmail(UserService.java:45)&#10;  at com.app.controller.UserController.handleRequest(UserController.java:23)"
          />
        </div>

        {/* Error Logs */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Error Logs
          </label>
          <textarea
            value={form.errorLogs}
            onChange={e => setForm(prev => ({ ...prev, errorLogs: e.target.value }))}
            rows={4}
            className="w-full px-4 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-y font-mono text-xs"
            placeholder="2024-01-15 10:23:45 ERROR [main] c.a.s.UserService - Failed to process request&#10;2024-01-15 10:23:45 WARN  [main] c.a.c.ConnectionPool - Connection timeout"
          />
        </div>

        {/* Environment */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            Environment Details
          </label>
          <input
            type="text"
            value={form.environment}
            onChange={e => setForm(prev => ({ ...prev, environment: e.target.value }))}
            className="w-full px-4 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            placeholder="e.g., Java 17, Spring Boot 3.2, PostgreSQL 15, Ubuntu 22.04, 16GB RAM"
          />
        </div>

        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1.5">
            File Attachments
          </label>
          <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 text-center hover:border-gray-600 transition-colors">
            <Upload className="w-8 h-8 text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-gray-400 mb-1">Drop files here or click to upload</p>
            <p className="text-xs text-gray-500">Supported: {ALLOWED_EXTENSIONS.join(', ')}</p>
            <input
              type="file"
              multiple
              accept={ALLOWED_EXTENSIONS.join(',')}
              onChange={handleFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              style={{ position: 'relative' }}
            />
          </div>
          {errors.files && <p className="text-xs text-red-400 mt-1 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.files}</p>}

          {files.length > 0 && (
            <div className="mt-3 space-y-2">
              {files.map((file, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-gray-800 rounded-lg border border-gray-700">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-400" />
                    <span className="text-sm text-white">{file.name}</span>
                    <span className="text-xs text-gray-500">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button onClick={() => removeFile(i)} className="text-gray-500 hover:text-red-400">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="flex items-center gap-3 pt-4 border-t border-gray-800">
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Submitting...</>
            ) : (
              'Submit Bug Report'
            )}
          </button>
          <button
            type="button"
            onClick={() => setForm({ title: '', description: '', stackTrace: '', errorLogs: '', environment: '' })}
            className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition-colors"
          >
            Clear Form
          </button>
        </div>
      </form>
    </div>
  );
}
