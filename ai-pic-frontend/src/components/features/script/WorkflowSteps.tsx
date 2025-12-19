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
        <div className="text-xs font-semibold uppercase tracking-wide text-blue-700">步骤 1</div>
        <div className="mt-1 text-base font-semibold text-gray-900">场景文本详情</div>
        <p className="mt-1 text-xs text-gray-600">
          浏览对白与舞台指令，确认场景意图和角色。
        </p>
        <button
          onClick={onGoToSceneDetails}
          className="mt-3 inline-flex items-center rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
        >
          查看场景详情
        </button>
      </div>
      <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-indigo-50 to-white p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-indigo-700">步骤 2</div>
        <div className="mt-1 text-base font-semibold text-gray-900">结构化场景 / 镜头</div>
        <p className="mt-1 text-xs text-gray-600">
          在此视图调整节拍与镜头顺序。
        </p>
        <button
          onClick={onGoToSceneStructure}
          className="mt-3 inline-flex items-center rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
        >
          打开结构编辑
        </button>
      </div>
      <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-purple-50 to-white p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-purple-700">步骤 3</div>
        <div className="mt-1 text-base font-semibold text-gray-900">分镜管理</div>
        <p className="mt-1 text-xs text-gray-600">
          进入分镜工作台，生成或调整镜头。
        </p>
        <button
          onClick={onGoToStoryboard}
          className="mt-3 inline-flex items-center rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700"
        >
          前往分镜
        </button>
      </div>
    </section>
  );
}
