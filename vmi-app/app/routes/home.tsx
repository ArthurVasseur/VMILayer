import type { Route } from "./+types/home";
import { Welcome } from "../welcome/welcome";
import { NavBar } from "@/components/navBar";

export function meta({ }: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export default function Home() {

  return (
    <div>
      <NavBar />
      <div className="flex items-center justify-center h-screen">
        <h1  className="text-xl">
          Launch an application from the menu above or open a trace to see data.
        </h1>
      </div>
    </div>
  );
}
