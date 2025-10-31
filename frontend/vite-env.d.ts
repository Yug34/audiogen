/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_KINDE_CLIENT_ID: string;
  readonly VITE_KINDE_DOMAIN: string;
  readonly VITE_KINDE_REDIRECT_URI: string;
  readonly VITE_KINDE_LOGOUT_URI: string;
}
