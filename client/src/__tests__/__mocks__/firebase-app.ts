// Lightweight stub for firebase/app — prevents real Firebase SDK from being loaded in tests
export function initializeApp(_config: object) {
  return { name: '[DEFAULT]', options: _config };
}
export function getApp() {
  return { name: '[DEFAULT]' };
}
