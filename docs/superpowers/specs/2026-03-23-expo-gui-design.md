# OneLap-Strava Sync - Expo Cross-Platform App Design

**Date**: 2026-03-23
**Status**: Approved
**Scope**: Full cross-platform GUI (iOS / Android / Web / Desktop) for the OneLap-to-Strava sync tool

---

## 1. Overview

Build a cross-platform mobile/web app using Expo (React Native) that replaces the Python CLI as the primary user interface. The app runs entirely on the client side — no backend server required. All core sync logic (OneLap login, FIT download, Strava OAuth, upload, dedup) is rewritten in TypeScript.

The existing Python CLI remains untouched and continues to work independently.

## 2. Goals

- **All platforms**: iOS, Android, Web, Desktop (via PWA)
- **No backend**: App calls OneLap and Strava APIs directly
- **Feature parity**: All CLI features available through GUI
- **Bilingual**: Chinese and English UI with runtime switching
- **Standalone**: Install on phone, open, and use — no computer needed

## 3. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | Expo (React Native) ~52 | Single codebase -> iOS/Android/Web |
| Language | TypeScript | Type safety for rewritten sync logic |
| Navigation | Expo Router ~4 (file-system routing) | Simple, convention-based |
| State management | Zustand ^5 | Lightweight, minimal boilerplate |
| Secure storage | expo-secure-store ~14 | Encrypted credential storage |
| General storage | @react-native-async-storage/async-storage ~2 | Sync state + history + preferences |
| HTTP | fetch (built-in) | No extra dependency |
| Cookie management | @react-native-cookies/cookies ^6 | Cross-subdomain cookie handling for OneLap |
| File system | expo-file-system ~18 | FIT file download to cache |
| Crypto | expo-crypto ~14 | MD5 (OneLap password) + SHA-256 (dedup) |
| OAuth | expo-auth-session ~6 | Strava OAuth with deep link callback |
| i18n | i18next ^24 + react-i18next ^15 | Mature bilingual solution |
| UI | React Native built-in components | Keep lightweight |

## 4. Project Structure

```
onelap-strava-sync/
├── src/sync_onelap_strava/    # Existing Python CLI (unchanged)
├── tests/                     # Existing Python tests (unchanged)
├── app/                       # NEW: Expo App
│   ├── app/                   # Expo Router pages
│   │   ├── (tabs)/            # Tab navigation
│   │   │   ├── index.tsx      # Sync home page
│   │   │   ├── history.tsx    # Sync history
│   │   │   ├── logs.tsx       # Log viewer
│   │   │   └── settings.tsx   # Configuration
│   │   └── _layout.tsx        # Root layout
│   ├── src/
│   │   ├── services/          # Core business logic (rewritten from Python)
│   │   │   ├── onelap-client.ts
│   │   │   ├── strava-client.ts
│   │   │   ├── sync-engine.ts
│   │   │   ├── state-store.ts
│   │   │   └── dedupe-service.ts
│   │   ├── stores/            # Zustand state stores
│   │   │   ├── settings-store.ts
│   │   │   ├── sync-store.ts
│   │   │   └── log-store.ts
│   │   ├── i18n/              # Translations
│   │   │   ├── index.ts
│   │   │   ├── zh.json
│   │   │   └── en.json
│   │   ├── hooks/             # Custom React hooks
│   │   │   ├── use-sync.ts
│   │   │   └── use-settings.ts
│   │   └── components/        # Reusable UI components
│   │       ├── ActivityRow.tsx
│   │       ├── ProgressBar.tsx
│   │       └── StatusBadge.tsx
│   ├── __tests__/             # Jest tests
│   │   ├── services/
│   │   │   ├── onelap-client.test.ts
│   │   │   ├── strava-client.test.ts
│   │   │   ├── sync-engine.test.ts
│   │   │   ├── state-store.test.ts
│   │   │   └── dedupe-service.test.ts
│   │   └── components/
│   ├── package.json
│   ├── tsconfig.json
│   └── app.json               # Expo config
├── pyproject.toml             # Python project (unchanged)
└── ...
```

## 5. Page Design

### 5.1 Navigation: Bottom Tab Bar (4 tabs)

| Tab | Icon | Label (zh/en) | Purpose |
|---|---|---|---|
| 1 | sync icon | 同步 / Sync | Main sync operations |
| 2 | clock icon | 历史 / History | Past sync records |
| 3 | document icon | 日志 / Logs | Runtime log viewer |
| 4 | gear icon | 设置 / Settings | Configuration |

### 5.2 Tab 1: Sync Home

Primary operation page. Contains:
- **Date picker**: Select start date for sync (defaults to today minus lookback days)
- **"Start Sync" button**: Full sync (download + upload)
- **"Download Only" button**: Download FIT files without uploading
- **Progress section**: Real-time progress bar + per-activity status list
  - Each activity row shows: filename, status icon (pending/downloading/uploading/done/skipped/failed), status text
- **Last sync info**: Timestamp of last successful sync

States:
- **Idle**: Both buttons enabled, progress section shows last sync summary or empty
- **Syncing**: Buttons disabled, progress bar animating, activity list updating in real-time
- **Complete**: Summary shown (fetched X / deduped Y / success Z / failed W)
- **Error**: Error banner at top with message, failed activities marked in red

### 5.3 Tab 2: History

Displays sync history in reverse chronological order:
- Each entry: timestamp + summary counters (fetched/deduped/success/failed)
- Expandable: tap to see individual activity details
- Below history: scrollable list of all synced activities with their Strava activity IDs

Data source: AsyncStorage (persisted after each sync run)

### 5.4 Tab 3: Logs

Scrollable log viewer:
- Displays log entries with timestamp, level (INFO/WARN/ERROR), and message
- Auto-scrolls to bottom during active sync
- "Clear" button to reset logs
- Color-coded: INFO=default, WARN=yellow, ERROR=red

Logs are collected in-memory via the log store during sync and persisted to AsyncStorage.

### 5.5 Tab 4: Settings

Sections:
1. **OneLap Account**: Username (text input) + Password (secure input) + "Test Connection" button
2. **Strava Authorization**: Status indicator (authorized/expired/not set) + "Authorize" / "Re-authorize" button (triggers OAuth flow)
3. **Sync Settings**: Default lookback days (number input)
4. **Language**: Dropdown/picker to switch between 中文 and English
5. **About**: App version

All credential changes are persisted to SecureStore immediately on save.

## 6. Core Service Layer (TypeScript Rewrite)

### 6.1 Module Mapping

| Python Module | TS Module | Key Changes |
|---|---|---|
| `onelap_client.py` | `onelap-client.ts` | `requests.Session` -> `fetch` + manual cookie; MD5 via `expo-crypto` |
| `strava_client.py` | `strava-client.ts` | 1:1 translation; tokens stored in SecureStore |
| `sync_engine.py` | `sync-engine.ts` | Same loop; progress via callback functions |
| `state_store.py` | `state-store.ts` | JSON file -> AsyncStorage |
| `dedupe_service.py` | `dedupe-service.ts` | SHA-256 via `expo-crypto` |
| `config.py` | Zustand store | Settings dataclass -> Zustand + SecureStore |

### 6.2 OneLap Client

```typescript
class OneLapClient {
  constructor(baseUrl: string, username: string, password: string)
  async login(): Promise<boolean>
  async listFitActivities(since: Date, limit: number): Promise<OneLapActivity[]>
  async downloadFit(recordKey: string, fitUrl: string): Promise<string> // returns local file URI
}
```

Key implementation details:
- Login sends MD5-hashed password to `{baseUrl}/api/login`
- MD5 computed via `expo-crypto.digestStringAsync(CryptoDigestAlgorithm.MD5, password)`
- **Cookie management**: The Python `requests.Session` auto-manages cookies. On React Native, cookies are trickier:
  - Login is to `www.onelap.cn` but activity list is fetched from `u.onelap.cn` (different subdomain)
  - Native `fetch` with `credentials: 'include'` uses the OS cookie jar, which follows RFC 6265 — cookies set for `www.onelap.cn` will NOT be sent to `u.onelap.cn` unless the cookie domain is `.onelap.cn`
  - **Solution**: Use `@react-native-cookies/cookies` to read cookies after login and manually set them for the `u.onelap.cn` domain. If the login response sets cookies with domain `www.onelap.cn`, copy them to `.onelap.cn` scope using `CookieManager.set()`
  - On web platform: browser's native cookie jar handles this automatically
- Activity list fetched from `http://u.onelap.cn/analysis/list` (plain HTTP — see §13.3 for platform config)
- On 401/login-redirect: auto-retry with login (max 1 retry)
- FIT files downloaded to `FileSystem.cacheDirectory` (volatile — OS may reclaim, acceptable for transient sync use)
- **Download-level dedup**: Unlike the Python client which avoids overwriting identical files via SHA-256 comparison, the TS client skips this since files go to a volatile cache and are used only during the current sync operation. Fingerprint-level dedup in the StateStore is the primary dedup mechanism.

### 6.3 Strava Client

```typescript
class StravaClient {
  constructor(clientId: string, clientSecret: string, refreshToken: string, accessToken: string, expiresAt: number)
  async ensureAccessToken(): Promise<string>
  async uploadFit(fileUri: string, retries?: number): Promise<number> // returns upload_id
  async pollUpload(uploadId: number, maxAttempts?: number): Promise<UploadResult>
}
```

Key implementation details:
- Token refresh: POST `https://www.strava.com/oauth/token` with `grant_type=refresh_token`
- After refresh: update SecureStore with new access_token, refresh_token, expires_at
- **Multipart upload**: Platform-specific approach:
  - **Native (iOS/Android)**: Use `FileSystem.uploadAsync(url, fileUri, { uploadType: FileSystemUploadType.MULTIPART, fieldName: 'file', parameters: { data_type: 'fit', ... } })` for reliable multipart upload from local file URI
  - **Web**: Use `FormData` with `Blob` constructed from file content read via `FileSystem.readAsStringAsync(uri, { encoding: 'base64' })`
- Upload endpoint: POST `https://www.strava.com/api/v3/uploads` with `data_type=fit`
- 5xx retry: up to 3 times with 1s backoff
- 4xx: throw `StravaPermanentError`
- Poll: GET upload status up to 10 times with 2s interval

### 6.4 Sync Engine

```typescript
class SyncEngine {
  constructor(
    onelapClient: OneLapClient,
    stravaClient: StravaClient,
    stateStore: StateStore,
    makeFingerprint: (fileUri: string, startTime: string, recordKey: string) => Promise<string>,
    onEvent?: (event: SyncEvent) => void
  )
  async runOnce(sinceDate?: Date, limit?: number): Promise<SyncSummary>
}
```

Note: `makeFingerprint` is injected as a dependency (matching the Python pattern) to allow mocking in tests. Downloaded FIT files are stored in the app's cache directory (`FileSystem.cacheDirectory`), managed internally by the engine.

**SyncEvent type** for real-time UI updates:

```typescript
type SyncEvent =
  | { type: 'activity_start'; activity: OneLapActivity; index: number; total: number }
  | { type: 'activity_downloaded'; filename: string }
  | { type: 'activity_uploaded'; stravaId: number }
  | { type: 'activity_deduped'; reason: 'already_synced' | 'strava_duplicate' }
  | { type: 'activity_failed'; error: string }
  | { type: 'sync_complete'; summary: SyncSummary }
  | { type: 'sync_aborted'; reason: string };
```

**SyncSummary**:

```typescript
interface SyncSummary {
  fetched: number;
  deduped: number;
  success: number;
  failed: number;
  abortedReason?: string;
}
```

### 6.5 State Store

```typescript
class StateStore {
  async isSynced(fingerprint: string): Promise<boolean>
  async markSynced(fingerprint: string, stravaActivityId: number): Promise<void>
  async lastSuccessSyncTime(): Promise<string | null>
  async getAllSynced(): Promise<Record<string, SyncedEntry>>
}
```

Storage format in AsyncStorage (key: `@sync_state`):
```json
{
  "synced": {
    "fileKey:abc|sha256hash|2026-03-09T08:00:00Z": {
      "strava_activity_id": 12345,
      "synced_at": "2026-03-10T10:30:00+00:00"
    }
  }
}
```

### 6.6 Fingerprint (Dedupe Service)

```typescript
async function makeFingerprint(fileUri: string, startTime: string, recordKey: string): Promise<string>
// Returns: "{recordKey}|{sha256_of_file}|{startTime}"
```

**SHA-256 implementation**: The Python code hashes raw file bytes (`hashlib.sha256(path.read_bytes())`). On React Native:
- Read file as base64: `FileSystem.readAsStringAsync(fileUri, { encoding: 'base64' })`
- Decode base64 to `Uint8Array` for hashing
- Use `expo-crypto.digest(CryptoDigestAlgorithm.SHA256, data)` (Expo SDK 52+ supports `Uint8Array` input)
- Convert result to hex string to match Python's `hexdigest()` output
- **Critical**: Must hash the raw bytes, NOT the base64 string, to produce fingerprints compatible with the Python CLI's state store

## 7. Strava OAuth on Mobile

Mobile OAuth flow differs from the desktop CLI flow. Uses the current `expo-auth-session` API (`useAuthRequest` hook + `promptAsync`, NOT the deprecated `startAsync`):

1. App defines Strava discovery document and calls `useAuthRequest` hook with client_id, scopes, redirect URI
2. App calls `AuthSession.makeRedirectUri()` to get the deep link redirect URI (e.g., `onelap-sync://oauth/callback`)
3. User taps "Authorize" -> `promptAsync()` opens Strava authorize URL in system browser:
   ```
   https://www.strava.com/oauth/authorize?client_id=...&redirect_uri=onelap-sync://oauth/callback&response_type=code&scope=read,activity:write
   ```
4. User authorizes in Strava web page
5. Strava redirects to deep link -> App receives authorization code via `response.params.code`
6. **Scope validation**: App verifies the returned scope (from exchange response) includes `activity:write`. If not, show error: "Strava authorization missing required permission (activity:write). Please re-authorize."
7. App exchanges code for tokens: POST `https://www.strava.com/oauth/token`
8. Tokens saved to SecureStore

Configuration in `app.json`:
```json
{
  "expo": {
    "scheme": "onelap-sync"
  }
}
```

## 8. Data Storage Strategy

| Data | Storage | Encryption |
|---|---|---|
| OneLap username/password | SecureStore | Yes (OS-level) |
| Strava client_id/secret | SecureStore | Yes (OS-level) |
| Strava access/refresh tokens | SecureStore | Yes (OS-level) |
| Strava expires_at | SecureStore | Yes (OS-level) |
| Sync state (fingerprints) | AsyncStorage | No |
| Sync history (summaries) | AsyncStorage | No |
| Log entries | In-memory + AsyncStorage | No |
| Language preference | AsyncStorage | No |
| Default lookback days | AsyncStorage | No |

**Web platform note**: `expo-secure-store` is not available on web. On web, credentials fall back to `AsyncStorage` (backed by `localStorage`), which is NOT encrypted. The app should display a warning on web: "Credentials are stored without encryption on web. For sensitive use, prefer the mobile app."

**AsyncStorage size note**: Android's default AsyncStorage limit is 6MB. Each synced entry is ~150 bytes, supporting ~40K activities before hitting the limit. This is sufficient for expected usage. If needed, implement state pruning for entries older than 1 year.

## 9. Error Handling

| Scenario | Handling | User-visible effect |
|---|---|---|
| OneLap 401 / session expired | Auto-retry login (max 1) | Progress shows "Re-logging in..." |
| OneLap risk control | Throw `OnelapRiskControlError`, abort sync | Alert: "OneLap triggered risk control, try later" |
| Strava 5xx | Retry up to 3 times, 1s backoff | Progress shows "Retrying (2/3)" |
| Strava 4xx | No retry, mark failed | Activity row shows red error message |
| Strava "duplicate of" | Treat as synced, record in state | Activity row shows "Skipped (duplicate)" |
| Token expired | Auto-refresh, update SecureStore | Transparent to user |
| Network offline | Catch exception, show alert | Alert: "Network connection failed" |
| OneLap credentials not set | Disable sync buttons | Banner: "Please configure OneLap account in Settings" |
| Strava not authorized | Disable sync buttons | Banner: "Please authorize Strava in Settings" |

## 10. Internationalization (i18n)

Two locale files: `zh.json` and `en.json`.

Key translation keys:
- `sync.title`, `sync.startSync`, `sync.downloadOnly`, `sync.progress`
- `history.title`, `history.fetched`, `history.deduped`, `history.success`, `history.failed`
- `logs.title`, `logs.clear`
- `settings.title`, `settings.onelapAccount`, `settings.stravaAuth`, `settings.testConnection`
- `settings.language`, `settings.about`
- `status.uploading`, `status.downloading`, `status.skipped`, `status.failed`, `status.success`
- `errors.networkFailed`, `errors.riskControl`, `errors.configMissing`

Language stored in AsyncStorage, applied on app startup via `i18next.changeLanguage()`.

## 11. Testing Strategy

- **Service layer unit tests**: Jest tests for all TS service modules, mocking `fetch` calls
- **1:1 correspondence with Python tests**: Use existing 21 Python test files as reference to ensure behavioral parity
- **Component tests**: Key interactions (sync button, progress display) via React Native Testing Library
- **Manual E2E**: Test on iOS Simulator, Android Emulator, and Expo Go

## 12. Build & Distribution

| Platform | Build Command | Output |
|---|---|---|
| Android | `eas build --platform android` | APK / AAB |
| iOS | `eas build --platform ios` | IPA (requires Apple Developer account) |
| Web | `npx expo export --platform web` | Static site |
| Desktop | Web build + PWA install | Installable web app |

For Android: APK can be sideloaded directly. For iOS: requires TestFlight or App Store distribution.

## 13. Constraints & Risks

1. **Strava client_secret in app**: Embedding `client_secret` in a mobile app is a security risk. Strava's API does not currently support PKCE for mobile apps. Mitigation: store in SecureStore (encrypted), accept the risk for a personal-use tool.
2. **OneLap cookie handling**: React Native `fetch` does not auto-manage cookies across subdomains. See §6.2 for the `@react-native-cookies/cookies` solution.
3. **OneLap HTTP endpoints**: OneLap uses `http://` (not HTTPS) for `u.onelap.cn`. Platform-specific configuration required:
   - **iOS**: Add domain-specific ATS exception in `app.json` (NOT global `NSAllowsArbitraryLoads`):
     ```json
     {
       "expo": {
         "ios": {
           "infoPlist": {
             "NSAppTransportSecurity": {
               "NSExceptionDomains": {
                 "onelap.cn": {
                   "NSIncludesSubdomains": true,
                   "NSExceptionAllowsInsecureHTTPLoads": true
                 }
               }
             }
           }
         }
       }
     }
     ```
   - **Android**: Add `android:usesCleartextTraffic` for `onelap.cn` only via `network_security_config.xml`:
     ```xml
     <network-security-config>
       <domain-config cleartextTrafficPermitted="true">
         <domain includeSubdomains="true">onelap.cn</domain>
       </domain-config>
     </network-security-config>
     ```
4. **FIT file size**: Large FIT files may need streaming download. `expo-file-system.downloadAsync` handles this.
5. **Rate limiting**: Both OneLap and Strava may rate-limit. Existing retry/backoff logic handles Strava; OneLap risk control detection handles OneLap.

## 14. OneLap Risk Control Detection

The Python `SyncEngine` catches `OnelapRiskControlError`. This error is raised when the OneLap API returns a response indicating the account has been flagged for abnormal access patterns. Detection criteria in the TS client:
- HTTP response contains specific error code or message pattern indicating risk control (e.g., response body containing "风控" or a specific error code)
- The exact detection logic should be determined during implementation by examining actual OneLap API error responses
- When detected: immediately abort sync, show user alert with the `aborted_reason="risk-control"` message

## 15. Out of Scope (Future Considerations)

These features are intentionally excluded from v1 but may be added later:
- **Background sync**: Periodic automatic sync (e.g., after each workout)
- **Push notifications**: Notify user when sync completes or fails
- **Auto-sync on activity detection**: Trigger sync when OneLap records a new activity
- **Strava activity editing**: Modify activity name/type after upload
- **Multi-account support**: Sync multiple OneLap/Strava account pairs
