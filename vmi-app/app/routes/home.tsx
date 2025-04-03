import type { Route } from "./+types/home";
import { NavBar } from "@/components/navBar";
import { Button } from "@/components/ui/button";
import LaunchApplicationModal from "@/components/launchApplicationModal";
import { useState } from "react";

export function meta({ }: Route.MetaArgs) {
  return [
    { title: "Vulkan Memory Inspector" },
    { name: "description", content: "Vulkan Memory Inspector layer" },
  ];
}

export default function Home() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <NavBar />
      <div className="flex items-center justify-center h-screen">
        <div className="grid grid-cols-2 gap-4 p-6 bg-white rounded-2xl shadow-md">
          <Button variant="default" onClick={() => setIsModalOpen(true)}>Start new Application</Button>
          <Button variant="default">Open Trace</Button>
        </div>
      </div>
      {/* Launch Application Modal */}
      <LaunchApplicationModal isOpen={isModalOpen} setIsOpen={setIsModalOpen} />
    </div>
  );
}
