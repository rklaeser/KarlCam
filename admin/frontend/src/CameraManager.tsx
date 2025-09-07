import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './CameraManager.css';

interface Camera {
  id: string;
  name: string;
  description: string;
  url: string;
  video_url?: string;
  latitude: number;
  longitude: number;
  active: boolean;
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
    video_url: '',
    latitude: 37.7749,
    longitude: -122.4194,
    active: true
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
      video_url: camera.video_url || '',
      latitude: camera.latitude,
      longitude: camera.longitude,
      active: camera.active
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
      video_url: '',
      latitude: 37.7749,
      longitude: -122.4194,
      active: true
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
        video_url: selectedCamera.video_url || '',
        latitude: selectedCamera.latitude,
        longitude: selectedCamera.longitude,
        active: selectedCamera.active
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

  const handleToggleActive = async () => {
    if (!selectedCamera) return;

    try {
      setLoading(true);
      const response = await axios.patch(`${apiBase}/api/cameras/${selectedCamera.id}/toggle-active`);
      await loadCameras();
      // Update selected camera with new active status
      const updatedCamera = cameras.find(c => c.id === selectedCamera.id);
      if (updatedCamera) {
        selectCamera(updatedCamera);
      }
    } catch (error) {
      console.error('Error toggling camera active status:', error);
      setError('Failed to toggle camera active status');
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
                  className={`camera-item ${selectedCamera?.id === camera.id ? 'selected' : ''} ${!camera.active ? 'inactive' : ''}`}
                  onClick={() => selectCamera(camera)}
                >
                  <div className="camera-name">
                    {camera.name}
                    {!camera.active && <span className="inactive-badge">Inactive</span>}
                  </div>
                  <div className="camera-url">{camera.url}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="camera-details">
            {(selectedCamera || isCreating) ? (
              <>
                <h3>
                  {isCreating ? 'New Camera' : selectedCamera?.name}
                  {selectedCamera && !selectedCamera.active && 
                    <span className="inactive-indicator"> (Inactive)</span>
                  }
                </h3>
                
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
                  <label>Latitude</label>
                  <input
                    type="number"
                    value={formData.latitude}
                    onChange={(e) => setFormData({...formData, latitude: parseFloat(e.target.value)})}
                    disabled={!isEditing && !isCreating}
                    placeholder="37.7749"
                    step="0.0001"
                  />
                </div>

                <div className="form-group">
                  <label>Longitude</label>
                  <input
                    type="number"
                    value={formData.longitude}
                    onChange={(e) => setFormData({...formData, longitude: parseFloat(e.target.value)})}
                    disabled={!isEditing && !isCreating}
                    placeholder="-122.4194"
                    step="0.0001"
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

                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.active}
                      onChange={(e) => setFormData({...formData, active: e.target.checked})}
                      disabled={!isEditing && !isCreating}
                    />
                    Active (Camera will be included in image collection)
                  </label>
                </div>

                {selectedCamera && !isCreating && (
                  <div className="form-info">
                    <small>Created: {new Date(selectedCamera.created_at).toLocaleString()}</small>
                    <small>Status: {selectedCamera.active ? 'Active' : 'Inactive'}</small>
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
                      <button 
                        className={`toggle-btn ${selectedCamera?.active ? 'deactivate' : 'activate'}`} 
                        onClick={handleToggleActive} 
                        disabled={loading}
                      >
                        {selectedCamera?.active ? 'Deactivate' : 'Activate'}
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