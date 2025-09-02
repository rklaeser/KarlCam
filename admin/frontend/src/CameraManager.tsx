import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './CameraManager.css';

interface Camera {
  id: string;
  name: string;
  description: string;
  url: string;
  video_url?: string;
  created_at: string;
}

interface CameraManagerProps {
  isOpen: boolean;
  onClose: () => void;
  apiBase: string;
}

const CameraManager: React.FC<CameraManagerProps> = ({ isOpen, onClose, apiBase }) => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    url: '',
    video_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadCameras();
    }
  }, [isOpen]);

  const loadCameras = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiBase}/api/cameras`);
      setCameras(response.data);
    } catch (error) {
      console.error('Error loading cameras:', error);
      setError('Failed to load cameras');
    } finally {
      setLoading(false);
    }
  };

  const selectCamera = (camera: Camera) => {
    setSelectedCamera(camera);
    setFormData({
      name: camera.name,
      description: camera.description,
      url: camera.url,
      video_url: camera.video_url || ''
    });
    setIsEditing(false);
    setIsCreating(false);
  };

  const startCreate = () => {
    setSelectedCamera(null);
    setIsCreating(true);
    setIsEditing(false);
    setFormData({
      name: '',
      description: '',
      url: '',
      video_url: ''
    });
  };

  const startEdit = () => {
    setIsEditing(true);
    setIsCreating(false);
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setIsCreating(false);
    if (selectedCamera) {
      setFormData({
        name: selectedCamera.name,
        description: selectedCamera.description,
        url: selectedCamera.url,
        video_url: selectedCamera.video_url || ''
      });
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError('');

      if (isCreating) {
        // Create new camera
        const response = await axios.post(`${apiBase}/api/cameras`, formData);
        await loadCameras();
        selectCamera(response.data);
      } else if (isEditing && selectedCamera) {
        // Update existing camera
        await axios.put(`${apiBase}/api/cameras/${selectedCamera.id}`, formData);
        await loadCameras();
        setIsEditing(false);
      }
    } catch (error) {
      console.error('Error saving camera:', error);
      setError('Failed to save camera');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedCamera || !window.confirm(`Delete camera "${selectedCamera.name}"?`)) {
      return;
    }

    try {
      setLoading(true);
      await axios.delete(`${apiBase}/api/cameras/${selectedCamera.id}`);
      setSelectedCamera(null);
      await loadCameras();
    } catch (error) {
      console.error('Error deleting camera:', error);
      setError('Failed to delete camera');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="camera-manager-overlay" onClick={onClose}>
      <div className="camera-manager-modal" onClick={(e) => e.stopPropagation()}>
        <div className="camera-manager-header">
          <h2>Camera Management</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError('')}>×</button>
          </div>
        )}

        <div className="camera-manager-body">
          <div className="camera-list">
            <div className="camera-list-header">
              <h3>Cameras</h3>
              <button className="add-btn" onClick={startCreate}>+ Add Camera</button>
            </div>
            
            {loading && <div className="loading">Loading...</div>}
            
            <div className="camera-items">
              {cameras.map(camera => (
                <div
                  key={camera.id}
                  className={`camera-item ${selectedCamera?.id === camera.id ? 'selected' : ''}`}
                  onClick={() => selectCamera(camera)}
                >
                  <div className="camera-name">{camera.name}</div>
                  <div className="camera-url">{camera.url}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="camera-details">
            {(selectedCamera || isCreating) ? (
              <>
                <h3>{isCreating ? 'New Camera' : selectedCamera?.name}</h3>
                
                <div className="form-group">
                  <label>Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    disabled={!isEditing && !isCreating}
                    placeholder="Camera name"
                  />
                </div>

                <div className="form-group">
                  <label>Image URL</label>
                  <input
                    type="text"
                    value={formData.url}
                    onChange={(e) => setFormData({...formData, url: e.target.value})}
                    disabled={!isEditing && !isCreating}
                    placeholder="https://example.com/camera.jpg"
                  />
                </div>

                <div className="form-group">
                  <label>Video URL (Live Stream)</label>
                  <input
                    type="text"
                    value={formData.video_url}
                    onChange={(e) => setFormData({...formData, video_url: e.target.value})}
                    disabled={!isEditing && !isCreating}
                    placeholder="https://example.com/live-stream"
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    disabled={!isEditing && !isCreating}
                    placeholder="Camera description"
                    rows={3}
                  />
                </div>

                {selectedCamera && !isCreating && (
                  <div className="form-info">
                    <small>Created: {new Date(selectedCamera.created_at).toLocaleString()}</small>
                  </div>
                )}

                <div className="camera-actions">
                  {isEditing || isCreating ? (
                    <>
                      <button className="save-btn" onClick={handleSave} disabled={loading}>
                        Save
                      </button>
                      <button className="cancel-btn" onClick={cancelEdit} disabled={loading}>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="edit-btn" onClick={startEdit}>
                        Edit
                      </button>
                      <button className="delete-btn" onClick={handleDelete} disabled={loading}>
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="no-selection">
                Select a camera or create a new one
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraManager;