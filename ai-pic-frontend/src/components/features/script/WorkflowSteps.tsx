"use client";

interface WorkflowStepsProps {
  onGoToSceneDetails: () => void;
  onGoToSceneStructure: () => void;
  onGoToStoryboard: () => void;
}

export function WorkflowSteps({
  onGoToSceneDetails,
  onGoToSceneStructure,
  onGoToStoryboard,
}: WorkflowStepsProps) {
  return (
    <section className="grid gap-3 rounded-2xl bg-white p-4 shadow md:grid-cols-3">
      <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-blue-50 to-white p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-blue-700">Step 1</div>
        <div className="mt-1 text-base font-semibold text-gray-900">Scene Text Details</div>
        <p className="mt-1 text-xs text-gray-600">
          Browse dialogues, stage directions, confirm scene intent and characters.
        </p>
        <button
          onClick={onGoToSceneDetails}
          className="mt-3 inline-flex items-center rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
        >
          View Scene Details
        </button>
      </div>
      <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-indigo-50 to-white p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Step 2</div>
        <div className="mt-1 text-base font-semibold text-gray-900">Structured Scenes / Shots</div>
        <p className="mt-1 text-xs text-gray-600">
          Adjust beats, shot order when needed in this view.
        </p>
        <button
          onClick={onGoToSceneStructure}
          className="mt-3 inline-flex items-center rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
        >
          Open Structure Editor
        </button>
      </div>
      <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-purple-50 to-white p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-purple-700">Step 3</div>
        <div className="mt-1 text-base font-semibold text-gray-900">Storyboard Management</div>
        <p className="mt-1 text-xs text-gray-600">
          Go directly to storyboard workspace, generate or adjust shots.
        </p>
        <button
          onClick={onGoToStoryboard}
          className="mt-3 inline-flex items-center rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700"
        >
          Go to Storyboard
        </button>
      </div>
    </section>
  );
}
