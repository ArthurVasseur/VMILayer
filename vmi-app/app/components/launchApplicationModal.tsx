import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { useRef, useState } from "react";
import type { CheckedState } from "@radix-ui/react-checkbox";
import { invoke } from "@tauri-apps/api/core";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { open } from '@tauri-apps/plugin-dialog';

interface LaunchApplicationModalProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export default function LaunchApplicationModal({ isOpen, setIsOpen }: LaunchApplicationModalProps) {
  const [filePath, setFilePath] = useState<string>("");
  const [useDifferentWD, setUseDifferentWD] = useState<CheckedState>(false);
  const [workingDir, setWorkingDir] = useState<string>("");
  const [commandArgs, setCommandArgs] = useState<string>("");
  const [alertMessage, setAlertMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const openFileDialog = async () => {
    const file = await open({ multiple: false, directory: false});
    if (file) {
      setFilePath(file);
      setWorkingDir(file.substring(0, file.lastIndexOf("\\")));
      setAlertMessage(null);
    }
  }

  const handleLaunch = () => {
    if (!filePath) {
      setAlertMessage("Please select an application before launching.");
      return;
    }
    setIsOpen(false);
    invoke("launch_application", { filePath, workingDirectory: workingDir, commandArgs });
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Launch Application</DialogTitle>
        </DialogHeader>

        {/* Display Alert Message */}
        {alertMessage && (
          <Alert className="border-2 border-red-500">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{alertMessage}</AlertDescription>
          </Alert>
        )}

        {/* File Selection */}
        <div className="grid gap-2">
          <Label>Application</Label>
          <div className="flex gap-2">
            <Input readOnly value={filePath} placeholder="Select an application..." />
            <input ref={fileInputRef} type="file" className="hidden" onChange={openFileDialog} />
            <Button onClick={openFileDialog}>Browse</Button>
          </div>
        </div>

        {/* Working Directory Option */}
        <div className="flex items-center gap-2">
          <Checkbox checked={useDifferentWD} onCheckedChange={setUseDifferentWD} />
          <Label>Use different working directory</Label>
        </div>
        {useDifferentWD && (
          <div>
            <Label>Working Directory</Label>
            <Input value={workingDir} onChange={(e) => setWorkingDir(e.target.value)} placeholder="Enter working directory..." />
          </div>
        )}

        {/* Command Arguments */}
        <div>
          <Label>Command Arguments</Label>
          <Input value={commandArgs} onChange={(e) => setCommandArgs(e.target.value)} placeholder="Enter arguments..." />
        </div>

        {/* Launch Button */}
        <Button onClick={handleLaunch} className="w-full mt-2">
          Launch
        </Button>
      </DialogContent>
    </Dialog>
  );
}
