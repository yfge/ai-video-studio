"use client";

import { AuthGuard } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { StoryProductionBoard } from "@/components/features";

function StoriesPageContent() {
  const { showAlert } = useAlertModal();
  return <StoryProductionBoard showAlert={showAlert} />;
}

export default function StoriesPage() {
  return (
    <AuthGuard>
      <StoriesPageContent />
    </AuthGuard>
  );
}
