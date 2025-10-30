// KarlCam Types

export interface Webcam {
	id: string;
	name: string;
	latitude: number;
	longitude: number;
	url: string;
	video_url?: string;
	description?: string;
	active: boolean;
}

export interface CameraLabel {
	camera_id: string;
	camera_name: string;
	timestamp: Date;
	image_url: string;
	fog_score?: number;
	fog_level?: string;
	confidence?: number;
	reasoning?: string;
	weather_conditions?: string[];
	latitude?: number;
	longitude?: number;
	source_environment?: string;
	labeler_name?: string;
	description?: string;
}

export interface LabelResponse {
	source: 'firestore' | 'on-demand';
	label: CameraLabel;
}
