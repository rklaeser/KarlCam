import { initializeApp, getApps, type FirebaseApp } from 'firebase/app';
import { getFirestore, type Firestore } from 'firebase/firestore';

let app: FirebaseApp;
let db: Firestore;

// Firebase config (public information)
const firebaseConfig = {
	projectId: 'karlcam',
	authDomain: 'karlcam.firebaseapp.com'
};

/**
 * Initialize Firebase client SDK
 * Uses singleton pattern to avoid re-initializing
 */
export function getFirebaseApp(): FirebaseApp {
	if (!app && typeof window !== 'undefined') {
		const existingApps = getApps();
		if (existingApps.length > 0) {
			app = existingApps[0];
		} else {
			app = initializeApp(firebaseConfig);
		}
	}
	return app;
}

/**
 * Get Firestore client instance
 * Connects to the karlcam-firestore database
 */
export function getFirestoreClient(): Firestore {
	if (!db && typeof window !== 'undefined') {
		const app = getFirebaseApp();
		// Connect to named database
		db = getFirestore(app, 'karlcam-firestore');
	}
	return db;
}
