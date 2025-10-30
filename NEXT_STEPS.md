# KarlCam SvelteKit Frontend - Next Steps

## Current Status

✅ **Completed:**
- Migrated 21,408 labels from PostgreSQL (staging + production) to Firestore
- Created Firestore database: `karlcam-firestore` in GCP project `karlcam`
- Upgraded GCP project to Firebase (can now use Firebase Console)
- Copied SvelteKit template to `web/frontend-sveltekit/`
- Removed auth and career-related pages/components
- Configured `.env` with Gemini API key

🔨 **In Progress:**
- Setting up SvelteKit frontend for KarlCam

## Firebase Console Access

View your migrated data:
- **Firebase Console**: https://console.firebase.google.com/project/karlcam/firestore/databases/karlcam-firestore/data
- **GCP Console**: https://console.cloud.google.com/firestore/databases/karlcam-firestore/data?project=karlcam

Collections:
- `webcams`: 12 cameras
- `labels`: 21,408 labeled images (tagged with `source_environment: staging/production`)
- `system/status`: Migration metadata

---

## Next Session Plan

### Phase 1: Update Firebase/Firestore Configuration (15 min)

**Files to modify:**

#### 1. `src/lib/firebase.ts` - Remove auth, add Firestore
```typescript
// Current: Has Firebase Auth
// Need: Firestore client connection to karlcam-firestore database

import { initializeApp, getApps, type FirebaseApp } from 'firebase/app';
import { getFirestore, type Firestore } from 'firebase/firestore';
import { PUBLIC_FIREBASE_PROJECT_ID, PUBLIC_FIREBASE_AUTH_DOMAIN } from '$env/static/public';

let app: FirebaseApp;
let db: Firestore;

export function getFirebaseApp(): FirebaseApp {
  if (!app && typeof window !== 'undefined') {
    const existingApps = getApps();
    if (existingApps.length > 0) {
      app = existingApps[0];
    } else {
      app = initializeApp({
        projectId: PUBLIC_FIREBASE_PROJECT_ID,
        authDomain: PUBLIC_FIREBASE_AUTH_DOMAIN
      });
    }
  }
  return app;
}

export function getFirestoreClient(): Firestore {
  if (!db && typeof window !== 'undefined') {
    const app = getFirebaseApp();
    // Connect to named database
    db = getFirestore(app, 'karlcam-firestore');
  }
  return db;
}
```

#### 2. `src/lib/server/firebase.ts` - Create server-side Firebase Admin
```typescript
// New file - Server-side Firebase Admin SDK
import admin from 'firebase-admin';
import { getFirestore, type Firestore } from 'firebase-admin/firestore';

let db: Firestore | null = null;

export function getFirestoreAdmin(): Firestore {
  if (!db) {
    // Initialize Firebase Admin with default credentials
    if (admin.apps.length === 0) {
      admin.initializeApp({
        projectId: 'karlcam'
      });
    }
    // Connect to karlcam-firestore database
    db = getFirestore('karlcam-firestore');
  }
  return db;
}
```

#### 3. Remove `src/lib/server/auth.ts` (no longer needed)
```bash
rm src/lib/server/auth.ts
```

---

### Phase 2: Create Data Loading Logic (20 min)

#### 4. `src/lib/server/firestore.ts` - Firestore query utilities
```typescript
// Server-side Firestore utilities for KarlCam
import { getFirestoreAdmin } from './firebase';

export interface Webcam {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  url: string;
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
}

/**
 * Get all active webcams
 */
export async function getWebcams(): Promise<Webcam[]> {
  const db = getFirestoreAdmin();
  const snapshot = await db.collection('webcams')
    .where('active', '==', true)
    .get();

  return snapshot.docs.map(doc => ({
    id: doc.id,
    name: doc.data().name,
    latitude: doc.data().latitude,
    longitude: doc.data().longitude,
    url: doc.data().url,
    active: doc.data().active
  }));
}

/**
 * Get latest label for a camera (within maxAgeMinutes)
 * Returns null if no recent label found
 */
export async function getLatestLabel(
  cameraId: string,
  maxAgeMinutes: number = 30
): Promise<CameraLabel | null> {
  const db = getFirestoreAdmin();
  const cutoffTime = new Date(Date.now() - maxAgeMinutes * 60 * 1000);

  const snapshot = await db.collection('labels')
    .where('camera_id', '==', cameraId)
    .where('timestamp', '>=', cutoffTime)
    .orderBy('timestamp', 'desc')
    .limit(1)
    .get();

  if (snapshot.empty) {
    return null;
  }

  const data = snapshot.docs[0].data();
  return {
    camera_id: data.camera_id,
    camera_name: data.camera_name,
    timestamp: data.timestamp.toDate(),
    image_url: data.image_url,
    fog_score: data.fog_score,
    fog_level: data.fog_level,
    confidence: data.confidence,
    reasoning: data.reasoning,
    weather_conditions: data.weather_conditions,
    latitude: data.latitude,
    longitude: data.longitude,
    source_environment: data.source_environment,
    labeler_name: data.labeler_name
  };
}

/**
 * Save a new label to Firestore
 */
export async function saveLabel(label: Omit<CameraLabel, 'timestamp'> & { timestamp?: Date }): Promise<void> {
  const db = getFirestoreAdmin();

  const docData = {
    ...label,
    timestamp: label.timestamp || new Date(),
    labeled_at: new Date()
  };

  await db.collection('labels').add(docData);
}
```

---

### Phase 3: Create On-Demand Labeling API (25 min)

#### 5. `src/routes/api/label/[cameraId]/+server.ts` - On-demand Gemini labeling
```typescript
// API endpoint: GET /api/label/{cameraId}
// Checks Firestore for recent label (< 30 min)
// If stale or missing: fetch image, label with Gemini, save to Firestore
// Returns: { source: 'firestore' | 'on-demand', label: CameraLabel }

import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFirestoreAdmin, getLatestLabel, saveLabel } from '$lib/server/firestore';
import { GEMINI_API_KEY } from '$env/static/private';

interface GeminiResponse {
  fog_score: number;
  fog_level: string;
  confidence: number;
  reasoning: string;
  weather_conditions: string[];
}

async function labelImageWithGemini(imageUrl: string, cameraName: string): Promise<GeminiResponse> {
  // 1. Fetch image from URL
  const imageResponse = await fetch(imageUrl);
  if (!imageResponse.ok) {
    throw new Error(`Failed to fetch image: ${imageResponse.statusText}`);
  }

  // 2. Convert to base64
  const imageBuffer = await imageResponse.arrayBuffer();
  const base64Image = Buffer.from(imageBuffer).toString('base64');

  // 3. Call Gemini API
  const geminiResponse = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GEMINI_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{
          parts: [
            {
              text: `Analyze this webcam image from ${cameraName} in San Francisco for fog conditions.

Return JSON with:
- fog_score: 0-100 (0=clear, 100=very heavy fog)
- fog_level: "Clear", "Light Fog", "Moderate Fog", "Heavy Fog", or "Very Heavy Fog"
- confidence: 0.0-1.0
- reasoning: Brief explanation
- weather_conditions: Array like ["fog", "overcast", "clear"]

Focus on visibility and atmospheric haze.`
            },
            {
              inline_data: {
                mime_type: 'image/jpeg',
                data: base64Image
              }
            }
          ]
        }]
      })
    }
  );

  if (!geminiResponse.ok) {
    throw new Error(`Gemini API error: ${geminiResponse.statusText}`);
  }

  const result = await geminiResponse.json();
  const text = result.candidates[0].content.parts[0].text;

  // Extract JSON from response
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('Failed to parse Gemini response');
  }

  return JSON.parse(jsonMatch[0]);
}

export const GET: RequestHandler = async ({ params }) => {
  const { cameraId } = params;

  try {
    // Check for recent label
    const recentLabel = await getLatestLabel(cameraId, 30);
    if (recentLabel) {
      return json({
        source: 'firestore',
        label: recentLabel
      });
    }

    // No recent label - generate new one
    const db = getFirestoreAdmin();
    const webcamDoc = await db.collection('webcams').doc(cameraId).get();

    if (!webcamDoc.exists) {
      return json({ error: 'Camera not found' }, { status: 404 });
    }

    const webcam = webcamDoc.data()!;

    // Label image with Gemini
    const geminiResult = await labelImageWithGemini(webcam.url, webcam.name);

    // Create label
    const label = {
      camera_id: cameraId,
      camera_name: webcam.name,
      image_url: webcam.url,
      fog_score: geminiResult.fog_score,
      fog_level: geminiResult.fog_level,
      confidence: geminiResult.confidence,
      reasoning: geminiResult.reasoning,
      weather_conditions: geminiResult.weather_conditions,
      latitude: webcam.latitude,
      longitude: webcam.longitude,
      labeler_name: 'gemini-2.0-flash-exp',
      source_environment: 'on-demand'
    };

    // Save to Firestore
    await saveLabel(label);

    return json({
      source: 'on-demand',
      label: {
        ...label,
        timestamp: new Date()
      }
    });
  } catch (error) {
    console.error('Error labeling image:', error);
    return json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
};
```

---

### Phase 4: Build Main UI (30 min)

#### 6. `src/routes/+page.server.ts` - Server-side data loading
```typescript
import type { PageServerLoad } from './$types';
import { getWebcams, getLatestLabel } from '$lib/server/firestore';

export const load: PageServerLoad = async () => {
  try {
    // Get all active webcams
    const webcams = await getWebcams();

    // Get latest labels for each camera
    const camerasWithLabels = await Promise.all(
      webcams.map(async (webcam) => {
        const label = await getLatestLabel(webcam.id, 30);
        return {
          ...webcam,
          label: label ? {
            ...label,
            timestamp: label.timestamp.toISOString()
          } : null,
          needsRefresh: !label
        };
      })
    );

    return {
      cameras: camerasWithLabels,
      loadedAt: new Date().toISOString()
    };
  } catch (error) {
    console.error('Error loading camera data:', error);
    return {
      cameras: [],
      error: error instanceof Error ? error.message : 'Failed to load data'
    };
  }
};
```

#### 7. `src/routes/+page.svelte` - Main camera grid UI
```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  let loadingCameras = $state(new Set<string>());

  async function refreshCamera(cameraId: string) {
    loadingCameras.add(cameraId);
    try {
      const response = await fetch(`/api/label/${cameraId}`);
      const result = await response.json();

      if (result.label) {
        // Update camera with new label
        const cameraIndex = data.cameras.findIndex(c => c.id === cameraId);
        if (cameraIndex !== -1) {
          data.cameras[cameraIndex].label = result.label;
          data.cameras[cameraIndex].needsRefresh = false;
        }
      }
    } catch (error) {
      console.error(`Error refreshing camera ${cameraId}:`, error);
    } finally {
      loadingCameras.delete(cameraId);
    }
  }

  // Auto-refresh stale cameras on mount
  onMount(() => {
    data.cameras
      .filter(c => c.needsRefresh)
      .forEach(c => refreshCamera(c.id));
  });

  function getFogColor(fogScore: number | undefined): string {
    if (!fogScore) return '#94a3b8';
    if (fogScore < 20) return '#22c55e';
    if (fogScore < 40) return '#84cc16';
    if (fogScore < 60) return '#eab308';
    if (fogScore < 80) return '#f97316';
    return '#ef4444';
  }
</script>

<svelte:head>
  <title>KarlCam - San Francisco Fog Monitor</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-8">
  <div class="max-w-7xl mx-auto">
    <div class="text-white mb-8">
      <h1 class="text-5xl font-bold mb-2">KarlCam</h1>
      <p class="text-xl opacity-90">Real-time San Francisco Fog Monitoring</p>
    </div>

    {#if data.error}
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {data.error}
      </div>
    {/if}

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each data.cameras as camera (camera.id)}
        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
          <div class="relative h-48 bg-gray-200">
            <img src={camera.url} alt={camera.name} class="w-full h-full object-cover" />

            {#if camera.label}
              <div
                class="absolute top-2 right-2 px-3 py-1 rounded-full text-white font-bold"
                style="background-color: {getFogColor(camera.label.fog_score)}"
              >
                {camera.label.fog_score}
              </div>
            {/if}
          </div>

          <div class="p-4">
            <h3 class="font-bold text-lg mb-2">{camera.name}</h3>

            {#if loadingCameras.has(camera.id)}
              <div class="text-blue-600 text-sm">
                <span class="animate-spin inline-block">⟳</span> Analyzing...
              </div>
            {:else if camera.label}
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-gray-600 text-sm">Fog Level:</span>
                  <span class="font-semibold">{camera.label.fog_level}</span>
                </div>

                <button
                  onclick={() => refreshCamera(camera.id)}
                  class="w-full mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Refresh
                </button>
              </div>
            {:else}
              <div class="text-gray-500 text-sm">No recent data</div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>
```

#### 8. Update `src/routes/+layout.svelte` - Remove auth navigation
```svelte
<!-- Remove login/logout buttons, keep simple layout -->
<div class="min-h-screen">
  <slot />
</div>
```

---

### Phase 5: Install Dependencies & Test (10 min)

```bash
cd web/frontend-sveltekit

# Install dependencies
npm install

# Install missing dependencies
npm install firebase firebase-admin

# Start dev server
npm run dev

# Open http://localhost:3000
```

**Expected behavior:**
1. Page loads 12 cameras from Firestore
2. Cameras with labels < 30 min old show data immediately
3. Stale cameras trigger automatic refresh via Gemini API
4. Each camera shows fog score, level, and refresh button

---

### Phase 6: Deploy to Cloud Run (Optional - 20 min)

Once working locally, deploy:

#### 9. Create `Dockerfile`
```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/package*.json ./
RUN npm ci --only=production
EXPOSE 3000
CMD ["node", "build"]
```

#### 10. Deploy to Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/karlcam/karlcam-frontend-sveltekit
gcloud run deploy karlcam-frontend-sveltekit \
  --image gcr.io/karlcam/karlcam-frontend-sveltekit \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="PUBLIC_FIREBASE_PROJECT_ID=karlcam,PUBLIC_FIREBASE_AUTH_DOMAIN=karlcam.firebaseapp.com" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

---

## Testing Checklist

- [ ] Page loads 12 cameras
- [ ] Cameras with recent Firestore labels show data immediately
- [ ] Stale cameras auto-refresh with Gemini
- [ ] Manual refresh button works
- [ ] Fog scores and colors display correctly
- [ ] Images load from webcam URLs
- [ ] No console errors
- [ ] Firestore queries work (check Firebase Console)
- [ ] New labels are saved to Firestore after on-demand labeling

---

## Future Enhancements

After basic functionality works:

1. **Add map view** - Use Leaflet to show cameras on SF map
2. **Historical data** - Show fog trends over time
3. **Notifications** - Alert when fog conditions change
4. **Mobile optimization** - Better responsive design
5. **Caching** - Add caching layer for frequently accessed data

---

## Troubleshooting

### Firebase Admin Auth Issues
```bash
# Use default credentials
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"
```

### Firestore Database Not Found
```typescript
// Make sure to specify database name
getFirestore('karlcam-firestore')  // Not just getFirestore()
```

### Gemini API Rate Limits
- Free tier: 15 requests/minute
- Consider adding rate limiting or caching

---

## File Structure Reference

```
web/frontend-sveltekit/
├── src/
│   ├── lib/
│   │   ├── firebase.ts              # Client-side Firebase (Firestore only)
│   │   └── server/
│   │       ├── firebase.ts          # Server Firebase Admin init
│   │       └── firestore.ts         # Query utilities
│   ├── routes/
│   │   ├── api/
│   │   │   └── label/
│   │   │       └── [cameraId]/
│   │   │           └── +server.ts   # On-demand labeling API
│   │   ├── +layout.svelte           # Simple layout (no auth)
│   │   ├── +page.svelte             # Camera grid UI
│   │   └── +page.server.ts          # Server-side data loading
│   └── app.html
├── .env                              # Environment variables (gitignored)
├── .env.example                      # Template
├── package.json
├── svelte.config.js
├── tailwind.config.js
└── vite.config.ts
```

---

**Next session: Start with Phase 1, work through to Phase 5.**
**Estimated time: 90 minutes total**
