import { useKindeAuth } from "@kinde-oss/kinde-auth-react";
import Navbar from "./components/ui/navbar";
import FileUpload from "./components/FileUpload";

export function App() {
  const { login, register, user, isAuthenticated, isLoading, logout } =
    useKindeAuth();

  return (
    <div className="min-h-screen min-w-screen flex flex-col">
      <Navbar />
      <main className="w-full h-full flex items-center justify-center">
        {isAuthenticated ? (
          <>
            <h1 className="text-4xl font-bold">Hello {user?.givenName}</h1>
            <FileUpload />
          </>
        ) : (
          <h1 className="text-4xl font-bold">Hello World</h1>
        )}
      </main>
    </div>
  );
}
