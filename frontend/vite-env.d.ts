/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_KINDE_CLIENT_ID: string;
  readonly VITE_KINDE_DOMAIN: string;
  readonly VITE_KINDE_REDIRECT_URI: string;
  readonly VITE_KINDE_LOGOUT_URI: string;
}

// Declare module for audio file imports
declare module "*.mp3" {
  const src: string;
  export default src;
}
declare module "*.wav" {
  const src: string;
  export default src;
}
declare module "*.ogg" {
  const src: string;
  export default src;
}
