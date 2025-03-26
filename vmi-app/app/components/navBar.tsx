"use client"

import {
  Menubar,
  MenubarCheckboxItem,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarTrigger,
} from "@/components/ui/menubar"

import { useState } from "react";
import LaunchApplicationModal from "./launchApplicationModal";


export function NavBar()
{
  const [isModalOpen, setIsModalOpen] = useState(false);
  return (
    <div>

      <Menubar className="justify-start w-full">
        <MenubarMenu>
          <MenubarTrigger>File</MenubarTrigger>
          <MenubarContent align="start">
            <MenubarItem onClick={() => setIsModalOpen(true)}>Launch Application</MenubarItem>
            <MenubarItem>Open Trace</MenubarItem>
            <MenubarItem>Save Trace</MenubarItem>
            <MenubarSeparator />
            <MenubarItem>Exit</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger>Tools</MenubarTrigger>
          <MenubarContent align="start">
            <MenubarCheckboxItem>Settings</MenubarCheckboxItem>
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger>Help</MenubarTrigger>
          <MenubarContent align="start">
            <MenubarItem>Documentation</MenubarItem>
            <MenubarItem>About</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
      </Menubar>
      {/* Launch Application Modal */}
      <LaunchApplicationModal isOpen={isModalOpen} setIsOpen={setIsModalOpen} />
    </div>
  )
}
