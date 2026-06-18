import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { afterEach, describe, it } from "node:test";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { JSDOM } from "jsdom";

import {
  EpisodeWorkspaceHeader,
  type WorkflowStatus,
} from "../src/components/features/episode";
import { EpisodeTimelineWorkspace } from "../src/components/features/episode/EpisodeTimelineWorkspace";
import { AlertModalProvider } from "../src/components/shared/modals";
import { ToastProvider } from "../src/components/shared/notifications";
import { clearAvailableModelsCache } from "../src/hooks/useAvailableModels";
import { TimelineItemButton } from "../src/components/features/Timeline/TimelineItemButton";
import { TimelineOverview } from "../src/components/features/Timeline/TimelineOverview";
import { timelineLayoutForMeasuredWidth } from "../src/components/features/Timeline/timelineLayout";
import type {
  Episode,
  Script,
  TimelineClipAssetResponse,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost",
});
(globalThis as any).window = dom.window;
(globalThis as any).self = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;
(globalThis as any).HTMLSelectElement = dom.window.HTMLSelectElement;
(globalThis as any).localStorage = dom.window.localStorage;

const originalFetch = globalThis.fetch;
const GLOBAL_CSS = readFileSync(
  new URL("../src/app/globals.css", import.meta.url),
  "utf8",
);

describe("EpisodeTimelineWorkspace layout", () => {
  afterEach(() => {
    cleanup();
    clearAvailableModelsCache();
    globalThis.fetch = originalFetch;
    localStorage.clear();
  });

  it("puts video clip generation in the main canvas instead of a right inspector", async () => {
    mockWorkspaceFetch({
      resolvedVideos: resolvedVideos("https://example.com/clip-ready.mp4"),
    });

    const utils = render(
      workspace(
        videoTimeline(),
        undefined,
        resolvedVideos("https://example.com/clip-ready.mp4"),
      ),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByText("片段分镜管理"));
      assert.ok(utils.getByLabelText("步骤 1 · 片段分镜图"));
      assert.ok(utils.getByLabelText("步骤 3 · 片段视频"));
      assert.ok(utils.getByLabelText("在时间轴中选择 视频 1"));
    });
    assert.equal(utils.queryByText("片段检查器"), null);
    assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    const commandCards = Array.from(
      dom.window.document.querySelectorAll("[data-clip-command-card]"),
    ) as HTMLElement[];
    assert.deepEqual(
      commandCards.map((card) => card.getAttribute("data-clip-command-card")),
      ["storyboard", "keyframes", "video"],
    );
    const storyboardCard = commandCards.find(
      (card) => card.getAttribute("data-clip-command-card") === "storyboard",
    );
    const videoCard = commandCards.find(
      (card) => card.getAttribute("data-clip-command-card") === "video",
    );
    assert.match(storyboardCard?.className || "", /max-\[719px\]:order-1/);
    assert.doesNotMatch(videoCard?.className || "", /max-\[719px\]:order-1/);
    const video = utils.getByLabelText("播放选中片段视频");
    assert.equal(
      video.getAttribute("src"),
      "https://example.com/clip-ready.mp4",
    );
  });

  it("renders succeeded timeline render output as an embedded player", async () => {
    mockWorkspaceFetch({
      resolvedVideos: resolvedVideos("https://example.com/clip-ready.mp4"),
      renderJobs: [
        {
          id: 9,
          business_id: "render_9",
          timeline_id: 8,
          timeline_version: 3,
          render_type: "final",
          preset_hash: "hash",
          preset: {},
          status: "succeeded",
          progress: 100,
          output_asset_id: 18,
          output_asset: {
            id: 18,
            business_id: "asset_18",
            asset_type: "video",
            origin: "rendered",
            file_url: "https://example.com/final.mp4",
            created_at: "2026-06-11T00:00:00Z",
            updated_at: "2026-06-11T00:00:00Z",
          },
          created_at: "2026-06-11T00:00:00Z",
          updated_at: "2026-06-11T00:00:00Z",
        },
      ],
    });

    const utils = render(
      workspace(
        videoTimeline(),
        undefined,
        resolvedVideos("https://example.com/clip-ready.mp4"),
      ),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      const video = utils.getByLabelText("播放渲染成片");
      assert.equal(video.getAttribute("src"), "https://example.com/final.mp4");
      assert.ok(utils.getByRole("button", { name: "渲染预览" }));
      assert.ok(utils.getByRole("button", { name: "导出成片" }));
    });
  });

  it("renders a compact production path header with one primary next action", () => {
    const selectedScript = script();
    const tabChanges: string[] = [];
    const workflowStatus: WorkflowStatus = {
      script: "ready",
      timeline: "pending",
      storyboard: "pending",
    };
    const utils = render(
      <EpisodeWorkspaceHeader
        episode={episode()}
        script={selectedScript}
        scripts={[selectedScript]}
        selectedScriptId={selectedScript.id}
        workflowStatus={workflowStatus}
        activeTab="timeline"
        onTabChange={(tab) => tabChanges.push(tab)}
        onNavigateBack={() => {}}
        onGenerateScript={() => {}}
        onGenerateTimeline={() => {}}
        onSelectScript={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(utils.getByLabelText("生产主线"));
    assert.ok(utils.getByLabelText("当前剧本"));
    const scriptSelect = utils.getByLabelText("当前剧本") as HTMLSelectElement;
    assert.equal(scriptSelect.value, String(selectedScript.id));
    assert.equal(
      scriptSelect.selectedOptions[0]?.textContent,
      "第1集剧本 (v1.0)",
    );
    assert.equal(
      scriptSelect.selectedOptions[0]?.textContent?.includes("ID:"),
      false,
    );
    assert.ok(
      dom.window.document.querySelector(
        '[data-episode-workspace-timeline-header="compact"]',
      ),
    );
    const timelineHeader = dom.window.document.querySelector(
      '[data-episode-workspace-timeline-header="compact"]',
    );
    const timelineHeaderLayout = timelineHeader?.querySelector(
      '[data-episode-workspace-timeline-header-layout="responsive-workbar"]',
    );
    assert.ok(timelineHeaderLayout);
    assert.match(
      timelineHeaderLayout.className,
      /grid-cols-\[minmax\(0,1fr\)_auto\]/,
    );
    assert.match(timelineHeaderLayout.className, /760px/);
    assert.match(timelineHeaderLayout.className, /minmax\(10rem,1fr\)/);
    assert.match(timelineHeaderLayout.className, /gap-y-0\.5/);
    assert.match(timelineHeaderLayout.className, /min-\[760px\]:gap-y-1/);
    assert.doesNotMatch(timelineHeaderLayout.className, /grid-cols-1/);
    assert.doesNotMatch(timelineHeaderLayout.className, /22rem/);
    assert.ok(
      dom.window.document.querySelector(
        '[data-workspace-script-select-slot="compact"]',
      ),
    );
    assert.match(
      dom.window.document.querySelector(
        '[data-workspace-script-select-slot="compact"]',
      )?.className || "",
      /order-3/,
    );
    const productionStepRail = dom.window.document.querySelector(
      '[data-production-step-rail="compact"]',
    );
    assert.ok(productionStepRail);
    assert.match(productionStepRail.className, /order-4/);
    assert.equal(
      productionStepRail.getAttribute("data-production-step-rail-layout"),
      "segments",
    );
    assert.equal(productionStepRail.getAttribute("aria-label"), "生产主线");
    assert.ok(
      productionStepRail.querySelector(
        '[data-production-step-pills="compact"]',
      ),
    );
    assert.match(productionStepRail.textContent || "", /生产主线/);
    assert.match(
      productionStepRail.querySelector("span")?.className || "",
      /sr-only/,
    );
    assert.doesNotMatch(
      productionStepRail.querySelector("span")?.className || "",
      /not-sr-only/,
    );
    assert.doesNotMatch(productionStepRail.textContent || "", /时间轴\s*待/);
    assert.doesNotMatch(productionStepRail.textContent || "", /片段\s*待/);
    assert.doesNotMatch(productionStepRail.textContent || "", /导出\s*待/);
    assert.doesNotMatch(productionStepRail.textContent || "", /剧本\s*就绪/);
    const stepPills = Array.from(
      productionStepRail.querySelectorAll("[data-production-step-pill]"),
    ) as HTMLElement[];
    assert.deepEqual(
      stepPills.map((pill) => pill.getAttribute("data-production-step-pill")),
      ["script", "timeline", "clip-video", "render-export"],
    );
    assert.deepEqual(
      stepPills.map((pill) => pill.getAttribute("data-production-step-status")),
      ["ready", "pending", "pending", "pending"],
    );
    assert.equal(stepPills[0].getAttribute("aria-label"), "剧本 已就绪");
    assert.equal(stepPills[1].getAttribute("aria-label"), "时间轴 待处理");
    assert.equal(stepPills[2].getAttribute("aria-label"), "片段视频 待处理");
    assert.equal(stepPills[3].getAttribute("aria-label"), "渲染/导出 待处理");
    assert.equal(
      stepPills[0].getAttribute("data-production-step-compact"),
      "segment",
    );
    assert.equal(
      stepPills[1].getAttribute("data-production-step-compact"),
      "segment",
    );
    assert.equal(
      stepPills[2].getAttribute("data-production-step-compact"),
      "segment",
    );
    assert.equal(
      stepPills[3].getAttribute("data-production-step-compact"),
      "segment",
    );
    assert.ok(stepPills.every((pill) => pill.textContent?.trim() === ""));
    assert.match(stepPills[0].className, /h-1\.5/);
    assert.match(stepPills[0].className, /w-4/);
    assert.match(stepPills[0].className, /min-\[760px\]:w-5/);
    assert.match(stepPills[0].className, /rounded-full/);
    assert.match(stepPills[0].className, /bg-emerald-500/);
    assert.doesNotMatch(stepPills[0].className, /border-emerald-500/);
    assert.equal(
      stepPills[0].className.split(/\s+/).includes("bg-emerald-50"),
      false,
    );
    assert.match(stepPills[1].className, /bg-slate-200/);
    assert.doesNotMatch(stepPills[1].className, /border-gray-300/);
    assert.doesNotMatch(stepPills[1].className, /bg-white/);
    assert.equal(stepPills[0].querySelector("span"), null);
    assert.match(utils.getByLabelText("当前剧本").className, /bg-gray-50/);
    assert.match(utils.getByLabelText("当前剧本").className, /!h-6/);
    assert.match(
      utils.getByLabelText("当前剧本").className,
      /min-\[760px\]:!h-8/,
    );
    assert.equal(
      utils.getAllByRole("button", { name: "生成 Timeline" }).length,
      1,
    );
    assert.match(
      utils.getAllByRole("button", { name: "生成 Timeline" })[0].className,
      /!h-6/,
    );
    assert.match(
      utils.getAllByRole("button", { name: "生成 Timeline" })[0].className,
      /min-\[760px\]:!h-8/,
    );
    assert.equal(utils.queryByText("步骤 1"), null);
    assert.equal(utils.queryByRole("button", { name: "剧集概要" }), null);
    const supportButton = utils.getByRole("button", { name: "支持视图" });
    assert.equal(supportButton.textContent?.trim(), "");
    assert.equal(supportButton.getAttribute("title"), "支持视图");
    assert.equal(
      supportButton.getAttribute("data-support-view-trigger"),
      "icon",
    );
    assert.ok(supportButton.querySelector("svg"));
    assert.doesNotMatch(supportButton.className, /border-gray-200/);
    assert.match(supportButton.className, /w-6/);
    assert.match(supportButton.className, /min-\[760px\]:w-8/);
    assert.equal(supportButton.getAttribute("aria-expanded"), "false");
    assert.equal(utils.queryByRole("button", { name: "剧本设置" }), null);

    fireEvent.click(supportButton);
    assert.equal(supportButton.getAttribute("aria-expanded"), "true");
    assert.ok(utils.getByRole("button", { name: "剧本设置" }));
    assert.ok(utils.getByRole("button", { name: "分镜参考" }));
    assert.ok(utils.getByRole("button", { name: "临时角色/IP 绑定" }));

    fireEvent.click(utils.getByRole("button", { name: "分镜参考" }));
    assert.deepEqual(tabChanges, ["storyboard"]);
    assert.equal(supportButton.getAttribute("aria-expanded"), "false");
    assert.equal(utils.queryByRole("button", { name: "剧本设置" }), null);
  });

  it("uses the compact workspace header on storyboard support tabs", () => {
    const selectedScript = script();
    const workflowStatus: WorkflowStatus = {
      script: "ready",
      timeline: "ready",
      storyboard: "pending",
    };
    const tabChanges: string[] = [];
    const utils = render(
      <EpisodeWorkspaceHeader
        episode={episode()}
        script={selectedScript}
        scripts={[selectedScript]}
        selectedScriptId={selectedScript.id}
        workflowStatus={workflowStatus}
        resolvedVideos={resolvedVideosMissing()}
        activeTab="storyboard"
        onTabChange={(tab) => tabChanges.push(tab)}
        onNavigateBack={() => {}}
        onGenerateScript={() => {}}
        onGenerateTimeline={() => {}}
        onSelectScript={() => {}}
        storyboardActionLabel="进入片段分镜"
        onOpenStoryboard={() => {}}
      />,
      { container: dom.window.document.body },
    );

    assert.ok(
      dom.window.document.querySelector(
        '[data-episode-workspace-timeline-header="compact"]',
      ),
    );
    assert.equal(utils.queryByText("IP 剧集工作台"), null);
    assert.equal(utils.queryByText(/Timeline-first 生产控制台/), null);
    assert.ok(utils.getByRole("button", { name: "处理缺失片段" }));
    assert.ok(utils.getByLabelText("当前剧本"));
    assert.ok(
      dom.window.document.querySelector(
        '[data-production-step-rail="compact"]',
      ),
    );

    const supportButton = utils.getByRole("button", { name: "支持视图" });
    fireEvent.click(supportButton);
    fireEvent.click(utils.getByRole("button", { name: "剧本设置" }));
    assert.deepEqual(tabChanges, ["script"]);
  });

  it("keeps Timeline generation controls behind a compact setup affordance", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      const settingsButton = utils.getByRole("button", {
        name: "Timeline 生成设置",
      });
      assert.ok(settingsButton);
      assert.equal(settingsButton.textContent?.trim(), "");
      assert.ok(
        settingsButton.querySelector(
          '[data-timeline-settings-icon="pipeline"]',
        ),
      );
      assert.equal(
        utils.queryByRole("button", { name: "生成 Timeline" }),
        null,
      );
      assert.ok(utils.getAllByText("00:01.200").length >= 1);
      assert.equal(utils.queryByText("全片 00:01.200"), null);
      assert.equal(utils.queryByText("生成设置"), null);
      assert.equal(utils.queryByText("视图"), null);
      assert.equal(utils.queryByText("适配"), null);
    });
    const toolbar = dom.window.document.querySelector(
      '[data-timeline-toolbar="compact"]',
    );
    assert.ok(toolbar);
    assert.equal(
      toolbar.getAttribute("data-timeline-toolbar-intent"),
      "workspace-timeline",
    );
    assert.match(toolbar.className, /grid-cols-\[minmax\(0,1fr\)_auto\]/);
    assert.match(toolbar.className, /py-1/);
    assert.match(toolbar.className, /py-2/);
    assert.match(toolbar.className, /border-slate-200/);
    assert.match(toolbar.className, /bg-slate-50\/80/);
    assert.doesNotMatch(toolbar.className, /border-b-2/);
    assert.doesNotMatch(toolbar.className, /bg-blue-50\/70/);
    assert.doesNotMatch(toolbar.className, /flex-wrap/);
    const moduleLabel = dom.window.document.querySelector(
      "[data-timeline-module-label]",
    );
    const timelineIdentityBadge = dom.window.document.querySelector(
      '[data-timeline-identity-badge="primary"]',
    );
    assert.ok(timelineIdentityBadge);
    assert.equal(timelineIdentityBadge, moduleLabel);
    assert.equal(
      timelineIdentityBadge.getAttribute("data-timeline-identity-style"),
      "merged-heading",
    );
    const navigationLabel = timelineIdentityBadge.querySelector(
      '[data-timeline-navigation-label="sr-only"]',
    );
    const visibleTimelineTitle = timelineIdentityBadge.querySelector(
      '[data-timeline-header-title-text="visible"]',
    );
    const visibleTimelineKind = timelineIdentityBadge.querySelector(
      '[data-timeline-header-kind-text="visible"]',
    );
    assert.ok(navigationLabel);
    assert.ok(visibleTimelineKind);
    assert.ok(visibleTimelineTitle);
    assert.equal(navigationLabel.textContent?.trim(), "时间轴导航");
    assert.match(navigationLabel.className, /sr-only/);
    assert.equal(visibleTimelineKind.textContent, "时间轴");
    assert.equal(visibleTimelineTitle.textContent, "全片");
    assert.match(visibleTimelineTitle.className, /bg-slate-100/);
    assert.match(visibleTimelineTitle.className, /text-slate-600/);
    assert.match(visibleTimelineTitle.className, /font-semibold/);
    assert.doesNotMatch(visibleTimelineTitle.className, /bg-blue-50/);
    assert.doesNotMatch(visibleTimelineTitle.className, /text-blue-700/);
    assert.ok(
      timelineIdentityBadge.querySelector(
        '[data-timeline-header-scope-text="visible"]',
      ),
    );
    assert.equal(
      timelineIdentityBadge.querySelector(
        '[data-timeline-identity-icon="axis"]',
      ),
      null,
    );
    assert.doesNotMatch(timelineIdentityBadge.className, /bg-slate-950/);
    assert.match(timelineIdentityBadge.className, /bg-white/);
    assert.match(timelineIdentityBadge.className, /border-blue-200/);
    assert.match(timelineIdentityBadge.className, /text-blue-900/);
    assert.match(timelineIdentityBadge.className, /inset_3px_0_0/);
    assert.doesNotMatch(timelineIdentityBadge.className, /bg-blue-700/);
    assert.doesNotMatch(timelineIdentityBadge.className, /text-white/);
    assert.equal(
      moduleLabel?.querySelector('[data-timeline-header-title-text="visible"]')
        ?.textContent,
      "全片",
    );
    assert.match(
      moduleLabel?.textContent?.replace(/\s+/g, "") || "",
      /时间轴全片/,
    );
    assert.equal(
      moduleLabel?.getAttribute("data-timeline-module-label-style"),
      "editor-axis-title",
    );
    assert.match(moduleLabel?.className || "", /rounded-md/);
    assert.match(moduleLabel?.className || "", /border-blue-200/);
    assert.match(moduleLabel?.className || "", /bg-white/);
    assert.match(moduleLabel?.className || "", /text-blue-900/);
    assert.doesNotMatch(moduleLabel?.className || "", /bg-blue-700/);
    assert.doesNotMatch(moduleLabel?.className || "", /text-white/);
    assert.doesNotMatch(moduleLabel?.className || "", /bg-slate-900/);
    assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
    assert.equal(
      `${visibleTimelineTitle.textContent}${visibleTimelineKind.textContent}`,
      "全片时间轴",
    );
    assert.equal(toolbar.textContent?.includes("Timeline全片时间轴"), false);
    assert.equal(
      utils
        .getByRole("heading", { name: "全片时间轴" })
        .getAttribute("data-timeline-header-title"),
      "compact",
    );
    assert.equal(
      utils
        .getByRole("heading", { name: "全片时间轴" })
        .querySelector('[data-timeline-header-title-text="visible"]')
        ?.textContent,
      "全片",
    );
    const timelineWindowSummary = dom.window.document.querySelector(
      '[data-timeline-window-summary="visible"]',
    );
    assert.ok(timelineWindowSummary);
    assert.match(timelineWindowSummary.textContent || "", /1 段/);
    assert.match(timelineWindowSummary.textContent || "", /00:01/);
    assert.match(timelineWindowSummary.className, /bg-white/);
    assert.match(timelineWindowSummary.className, /font-bold/);
    const toolbarControls = dom.window.document.querySelector(
      '[data-timeline-toolbar-controls="compact"]',
    );
    assert.ok(toolbarControls);
    assert.equal(
      toolbarControls.getAttribute("data-timeline-toolbar-controls-surface"),
      "ghost-icons",
    );
    assert.match(toolbarControls.className, /bg-transparent/);
    assert.match(toolbarControls.className, /py-0/);
    assert.match(toolbarControls.className, /px-0\.5/);
    assert.match(toolbarControls.className, /shadow-none/);
    assert.match(toolbarControls.className, /shrink-0/);
    assert.doesNotMatch(toolbarControls.className, /border-blue-100/);
    assert.doesNotMatch(toolbarControls.className, /bg-white/);
    assert.doesNotMatch(toolbarControls.className, /shadow-sm/);
    const settingsButton = utils.getByRole("button", {
      name: "Timeline 生成设置",
    });
    assert.match(settingsButton.className, /h-7/);
    assert.match(settingsButton.className, /w-7/);
    assert.match(settingsButton.className, /bg-transparent/);
    assert.match(settingsButton.className, /border-transparent/);
    assert.doesNotMatch(settingsButton.className, /border-gray-200/);
    const viewControls = dom.window.document.querySelector(
      '[data-timeline-view-controls="collapsed"]',
    ) as HTMLDetailsElement | null;
    assert.ok(viewControls);
    assert.equal(viewControls.open, false);
    const viewSummary = viewControls.querySelector(
      "[data-timeline-view-summary]",
    ) as HTMLElement | null;
    assert.equal(viewSummary?.textContent?.trim(), "");
    assert.ok(
      viewSummary?.querySelector('[data-timeline-toolbar-icon="zoom"]'),
    );
    assert.match(viewSummary?.className || "", /h-7/);
    assert.match(viewSummary?.className || "", /w-7/);
    assert.match(viewSummary?.className || "", /hover:bg-white\/80/);
    assert.doesNotMatch(viewSummary?.className || "", /h-6/);
    const viewPanel = dom.window.document.querySelector(
      '[data-timeline-view-panel="compact"]',
    );
    assert.ok(viewPanel);
    const resetButton = utils.getByRole("button", {
      name: "重置为全片适配视图",
    });
    assert.equal(resetButton.textContent?.trim(), "适配全片");
    assert.equal(
      resetButton.getAttribute("data-timeline-reset-placement"),
      "view-panel",
    );
    assert.ok(viewPanel.contains(resetButton));
    assert.equal(toolbarControls.contains(resetButton), true);
    assert.equal(
      resetButton.parentElement?.getAttribute("data-timeline-view-panel"),
      "compact",
    );
    assert.ok(resetButton.querySelector('[data-timeline-toolbar-icon="fit"]'));
    const zoomRange = dom.window.document.querySelector(
      '[data-timeline-zoom-range="compact"]',
    );
    assert.ok(zoomRange);
    assert.equal(zoomRange.getAttribute("aria-label"), "视图缩放");
    fireEvent.click(utils.getByRole("button", { name: "Timeline 生成设置" }));
    await waitFor(() =>
      assert.ok(utils.getByRole("button", { name: "生成 Timeline" })),
    );
  });

  it("keeps missing render actions collapsed until clips are ready", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByText("成片"));
      assert.ok(utils.getByText("渲染/导出"));
      assert.ok(utils.getByText("待补 1 段"));
      assert.ok(utils.getByText("查看"));
    });
    const renderHeader = dom.window.document.querySelector(
      '[data-timeline-render-status-header="compact"]',
    );
    assert.ok(renderHeader);
    const renderLabel = renderHeader.querySelector(
      '[data-timeline-render-label="final-output"]',
    );
    assert.ok(renderLabel);
    assert.equal(renderLabel.textContent?.trim(), "成片");
    assert.equal(renderLabel.getAttribute("title"), "渲染/导出状态");
    assert.match(renderLabel.className, /text-\[11px\]/);
    assert.match(renderLabel.className, /text-slate-900/);
    assert.doesNotMatch(renderLabel.className, /text-gray-950/);
    assert.doesNotMatch(renderLabel.className, /text-sm/);
    assert.equal(utils.queryByText("导出状态"), null);
    const renderReadiness = renderHeader.querySelector(
      "[data-timeline-render-readiness]",
    );
    assert.equal(
      renderReadiness?.getAttribute("data-timeline-render-readiness"),
      "blocked",
    );
    assert.match(renderReadiness?.className || "", /text-slate-500/);
    assert.doesNotMatch(renderReadiness?.className || "", /text-amber-700/);
    assert.match(renderHeader.textContent || "", /待补 1 段/);
    assert.doesNotMatch(renderHeader.textContent || "", /渲染输出/);
    const summary = renderHeader.closest("summary");
    assert.ok(summary);
    assert.equal(
      summary.getAttribute("data-timeline-render-summary"),
      "inline",
    );
    assert.equal(
      summary.getAttribute("data-timeline-render-summary-layout"),
      "clustered-status-strip",
    );
    assert.match(summary.className, /flex/);
    assert.match(summary.className, /max-w-full/);
    assert.match(summary.className, /w-full/);
    assert.match(summary.className, /min-h-7/);
    assert.match(summary.className, /py-0\.5/);
    assert.doesNotMatch(
      summary.className,
      /grid-cols-\[minmax\(0,1fr\)_auto_auto\]/,
    );
    assert.doesNotMatch(summary.className, /border-l-2/);
    assert.doesNotMatch(summary.className, /border-l-slate-300/);
    assert.doesNotMatch(summary.className, /min-h-8/);
    assert.doesNotMatch(summary.className, /bg-white\/95/);
    assert.doesNotMatch(summary.className, /border-slate-200/);
    assert.doesNotMatch(summary.className, /rounded-md/);
    assert.doesNotMatch(summary.className, /shadow-\[0_1px_2px/);
    assert.doesNotMatch(summary.className, /inline-flex/);
    assert.doesNotMatch(summary.className, /min-h-11/);
    const readinessMeter = summary.querySelector(
      '[data-timeline-render-readiness-meter="inline-count"]',
    ) as HTMLElement | null;
    assert.ok(readinessMeter);
    assert.equal(readinessMeter.textContent?.trim(), "0/1 已备");
    assert.equal(readinessMeter.getAttribute("title"), "0/1 个片段就绪");
    assert.match(readinessMeter.className, /text-slate-600/);
    assert.match(readinessMeter.className, /inline-flex/);
    assert.match(readinessMeter.className, /ml-1/);
    assert.doesNotMatch(readinessMeter.className, /ml-auto/);
    assert.match(readinessMeter.className, /gap-1\.5/);
    assert.match(readinessMeter.className, /whitespace-nowrap/);
    assert.doesNotMatch(readinessMeter.className, /truncate/);
    assert.equal(readinessMeter.querySelector("div"), null);
    const readinessTrack = readinessMeter.querySelector(
      '[data-timeline-render-readiness-track="true"]',
    ) as HTMLElement | null;
    assert.ok(readinessTrack);
    assert.match(readinessTrack.className, /w-12/);
    assert.match(readinessTrack.className, /bg-slate-200/);
    const readinessFill = readinessMeter.querySelector(
      '[data-timeline-render-readiness-fill="true"]',
    ) as HTMLElement | null;
    assert.ok(readinessFill);
    assert.equal(readinessFill.style.width, "0%");
    assert.match(readinessFill.className, /bg-amber-400/);
    assert.doesNotMatch(readinessMeter.className, /justify-end/);
    const missingAction = summary.querySelector(
      '[data-timeline-render-missing-action="inline-link"]',
    );
    assert.ok(missingAction);
    assert.equal(missingAction.textContent?.trim(), "查看");
    assert.equal(missingAction.getAttribute("title"), "查看缺失片段");
    assert.match(missingAction.className, /text-slate-600/);
    assert.match(missingAction.className, /whitespace-nowrap/);
    assert.doesNotMatch(missingAction.className, /justify-end/);
    assert.doesNotMatch(missingAction.className, /border-slate-200/);
    assert.doesNotMatch(missingAction.className, /bg-slate-50/);
    assert.doesNotMatch(missingAction.className, /rounded/);
    assert.doesNotMatch(missingAction.className, /bg-amber-50/);
    assert.doesNotMatch(missingAction.className, /text-amber-700/);
    assert.doesNotMatch(missingAction.className, /border-amber-200/);
    const details = summary.closest("details");
    assert.ok(details);
    assert.equal(
      details.getAttribute("data-timeline-render-panel"),
      "collapsed",
    );
    assert.equal(details.hasAttribute("open"), false);
    const renderStrip = dom.window.document.querySelector(
      '[data-episode-render-strip="compact"]',
    );
    assert.ok(renderStrip);
    assert.equal(
      renderStrip.getAttribute("data-episode-render-strip-surface"),
      "inline-workflow-footer",
    );
    assert.equal(
      renderStrip.getAttribute("data-episode-render-strip-style"),
      "selected-clip-footer-dock",
    );
    assert.match(renderStrip.className, /border-t/);
    assert.match(renderStrip.className, /bg-slate-50\/70/);
    assert.doesNotMatch(renderStrip.className, /mx-3/);
    assert.doesNotMatch(renderStrip.className, /rounded-b-md/);
    assert.doesNotMatch(renderStrip.className, /rounded-lg/);
    assert.match(renderStrip.className, /border-slate-200/);
    assert.doesNotMatch(renderStrip.className, /border-t-0/);
    assert.doesNotMatch(renderStrip.className, /bg-slate-50\/60/);
    assert.doesNotMatch(renderStrip.className, /bg-transparent/);
    assert.doesNotMatch(renderStrip.className, /bg-white\/70/);
    assert.doesNotMatch(renderStrip.className, /\bbg-white\b/);
    assert.doesNotMatch(renderStrip.className, /border-y/);
    assert.doesNotMatch(renderStrip.className, /shadow-sm/);
    assert.match(renderStrip.className, /shadow-none/);
    assert.doesNotMatch(renderStrip.className, /bg-amber/);
    assert.equal(utils.queryByRole("button", { name: "渲染预览" }), null);
    assert.equal(utils.queryByRole("button", { name: "导出成片" }), null);

    fireEvent.click(summary);
    assert.equal(details.hasAttribute("open"), true);
    assert.ok(utils.getByText("缺失片段清单（1）"));
    assert.equal(utils.queryByRole("button", { name: "渲染预览" }), null);
    assert.equal(utils.queryByRole("button", { name: "导出成片" }), null);
  });

  it("falls back to the Timeline spec while resolved videos are loading", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(videoTimeline(), undefined, null), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByText("成片"));
      assert.ok(utils.getByText("待补 1 段"));
      assert.ok(utils.getByText("0/1 已备"));
    });

    assert.equal(utils.queryByText("无视频轨"), null);
    assert.equal(utils.queryByRole("button", { name: "渲染预览" }), null);
    assert.equal(utils.queryByRole("button", { name: "导出成片" }), null);
  });

  it("defaults to the first video clip so production entries are visible on deep links", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(dialogueBeforeVideoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByText("片段分镜管理"));
      assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
      const selectedContext = dom.window.document.querySelector(
        "[data-timeline-selected-context]",
      );
      assert.ok(selectedContext);
      assert.equal(
        selectedContext.getAttribute("data-timeline-selected-context-style"),
        "inline",
      );
      assert.match(selectedContext.className, /max-\[560px\]:sr-only/);
      assert.match(selectedContext.textContent || "", /当前/);
      assert.match(selectedContext.textContent || "", /视频 1/);
      assert.doesNotMatch(selectedContext.className, /bg-blue-50/);
      assert.doesNotMatch(selectedContext.className, /border-blue-100/);
      assert.ok(utils.getAllByText("视频 1").length >= 1);
      assert.ok(utils.getByLabelText("在时间轴中选择 视频 1"));
    });
    assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
    assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
  });

  it("honors a clip deep link when opening the Timeline workspace", async () => {
    mockWorkspaceFetch();
    const syncedClipIds: Array<string | null> = [];

    const utils = render(
      workspace(twoVideoTimeline(), "video_scene_1_beat_2_002", undefined, {
        onSelectedClipIdChange: (clipId) => syncedClipIds.push(clipId),
      }),
      {
        container: dom.window.document.body,
      },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByLabelText("在时间轴中选择 第二个视频"));
      assert.ok(utils.getAllByText("视频 2").length >= 1);
    });
    assert.deepEqual(syncedClipIds, ["video_scene_1_beat_2_002"]);

    const resyncedClipIds: Array<string | null> = [];
    utils.rerender(
      workspace(twoVideoTimeline(), undefined, undefined, {
        onSelectedClipIdChange: (clipId) => resyncedClipIds.push(clipId),
      }),
    );
    await waitFor(() =>
      assert.deepEqual(resyncedClipIds, ["video_scene_1_beat_2_002"]),
    );
  });

  it("falls back to the first video clip when a deep link clip id is stale", async () => {
    mockWorkspaceFetch();
    const syncedClipIds: Array<string | null> = [];

    const utils = render(
      workspace(twoVideoTimeline(), "video_scene_old", undefined, {
        selectedStoryboard: {
          frames: [
            {
              timeline_clip_id: "video_scene_old",
              start_ms: 0,
              end_ms: 1200,
              description: "旧 support item",
            },
          ],
        },
        onSelectedClipIdChange: (clipId) => syncedClipIds.push(clipId),
      }),
      {
        container: dom.window.document.body,
      },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByLabelText("在时间轴中选择 第一个视频"));
      assert.ok(utils.getAllByText("视频 1").length >= 1);
      assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
      assert.ok(utils.getByRole("button", { name: "生成/重做此片段视频" }));
    });
    assert.deepEqual(syncedClipIds, ["video_scene_1_beat_1_001"]);
  });

  it("syncs a valid clip id when fallback video clips use legacy id fields", async () => {
    mockWorkspaceFetch();
    const syncedClipIds: Array<string | null> = [];

    const utils = render(
      workspace(idOnlyVideoTimeline(), "video_scene_old", undefined, {
        onSelectedClipIdChange: (clipId) => syncedClipIds.push(clipId),
      }),
      {
        container: dom.window.document.body,
      },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("选中片段生产"));
      assert.ok(utils.getByLabelText("在时间轴中选择 历史 id 视频"));
      assert.ok(utils.getAllByText("视频 1").length >= 1);
      assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
    });
    assert.deepEqual(syncedClipIds, ["video_scene_legacy_id_001"]);
  });

  it("keeps Timeline generation visible when a stale clip link opens a dialogue-only timeline", async () => {
    mockWorkspaceFetch();
    const syncedClipIds: Array<string | null> = [];

    const utils = render(
      workspace(dialogueTimeline(), "video_scene_old", undefined, {
        onSelectedClipIdChange: (clipId) => syncedClipIds.push(clipId),
      }),
      {
        container: dom.window.document.body,
      },
    );

    await waitFor(() => {
      assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
      assert.ok(utils.getByRole("button", { name: "生成 Timeline" }));
      assert.ok(utils.getByLabelText("在时间轴中选择 native dialogue"));
      assert.ok(utils.getAllByText("对白 1").length >= 1);
      assert.equal(utils.queryByText("请选择时间轴片段。"), null);
      assert.equal(
        utils.queryByRole("button", { name: "生成片段分镜图" }),
        null,
      );
    });
    assert.deepEqual(syncedClipIds, [null]);
  });

  it("keeps an explicit Timeline frame visible when no clips are available yet", async () => {
    mockWorkspaceFetch();

    const utils = render(
      workspace(emptyTimeline(), "video_scene_old", undefined, {
        onSelectedClipIdChange: () => {},
      }),
      {
        container: dom.window.document.body,
      },
    );

    await waitFor(() => {
      assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
      assert.ok(utils.getByRole("button", { name: "生成 Timeline" }));
    });
    const timelineCanvas = dom.window.document.querySelector(
      '[data-timeline="workspace"]',
    );
    assert.ok(timelineCanvas);
    assert.equal(
      timelineCanvas.getAttribute("data-timeline-presence"),
      "explicit-production-time-axis",
    );
    assert.ok(
      timelineCanvas.querySelector('[data-timeline-track-row="video"]'),
    );
    assert.equal(utils.queryByText("请选择时间轴片段。"), null);
  });

  it("keeps storyboard support clicks mapped to the matching video clip", async () => {
    mockWorkspaceFetch();

    const utils = render(
      workspace(videoTimeline(), undefined, resolvedVideosMissing(), {
        selectedStoryboard: {
          frames: [
            {
              timeline_clip_id: "video_scene_1_beat_1_001",
              start_ms: 0,
              end_ms: 1200,
              description: "Storyboard support",
            },
          ],
        },
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => assert.ok(utils.getByText("片段分镜管理")));
    await waitFor(() =>
      assert.ok(
        utils.getAllByRole("button", {
          name: "在时间轴中选择 Storyboard support",
        }),
      ),
    );
    fireEvent.click(
      utils.getAllByRole("button", {
        name: "在时间轴中选择 Storyboard support",
      })[0],
    );

    await waitFor(() => {
      assert.ok(utils.getAllByText("视频 1").length >= 1);
      assert.ok(utils.getByText("片段分镜管理"));
      assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
    });
  });

  it("matches video clip scene_id against normalized scene ids", async () => {
    mockWorkspaceFetch({
      environments: [
        {
          id: 21,
          name: "哈尔滨科技公司开放式办公区（夜）",
          created_at: "2026-06-12T00:00:00Z",
          updated_at: "2026-06-12T00:00:00Z",
        },
      ],
    });

    const utils = render(
      workspace(sceneIdTimeline(), undefined, resolvedVideosMissing(), {
        normalizedScenes: [
          {
            id: 580,
            scene_number: "2",
            slug_line: "SCENE 2 - 升级推进",
            status: "draft",
            environment_id: 21,
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("场景 2 · 升级推进"));
      assert.ok(utils.getByRole("button", { name: "保存场景环境" }));
    });
    assert.equal(utils.queryByText("场景 2 · SCENE 2 - 升级推进"), null);
    assert.equal(
      utils.queryByText("未匹配规范化场景，当前环境仅用于片段生成参考。"),
      null,
    );
    assert.equal(
      (utils.getByLabelText("片段环境") as HTMLSelectElement).value,
      "21",
    );
  });

  it("keeps scene environment save hidden until an environment is selected", async () => {
    mockWorkspaceFetch({
      environments: [
        {
          id: 21,
          name: "哈尔滨科技公司开放式办公区（夜）",
          created_at: "2026-06-12T00:00:00Z",
          updated_at: "2026-06-12T00:00:00Z",
        },
      ],
    });

    const utils = render(
      workspace(sceneIdTimeline(), undefined, resolvedVideosMissing(), {
        normalizedScenes: [
          {
            id: 580,
            scene_number: "2",
            slug_line: "SCENE 2 - 升级推进",
            status: "draft",
            environment_id: null,
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      assert.ok(utils.getByText("场景 2 · 升级推进"));
    });
    assert.equal(utils.queryByText("场景 2 · SCENE 2 - 升级推进"), null);
    const environmentRow = dom.window.document.querySelector(
      "[data-clip-environment-row]",
    );
    assert.ok(environmentRow);
    assert.equal(
      environmentRow.getAttribute("data-clip-environment-layout"),
      "context-ribbon",
    );
    assert.equal((environmentRow as HTMLDetailsElement).open, false);
    assert.doesNotMatch(environmentRow.className, /border-t/);
    assert.doesNotMatch(environmentRow.className, /border-slate-100/);
    assert.match(environmentRow.className, /bg-transparent/);
    assert.doesNotMatch(environmentRow.className, /bg-white/);
    assert.match(environmentRow.className, /py-0/);
    assert.doesNotMatch(environmentRow.className, /rounded-lg/);
    assert.doesNotMatch(environmentRow.className, /shadow-sm/);
    const environmentSummary = dom.window.document.querySelector(
      '[data-clip-environment-summary="compact"]',
    ) as HTMLElement | null;
    assert.ok(environmentSummary);
    assert.ok(environmentSummary.textContent?.includes("场景环境"));
    assert.ok(environmentSummary.textContent?.includes("环境"));
    assert.ok(environmentSummary.textContent?.includes("未设置"));
    assert.ok(environmentSummary.textContent?.includes("更换"));
    assert.doesNotMatch(environmentSummary.className, /flex-wrap/);
    assert.match(environmentSummary.className, /overflow-hidden/);
    assert.match(environmentSummary.className, /min-h-6/);
    const environmentLabel = environmentSummary.querySelector(
      '[data-clip-environment-label="sr-only"]',
    ) as HTMLElement | null;
    const environmentKind = environmentSummary.querySelector(
      '[data-clip-environment-kind="visible"]',
    ) as HTMLElement | null;
    assert.ok(environmentLabel);
    assert.ok(environmentKind);
    assert.equal(environmentLabel.textContent?.trim(), "场景环境");
    assert.equal(environmentKind.textContent?.trim(), "环境");
    assert.match(environmentLabel.className, /sr-only/);
    assert.match(environmentKind.className, /text-slate-700/);
    assert.doesNotMatch(environmentKind.className, /sr-only/);
    assert.equal(
      environmentSummary.querySelector('[data-clip-environment-kind="hidden"]'),
      null,
    );
    const environmentScene = environmentSummary.querySelector(
      '[data-clip-environment-scene="inline"]',
    ) as HTMLElement | null;
    assert.ok(environmentScene);
    assert.equal(environmentScene.getAttribute("title"), "场景 2 · 升级推进");
    const hiddenSceneLabel = environmentScene.querySelector(".sr-only");
    assert.equal(hiddenSceneLabel?.textContent, "场景 2 · 升级推进");
    const visibleSceneLabel = environmentScene.querySelector(
      '[aria-hidden="true"]',
    );
    assert.equal(visibleSceneLabel?.textContent, "升级推进");
    assert.match(environmentScene.className || "", /font-medium/);
    assert.match(environmentScene.className || "", /text-slate-500/);
    assert.doesNotMatch(environmentScene.className || "", /bg-slate-100/);
    assert.doesNotMatch(environmentScene.className || "", /rounded/);
    const environmentChoice = environmentSummary.querySelector(
      '[data-clip-environment-choice="summary"]',
    );
    assert.ok(environmentChoice);
    assert.match(environmentChoice.className || "", /h-6/);
    assert.match(environmentChoice.className || "", /border-transparent/);
    assert.match(environmentChoice.className || "", /bg-transparent/);
    assert.match(environmentChoice.className || "", /text-slate-600/);
    assert.match(environmentChoice.className || "", /gap-1/);
    const environmentAction = environmentChoice.querySelector(
      '[data-clip-environment-action="inline"]',
    );
    assert.ok(environmentAction);
    assert.equal(environmentAction.textContent, "更换");
    assert.match(environmentAction.className || "", /text-blue-700/);
    assert.doesNotMatch(environmentChoice.className || "", /ml-auto/);
    assert.match(environmentChoice.className || "", /max-w-\[10rem\]/);
    assert.doesNotMatch(environmentChoice.className || "", /border-slate-200/);
    assert.doesNotMatch(environmentChoice.className || "", /bg-white/);
    assert.doesNotMatch(utils.getByLabelText("片段环境").className, /flex-1/);
    assert.equal(
      utils.queryByRole("button", {
        name: "保存场景环境",
      }),
      null,
    );
    assert.equal(environmentRow.textContent?.includes("保存场景环境"), false);

    fireEvent.click(environmentSummary);
    assert.equal((environmentRow as HTMLDetailsElement).open, true);
    fireEvent.change(utils.getByLabelText("片段环境"), {
      target: { value: "21" },
    });

    await waitFor(
      () => {
        const activeButton = utils.getByRole("button", {
          name: "保存场景环境",
        }) as HTMLButtonElement;
        assert.equal(activeButton.disabled, false);
        assert.equal(activeButton.textContent, "保存场景环境");
        assert.match(activeButton.className, /bg-blue-600/);
        assert.match(activeButton.className, /w-16/);
      },
      { timeout: 3000 },
    );
  });

  it("keeps environment support actions visually secondary", async () => {
    mockWorkspaceFetch();

    render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() =>
      assert.ok(
        dom.window.document.querySelector(
          '[data-clip-support-overflow="compact"]',
        ),
      ),
    );

    const supportSummary = dom.window.document.querySelector(
      '[data-clip-support-summary="ghost"]',
    );
    assert.ok(supportSummary);
    const environmentRow = supportSummary.closest(
      "[data-clip-environment-row]",
    ) as HTMLDetailsElement | null;
    assert.ok(environmentRow);
    assert.equal(environmentRow.open, false);
    assert.ok(supportSummary.closest("[data-clip-environment-controls]"));
    assert.equal(supportSummary.getAttribute("aria-label"), "更多片段支持操作");
    assert.equal(supportSummary.textContent?.trim(), "");
    assert.ok(
      supportSummary.querySelector('[data-clip-support-more-icon="dots"]'),
    );
    assert.match(supportSummary.className, /h-6/);
    assert.match(supportSummary.className, /w-6/);
    assert.doesNotMatch(supportSummary.className, /w-8/);
    assert.match(supportSummary.className, /border-transparent/);
    assert.match(supportSummary.className, /bg-transparent/);
    assert.doesNotMatch(supportSummary.className, /border-gray-200/);
    assert.doesNotMatch(supportSummary.className, /px-2/);
  });

  it("keeps selected clip script navigation visible outside collapsed support actions", async () => {
    mockWorkspaceFetch();
    const navigations: string[] = [];

    const utils = render(
      workspace(videoTimeline(), undefined, undefined, {
        onNavigateToScript: () => navigations.push("script"),
      }),
      {
        container: dom.window.document.body,
      },
    );

    await waitFor(() => {
      assert.ok(utils.getByRole("button", { name: "剧本" }));
      assert.ok(
        dom.window.document.querySelector(
          '[data-clip-support-overflow="compact"]',
        ),
      );
    });

    const scriptButton = utils.getByRole("button", { name: "剧本" });
    assert.ok(scriptButton.closest('[data-clip-script-support="visible"]'));
    assert.equal(
      scriptButton.closest('[data-clip-support-overflow="compact"]'),
      null,
    );
    const supportDetails = dom.window.document.querySelector(
      '[data-clip-support-overflow="compact"]',
    ) as HTMLDetailsElement;
    assert.ok(supportDetails);
    assert.equal(supportDetails.open, false);
    assert.equal(supportDetails.textContent?.includes("剧本"), false);

    fireEvent.click(scriptButton);
    assert.deepEqual(navigations, ["script"]);
  });

  it("shows scene environment save immediately for clips with a saved environment", async () => {
    mockWorkspaceFetch();

    const utils = render(
      workspace(sceneIdTimeline(), undefined, resolvedVideosMissing(), {
        normalizedScenes: [
          {
            id: 580,
            scene_number: "2",
            slug_line: "SCENE 2 - 升级推进",
            status: "draft",
            environment_id: 21,
          },
        ],
      }),
      { container: dom.window.document.body },
    );

    await waitFor(() => {
      const activeButton = utils.getByRole("button", {
        name: "保存场景环境",
      }) as HTMLButtonElement;
      assert.equal(activeButton.disabled, false);
      assert.match(activeButton.className, /bg-blue-600/);
    });
  });

  it("keeps the primary Timeline first while preserving selected clip production", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.ok(
      dom.window.document.querySelector(
        '[data-timeline-canvas-panel="primary"]',
      ),
    );
    assert.ok(
      dom.window.document.querySelector(
        '[data-timeline-header-title="compact"]',
      ),
    );

    {
      const timelineCanvasPanel = dom.window.document.querySelector(
        '[data-timeline-canvas-panel="primary"]',
      ) as HTMLElement | null;
      assert.ok(timelineCanvasPanel);
      assert.equal(timelineCanvasPanel.id, "episode-timeline-canvas");
      assert.equal(
        timelineCanvasPanel.getAttribute("data-timeline-canvas-presence-frame"),
        "restored-visible-axis",
      );
      assert.equal(
        timelineCanvasPanel.getAttribute("data-timeline-selection-visibility"),
        "anchor",
      );
      assert.match(timelineCanvasPanel.className, /scroll-mt-16/);
      assert.match(timelineCanvasPanel.className, /rounded-xl/);
      assert.match(timelineCanvasPanel.className, /bg-blue-50\/35/);
      assert.match(timelineCanvasPanel.className, /p-1/);
      assert.match(timelineCanvasPanel.className, /inset_0_0_0_1px/);
      const workspaceShell = dom.window.document
        .querySelector("[data-timeline-canvas]")
        ?.closest(".grid");
      assert.ok(workspaceShell);
      assert.match(workspaceShell.className, /!h-auto/);
      assert.match(workspaceShell.className, /!min-h-0/);
      assert.match(workspaceShell.className, /!overflow-visible/);
      assert.ok(dom.window.document.querySelector(".min-h-0.overflow-y-auto"));
      assert.ok(dom.window.document.querySelector("[data-timeline-canvas]"));
      const overview = dom.window.document.querySelector(
        "[data-timeline-overview]",
      );
      const overviewRail = dom.window.document.querySelector(
        "[data-timeline-overview-rail]",
      );
      assert.ok(overview);
      const timelineCanvas = dom.window.document.querySelector(
        "[data-timeline-canvas]",
      );
      assert.ok(timelineCanvas);
      assert.equal(timelineCanvas.getAttribute("data-timeline"), "workspace");
      assert.equal(
        timelineCanvas.getAttribute("data-timeline-density"),
        "primary",
      );
      assert.equal(
        timelineCanvas.getAttribute("data-timeline-presence"),
        "explicit-production-time-axis",
      );
      assert.equal(
        timelineCanvas.getAttribute("data-timeline-surface"),
        "dominant-workspace-axis",
      );
      assert.equal(
        timelineCanvas.getAttribute("data-timeline-visibility-contract"),
        "first-screen-primary",
      );
      assert.equal(
        timelineCanvas.getAttribute("data-timeline-visual-priority"),
        "main-time-axis",
      );
      assert.equal(
        timelineCanvas.getAttribute("data-timeline-fit-to-width"),
        "true",
      );
      assert.match(timelineCanvas.className, /rounded-lg/);
      assert.equal(
        timelineCanvas.getAttribute("aria-label"),
        "时间轴导航：片段时间轴定位区",
      );
      assert.match(timelineCanvas.className, /\bborder\b/);
      assert.match(timelineCanvas.className, /border-slate-300/);
      assert.match(timelineCanvas.className, /border-l-8/);
      assert.match(timelineCanvas.className, /border-l-blue-600/);
      assert.match(timelineCanvas.className, /shadow-md/);
      assert.match(timelineCanvas.className, /shadow-blue-100\/80/);
      assert.match(timelineCanvas.className, /ring-1/);
      assert.match(timelineCanvas.className, /ring-blue-100\/80/);
      assert.doesNotMatch(timelineCanvas.className, /border-blue-100/);
      assert.doesNotMatch(timelineCanvas.className, /border-l-2/);
      assert.doesNotMatch(timelineCanvas.className, /border-l-4/);
      assert.doesNotMatch(timelineCanvas.className, /border-l-blue-500\/70/);
      assert.doesNotMatch(timelineCanvas.className, /shadow-\[0_8px_18px/);
      assert.doesNotMatch(timelineCanvas.className, /border-2/);
      assert.doesNotMatch(timelineCanvas.className, /ring-2/);
      assert.doesNotMatch(timelineCanvas.className, /shadow-none/);
      assert.equal(
        overview.getAttribute("data-timeline-overview-layout"),
        "visible-overview-axis",
      );
      assert.equal(
        overview.getAttribute("data-timeline-overview-density"),
        "primary-navigation",
      );
      assert.equal(
        overview.getAttribute("data-timeline-overview-role"),
        "full-episode-time-axis",
      );
      assert.equal(
        overview.getAttribute("data-timeline-overview-visibility"),
        "full-episode-context-rail",
      );
      assert.match(overview.className, /border-slate-200/);
      assert.match(overview.className, /bg-slate-50\/80/);
      assert.doesNotMatch(overview.className, /border-blue-200/);
      assert.doesNotMatch(overview.className, /bg-blue-50/);
      assert.ok(overviewRail);
      assert.match(overviewRail.className, /h-8/);
      assert.match(overviewRail.className, /border-slate-300/);
      assert.match(overviewRail.className, /bg-white/);
      assert.match(overviewRail.className, /shadow-slate-200\/80/);
      assert.doesNotMatch(overviewRail.className, /border-blue-300/);
      assert.doesNotMatch(overviewRail.className, /shadow-blue-100/);
      assert.match(
        overviewRail.parentElement?.className || "",
        /grid-cols-\[auto_minmax\(0,1fr\)_auto\]/,
      );
      assert.doesNotMatch(
        overviewRail.parentElement?.className || "",
        /3\.5rem/,
      );
      const overviewLabel = dom.window.document.querySelector(
        '[data-timeline-overview-track-label="video"]',
      );
      assert.ok(overviewLabel);
      assert.equal(
        overviewLabel.getAttribute(
          "data-timeline-overview-track-label-visibility",
        ),
        "visible",
      );
      assert.doesNotMatch(overviewLabel.className, /sr-only/);
      assert.match(overviewLabel.textContent || "", /总览/);
      assert.match(
        overviewLabel.getAttribute("title") || "",
        /^全片时间轴 · 视频/,
      );
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-navigation-label="sr-only"]',
        ),
      );
      assert.ok(utils.getByText("全片概览"));
      assert.ok(utils.getByText("总览"));
      const timelineViewport = dom.window.document.querySelector(
        "[data-timeline-viewport]",
      ) as HTMLElement | null;
      assert.ok(timelineViewport);
      assert.equal(
        timelineViewport.getAttribute("data-timeline-scrollbar"),
        "subtle",
      );
      assert.match(timelineViewport.className, /overflow-x-scroll/);
      assert.match(timelineViewport.className, /border-slate-200/);
      assert.match(GLOBAL_CSS, /scrollbar-color:\s*#cbd5e1 transparent;/);
      assert.match(GLOBAL_CSS, /height:\s*6px;/);
      assert.match(GLOBAL_CSS, /background:\s*transparent;/);
      assert.match(GLOBAL_CSS, /background-clip:\s*content-box;/);
      assert.doesNotMatch(GLOBAL_CSS, /height:\s*10px;/);
      assert.ok(
        dom.window.document.querySelector("[data-timeline-module-label]"),
      );
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-overview-selected-marker="true"]',
        ),
      );
      const selectedRange = dom.window.document.querySelector(
        '[data-timeline-selected-range="true"]',
      ) as HTMLElement | null;
      const selectedCursor = dom.window.document.querySelector(
        '[data-timeline-selected-cursor="true"]',
      ) as HTMLElement | null;
      assert.ok(selectedRange);
      assert.ok(selectedCursor);
      assert.ok(Number.parseFloat(selectedRange.style.width) >= 14);
      assert.match(selectedRange.className, /border-blue-400\/35/);
      assert.match(selectedRange.className, /bg-blue-50\/25/);
      assert.match(selectedCursor.className, /w-px/);
      assert.match(selectedCursor.className, /bg-blue-500\/45/);
      assert.doesNotMatch(selectedCursor.className, /border-l-2/);
      assert.ok(dom.window.document.querySelector("[data-timeline-grid]"));
      const ruler = dom.window.document.querySelector(
        "[data-timeline-ruler]",
      ) as HTMLElement | null;
      assert.ok(ruler);
      assert.equal(ruler.style.height, "44px");
      assert.equal(
        ruler.getAttribute("data-timeline-ruler-visual"),
        "timecode-axis",
      );
      assert.match(ruler.className, /border-b/);
      assert.match(ruler.className, /border-slate-200/);
      assert.doesNotMatch(ruler.className, /border-teal/);
      assert.match(ruler.className, /bg-slate-50\/90/);
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-header-kind-text="visible"]',
        ),
      );
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-ruler-origin-secondary="true"]',
        ),
      );
      assert.equal(utils.queryByText("时间尺"), null);
      const rulerOrigin = dom.window.document.querySelector(
        "[data-timeline-ruler-origin]",
      ) as HTMLElement | null;
      assert.ok(rulerOrigin);
      assert.equal(
        rulerOrigin.getAttribute("data-timeline-ruler-origin-layout"),
        "timeline-axis-label",
      );
      assert.equal(rulerOrigin.style.width, "112px");
      assert.match(rulerOrigin.className, /flex-col/);
      assert.match(rulerOrigin.className, /justify-center/);
      assert.match(rulerOrigin.className, /bg-white/);
      assert.match(rulerOrigin.className, /text-blue-800/);
      assert.match(rulerOrigin.className, /inset_4px_0_0/);
      assert.match(rulerOrigin.className, /border-blue-200/);
      assert.doesNotMatch(rulerOrigin.className, /bg-blue-700/);
      assert.doesNotMatch(rulerOrigin.className, /bg-slate-900/);
      assert.doesNotMatch(rulerOrigin.className, /justify-between/);
      const rulerOriginPrimary = dom.window.document.querySelector(
        '[data-timeline-ruler-origin-primary="true"]',
      ) as HTMLElement | null;
      const rulerOriginSecondary = dom.window.document.querySelector(
        '[data-timeline-ruler-origin-secondary="true"]',
      ) as HTMLElement | null;
      assert.ok(rulerOriginPrimary);
      assert.ok(rulerOriginSecondary);
      assert.equal(rulerOriginPrimary.textContent, "时间轴");
      assert.equal(rulerOriginSecondary.textContent, "刻度");
      assert.doesNotMatch(rulerOriginSecondary.className, /sr-only/);
      assert.match(rulerOriginPrimary.className, /font-extrabold/);
      assert.match(rulerOriginSecondary.className, /font-semibold/);
      assert.match(rulerOriginSecondary.className, /text-slate-500/);
      assert.doesNotMatch(rulerOriginSecondary.className, /text-blue-600/);
      const axisLine = dom.window.document.querySelector(
        "[data-timeline-axis-line]",
      ) as HTMLElement | null;
      assert.ok(axisLine);
      assert.equal(axisLine.style.top, "43px");
      assert.match(axisLine.className, /border-b-2/);
      assert.match(axisLine.className, /border-blue-500\/70/);
      assert.match(axisLine.className, /shadow-\[0_1px_0/);
      assert.doesNotMatch(axisLine.className, /border-blue-300\/45/);
      assert.doesNotMatch(axisLine.className, /shadow-none/);
      const firstGridLine = dom.window.document.querySelector(
        "[data-timeline-grid] > div",
      ) as HTMLElement | null;
      assert.ok(firstGridLine);
      assert.equal(
        firstGridLine.getAttribute("data-timeline-grid-line-depth"),
        "ruler-fade",
      );
      assert.match(firstGridLine.className, /bg-gradient-to-b/);
      assert.match(firstGridLine.className, /from-slate-300\/80/);
      assert.match(firstGridLine.className, /via-slate-200\/25/);
      assert.match(firstGridLine.className, /to-transparent/);
      assert.doesNotMatch(firstGridLine.className, /bg-slate-300\/80/);
      const firstTick = dom.window.document.querySelector(
        "[data-timeline-tick]",
      ) as HTMLElement | null;
      assert.ok(firstTick);
      assert.match(firstTick.className, /border-slate-300\/70/);
      assert.ok(
        dom.window.document.querySelector('[data-timeline-track-row="video"]'),
      );
      const videoAxisLine = dom.window.document.querySelector(
        '[data-timeline-video-axis-line="true"]',
      );
      assert.ok(videoAxisLine);
      assert.match(videoAxisLine.className, /h-7/);
      assert.match(videoAxisLine.className, /border-y/);
      assert.match(videoAxisLine.className, /border-teal-500\/35/);
      assert.match(videoAxisLine.className, /bg-teal-500\/20/);
      const videoTrackLabel = dom.window.document.querySelector(
        '[data-timeline-track-label="video"]',
      ) as HTMLElement | null;
      assert.ok(videoTrackLabel);
      assert.equal(videoTrackLabel.style.width, "112px");
      assert.match(videoTrackLabel.className, /bg-white/);
      assert.match(videoTrackLabel.className, /border-slate-200/);
      assert.match(videoTrackLabel.className, /text-slate-900/);
      assert.match(videoTrackLabel.className, /inset_4px_0_0/);
      assert.doesNotMatch(videoTrackLabel.className, /bg-slate-900/);
      assert.doesNotMatch(videoTrackLabel.className, /text-white/);
      assert.match(videoTrackLabel.className, /font-bold/);
      const videoPrimaryLaneLabel = videoTrackLabel.querySelector(
        '[data-timeline-primary-lane-label="visible"]',
      ) as HTMLElement | null;
      assert.ok(videoPrimaryLaneLabel);
      assert.equal(videoPrimaryLaneLabel.textContent, "主时间轴");
      assert.match(videoPrimaryLaneLabel.className, /text-\[9px\]/);
      assert.match(videoPrimaryLaneLabel.className, /text-slate-500/);
      assert.doesNotMatch(videoPrimaryLaneLabel.className, /sr-only/);
      assert.match(videoTrackLabel.textContent || "", /视频/);
      assert.match(videoTrackLabel.textContent || "", /主时间轴/);
      const videoTrackRow = dom.window.document.querySelector(
        '[data-timeline-track-row="video"]',
      ) as HTMLElement | null;
      assert.ok(videoTrackRow);
      assert.equal(
        videoTrackRow.getAttribute("data-timeline-primary-lane"),
        "video-production",
      );
      assert.equal(
        videoTrackRow.getAttribute("data-timeline-primary-lane-visual"),
        "dominant-time-axis",
      );
      assert.match(videoTrackRow.className, /border-slate-400/);
      assert.match(videoTrackRow.className, /bg-white/);
      assert.doesNotMatch(videoTrackRow.className, /bg-teal-50/);
      assert.doesNotMatch(videoTrackRow.className, /bg-slate-100/);
      assert.ok(
        dom.window.document.querySelector('[data-timeline-item-type="video"]'),
      );
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-video-clip-frame="filmstrip"]',
        ),
      );
      assert.ok(utils.getByText("主线"));
      assert.ok(
        dom.window.document.querySelector('[data-timeline-item-type="video"]'),
      );
      assert.ok(utils.getByText("选中片段生产"));
      assert.equal(utils.queryByText("当前片段"), null);
      const currentBar = dom.window.document.querySelector(
        '[data-clip-current-bar="identity"]',
      );
      assert.ok(currentBar);
      assert.equal(
        currentBar.getAttribute("data-clip-current-bar-layout"),
        "identity-chip",
      );
      assert.match(currentBar.className, /text-slate-700/);
      assert.match(currentBar.className, /px-0/);
      assert.match(currentBar.className, /py-0/);
      assert.doesNotMatch(currentBar.className, /border-l-2/);
      assert.doesNotMatch(currentBar.className, /border-l-blue-500/);
      assert.doesNotMatch(currentBar.className, /rounded-sm/);
      assert.doesNotMatch(currentBar.className, /rounded-md/);
      assert.doesNotMatch(currentBar.className, /bg-slate-50\/80/);
      assert.doesNotMatch(currentBar.className, /bg-slate-50\/70/);
      assert.match(currentBar.textContent || "", /视频 1/);
      assert.match(
        dom.window.document.body.textContent || "",
        /时间轴窗口\s*00:00/,
      );
      assert.match(dom.window.document.body.textContent || "", /全片\s*时间轴/);
      assert.match(dom.window.document.body.textContent || "", /全片概览/);
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-reset-placement="view-panel"]',
        ),
      );
    }
    const mainLayout = dom.window.document.querySelector(
      '[data-episode-timeline-main-layout="timeline-first-with-production"]',
    );
    assert.ok(mainLayout);
    const mainChildren = Array.from(mainLayout.children) as HTMLElement[];
    assert.equal(
      mainChildren[0]?.getAttribute("data-timeline-canvas-panel"),
      "primary",
    );
    assert.equal(
      mainChildren[1]?.getAttribute("data-clip-production-panel"),
      "dock",
    );
    assert.equal(
      mainChildren[2]?.getAttribute("data-episode-render-strip"),
      "compact",
    );
    const text = dom.window.document.body.textContent || "";
    assert.ok(text.indexOf("时间轴窗口") < text.indexOf("选中片段生产"));
    assert.ok(mainChildren[0]?.nextElementSibling === mainChildren[1]);
    assert.ok(mainChildren[1]?.nextElementSibling === mainChildren[2]);
  });

  it("keeps compact Timeline dimensions large enough to read as a full timeline", () => {
    const compactLayout = timelineLayoutForMeasuredWidth(390);

    assert.equal(compactLayout.compact, true);
    assert.equal(compactLayout.tickLaneHeight, 44);
    assert.equal(compactLayout.trackHeight, 104);
    assert.equal(compactLayout.secondaryTrackHeight, 16);
    assert.equal(compactLayout.trackLabelWidth, 88);
    assert.equal(compactLayout.trackGap, 1);

    const regularLayout = timelineLayoutForMeasuredWidth(760);
    assert.equal(regularLayout.compact, false);
    assert.equal(regularLayout.tickLaneHeight, 44);
    assert.equal(regularLayout.trackHeight, 116);
    assert.equal(regularLayout.secondaryTrackHeight, 18);
    assert.equal(regularLayout.trackLabelWidth, 112);
    assert.equal(regularLayout.trackGap, 2);
  });

  it("brings the primary Timeline back into view when clip selection changes off-screen", async () => {
    mockWorkspaceFetch();
    const originalScrollIntoView =
      dom.window.HTMLElement.prototype.scrollIntoView;
    const originalGetBoundingClientRect =
      dom.window.HTMLElement.prototype.getBoundingClientRect;
    const scrollCalls: Array<ScrollIntoViewOptions | boolean | undefined> = [];

    dom.window.HTMLElement.prototype.scrollIntoView = function (options) {
      if (
        (this as HTMLElement).getAttribute("data-timeline-canvas-panel") ===
        "primary"
      ) {
        scrollCalls.push(options);
      }
    };
    dom.window.HTMLElement.prototype.getBoundingClientRect = function () {
      if (
        (this as HTMLElement).getAttribute("data-timeline-canvas-panel") ===
        "primary"
      ) {
        return {
          x: 0,
          y: 1200,
          top: 1200,
          bottom: 1525,
          left: 0,
          right: 1340,
          width: 1340,
          height: 325,
          toJSON: () => ({}),
        } as DOMRect;
      }
      return originalGetBoundingClientRect.call(this);
    };

    try {
      render(workspace(videoTimeline()), {
        container: dom.window.document.body,
      });

      await waitFor(() => {
        assert.ok(
          dom.window.document.querySelector(
            '[data-timeline-canvas-panel="primary"]',
          ),
        );
        assert.ok(scrollCalls.length > 0);
      });
      assert.deepEqual(scrollCalls[0], {
        block: "start",
        behavior: "smooth",
      });
    } finally {
      dom.window.HTMLElement.prototype.getBoundingClientRect =
        originalGetBoundingClientRect;
      dom.window.HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
    }
  });

  it("brings the primary Timeline back when only a sliver remains visible", async () => {
    mockWorkspaceFetch();
    const originalScrollIntoView =
      dom.window.HTMLElement.prototype.scrollIntoView;
    const originalGetBoundingClientRect =
      dom.window.HTMLElement.prototype.getBoundingClientRect;
    const scrollCalls: Array<ScrollIntoViewOptions | boolean | undefined> = [];

    dom.window.HTMLElement.prototype.scrollIntoView = function (options) {
      if (
        (this as HTMLElement).getAttribute("data-timeline-canvas-panel") ===
        "primary"
      ) {
        scrollCalls.push(options);
      }
    };
    dom.window.HTMLElement.prototype.getBoundingClientRect = function () {
      if (
        (this as HTMLElement).getAttribute("data-timeline-canvas-panel") ===
        "primary"
      ) {
        return {
          x: 0,
          y: 610,
          top: 610,
          bottom: 935,
          left: 0,
          right: 1340,
          width: 1340,
          height: 325,
          toJSON: () => ({}),
        } as DOMRect;
      }
      return originalGetBoundingClientRect.call(this);
    };

    try {
      render(workspace(videoTimeline()), {
        container: dom.window.document.body,
      });

      await waitFor(() => assert.ok(scrollCalls.length > 0));
      assert.deepEqual(scrollCalls[0], {
        block: "start",
        behavior: "smooth",
      });
    } finally {
      dom.window.HTMLElement.prototype.getBoundingClientRect =
        originalGetBoundingClientRect;
      dom.window.HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
    }
  });

  it("shows a full-episode overview above the scrollable Timeline lanes", async () => {
    mockWorkspaceFetch();

    render(workspace(twoVideoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      const overview = dom.window.document.querySelector(
        "[data-timeline-overview]",
      );
      const viewport = dom.window.document.querySelector(
        "[data-timeline-grid]",
      );
      assert.ok(overview);
      assert.ok(viewport);
      assert.ok(
        (overview.compareDocumentPosition(viewport) &
          dom.window.Node.DOCUMENT_POSITION_FOLLOWING) !==
          0,
      );
      assert.equal(
        dom.window.document.querySelectorAll(
          '[data-timeline-overview-item="video"]',
        ).length,
        2,
      );
      const overviewItems = Array.from(
        dom.window.document.querySelectorAll(
          '[data-timeline-overview-item="video"]',
        ),
      );
      assert.ok(
        overviewItems.some((item) => item.className.includes("bg-teal-50/80")),
      );
      assert.ok(
        overviewItems.some((item) =>
          item.className.includes("border-teal-200/80"),
        ),
      );
      assert.equal(
        overviewItems.some((item) =>
          item.className.includes("bg-slate-200/80"),
        ),
        false,
      );
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-overview-track-label="video"]',
        ),
      );
      assert.equal(
        dom.window.document
          .querySelector('[data-timeline-overview-track-label="video"]')
          ?.getAttribute("data-timeline-overview-track-label-visibility"),
        "visible",
      );
      assert.doesNotMatch(
        dom.window.document.querySelector(
          '[data-timeline-overview-track-label="video"]',
        )?.className || "",
        /sr-only/,
      );
      assert.match(
        dom.window.document.querySelector(
          '[data-timeline-overview-track-label="video"]',
        )?.textContent || "",
        /总览/,
      );
      assert.equal(
        dom.window.document
          .querySelector('[data-timeline-overview-track-label="video"]')
          ?.getAttribute("title"),
        "全片时间轴 · 视频",
      );
      assert.equal(
        overview.getAttribute("data-timeline-overview-layout"),
        "visible-overview-axis",
      );
      assert.equal(
        overview.getAttribute("data-timeline-overview-density"),
        "primary-navigation",
      );
      assert.equal(
        overview.getAttribute("data-timeline-overview-role"),
        "full-episode-time-axis",
      );
      assert.equal(
        overview.getAttribute("data-timeline-overview-visibility"),
        "full-episode-context-rail",
      );
      assert.match(
        dom.window.document.querySelector("[data-timeline-overview-rail]")
          ?.className || "",
        /h-8/,
      );
      assert.ok(
        dom.window.document.querySelector(
          '[data-timeline-overview-selected-marker="true"]',
        ),
      );
    });
  });

  it("shows the selected clip summary before production commands", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(
        dom.window.document.querySelector("[data-clip-production-summary]"),
      );
      assert.equal(
        dom.window.document
          .querySelector("[data-clip-production-summary]")
          ?.getAttribute("data-clip-production-summary-layout"),
        "inline-identity",
      );
      const clipTypeBadge = dom.window.document.querySelector(
        '[data-clip-type-badge="neutral"]',
      ) as HTMLElement | null;
      assert.ok(clipTypeBadge);
      assert.equal(clipTypeBadge.textContent?.trim(), "当前视频");
      assert.equal(
        clipTypeBadge.getAttribute("data-clip-type-badge-visibility"),
        "sr-only",
      );
      assert.match(clipTypeBadge.className, /sr-only/);
      assert.doesNotMatch(clipTypeBadge.className, /text-blue-700/);
      assert.doesNotMatch(clipTypeBadge.className, /max-\[760px\]:sr-only/);
      assert.doesNotMatch(clipTypeBadge.className, /rounded-sm/);
      assert.doesNotMatch(clipTypeBadge.className, /bg-slate-100/);
      assert.doesNotMatch(clipTypeBadge.className, /text-slate-700/);
      assert.doesNotMatch(clipTypeBadge.className, /border-l/);
      assert.doesNotMatch(clipTypeBadge.className, /border-slate-300/);
      assert.doesNotMatch(clipTypeBadge.className, /bg-green-50/);
      assert.doesNotMatch(clipTypeBadge.className, /border-green-200/);
      assert.doesNotMatch(clipTypeBadge.className, /text-green-700/);
      assert.doesNotMatch(clipTypeBadge.className, /rounded-md/);
      const productionKicker = dom.window.document.querySelector(
        '[data-clip-production-kicker="current-video"]',
      ) as HTMLElement | null;
      assert.ok(productionKicker);
      assert.equal(
        productionKicker.getAttribute("data-clip-production-kicker-layout"),
        "title-first",
      );
      assert.equal(
        dom.window.document.querySelector(
          '[data-clip-production-heading="current"]',
        ),
        null,
      );
      assert.ok(utils.getByRole("button", { name: "生成片段分镜图" }));
      assert.equal(
        utils.getByText("缺视频").getAttribute("title"),
        "缺少视频素材",
      );
      const videoStatus = utils.getByText("缺视频");
      const productionMeta = dom.window.document.querySelector(
        '[data-clip-production-meta="true"]',
      ) as HTMLElement | null;
      assert.ok(productionMeta);
      assert.match(productionMeta.className, /max-\[760px\]:sr-only/);
      assert.doesNotMatch(productionMeta.className, /mt-0\.5/);
      assert.equal(
        productionMeta.getAttribute("title"),
        "片段时间 00:00 - 00:01 · 待复核",
      );
      assert.equal(
        productionMeta.textContent?.replace(/\s+/g, " ").trim(),
        "00:00 - 00:01待复核",
      );
      const reviewStatus = productionMeta.querySelector(
        '[data-clip-production-review-status="sr-only"]',
      ) as HTMLElement | null;
      assert.ok(reviewStatus);
      assert.equal(reviewStatus.textContent, "待复核");
      assert.match(reviewStatus.className, /sr-only/);
      const mobileLabel = dom.window.document.querySelector(
        '[data-clip-production-mobile-label="true"]',
      ) as HTMLElement | null;
      assert.ok(mobileLabel);
      assert.equal(mobileLabel.textContent, "视频 1");
      assert.equal(mobileLabel.getAttribute("title"), "视频 1");
      assert.match(mobileLabel.className, /max-\[760px\]:inline/);
      assert.match(mobileLabel.className, /truncate/);
      const mobileTime = dom.window.document.querySelector(
        '[data-clip-production-mobile-time="true"]',
      ) as HTMLElement | null;
      assert.ok(mobileTime);
      assert.equal(mobileTime.textContent, "00:00-00:01");
      assert.match(mobileTime.className, /max-\[760px\]:inline/);
      const visibleLabel = dom.window.document.querySelector(
        '[data-clip-production-title="full"]',
      ) as HTMLElement | null;
      assert.ok(visibleLabel);
      assert.equal(visibleLabel.getAttribute("title"), "视频 1");
      assert.match(visibleLabel.className, /max-\[760px\]:sr-only/);
      assert.match(visibleLabel.className, /shrink-0/);
      assert.match(visibleLabel.className, /max-w-\[4\.5rem\]/);
      assert.doesNotMatch(visibleLabel.className, /flex-1/);
      assert.notEqual(
        visibleLabel.compareDocumentPosition(videoStatus) &
          dom.window.Node.DOCUMENT_POSITION_FOLLOWING,
        0,
      );
      assert.equal(
        videoStatus.closest('[data-clip-production-kicker="current-video"]'),
        productionKicker,
      );
      assert.equal(
        videoStatus.closest('[data-clip-production-meta="true"]'),
        null,
      );
      assert.equal(
        videoStatus.getAttribute("data-clip-video-status"),
        "inline",
      );
      assert.equal(
        videoStatus.getAttribute("data-clip-video-state"),
        "missing",
      );
      assert.match(videoStatus.className, /text-amber-700/);
      assert.doesNotMatch(videoStatus.className, /border/);
      assert.doesNotMatch(videoStatus.className, /bg-amber-50/);
      assert.equal(utils.queryByText("缺少视频素材"), null);
    });

    const productionPanel = dom.window.document.querySelector(
      '[data-clip-production-panel="dock"]',
    );
    const commandRail = dom.window.document.querySelector(
      '[data-clip-command-rail="compact"]',
    );
    assert.ok(productionPanel);
    assert.ok(commandRail);
    assert.equal(
      productionPanel.getAttribute("data-clip-production-surface"),
      "inline-workflow-band",
    );
    assert.equal(
      productionPanel.getAttribute("data-clip-production-surface-style"),
      "selected-clip-dock",
    );
    assert.equal(
      commandRail.getAttribute("data-clip-command-layout"),
      "compact-video-primary",
    );
    assert.match(productionPanel.className, /border-t/);
    assert.doesNotMatch(productionPanel.className, /border-l-2/);
    assert.doesNotMatch(productionPanel.className, /border-teal/);
    assert.match(productionPanel.className, /border-slate-200/);
    assert.match(productionPanel.className, /bg-slate-50\/70/);
    assert.match(productionPanel.className, /shadow-none/);
    assert.doesNotMatch(productionPanel.className, /border-y/);
    assert.doesNotMatch(productionPanel.className, /bg-slate-50\/80/);
    assert.doesNotMatch(productionPanel.className, /\bbg-white\b/);
    assert.doesNotMatch(productionPanel.className, /shadow-\[/);
    const productionPanelInner =
      productionPanel.firstElementChild as HTMLElement | null;
    assert.ok(productionPanelInner);
    assert.match(productionPanelInner.className, /py-1\.5/);
    assert.doesNotMatch(productionPanelInner.className, /space-y-1/);
    const currentBar = dom.window.document.querySelector(
      '[data-clip-current-bar="identity"]',
    ) as HTMLElement | null;
    const productionTopRow = dom.window.document.querySelector(
      '[data-clip-production-top-row="action-dock"]',
    ) as HTMLElement | null;
    assert.ok(productionTopRow);
    assert.match(productionTopRow.className, /grid/);
    assert.equal(
      productionTopRow.getAttribute("data-clip-production-top-row-layout"),
      "selected-clip-production-dock",
    );
    assert.match(productionTopRow.className, /px-0/);
    assert.match(productionTopRow.className, /py-0/);
    assert.match(productionTopRow.className, /1040px/);
    assert.match(
      productionTopRow.className,
      /minmax\(14rem,18rem\)_minmax\(30rem,max-content\)_minmax\(10rem,1fr\)/,
    );
    assert.match(productionTopRow.className, /gap-x-2/);
    assert.match(productionTopRow.className, /gap-y-1/);
    assert.doesNotMatch(productionTopRow.className, /minmax\(12rem,16rem\)/);
    assert.doesNotMatch(productionTopRow.className, /minmax\(18rem,28rem\)/);
    assert.doesNotMatch(productionTopRow.className, /minmax\(14rem,20rem\)/);
    assert.doesNotMatch(productionTopRow.className, /0\.72fr/);
    assert.doesNotMatch(productionTopRow.className, /1\.28fr/);
    assert.doesNotMatch(productionTopRow.className, /rounded-md/);
    assert.doesNotMatch(productionTopRow.className, /border-slate-200/);
    assert.doesNotMatch(productionTopRow.className, /bg-white\/95/);
    assert.doesNotMatch(productionTopRow.className, /px-1\.5/);
    assert.doesNotMatch(productionTopRow.className, /py-1/);
    assert.doesNotMatch(productionTopRow.className, /shadow-\[0_1px_2px/);
    assert.doesNotMatch(productionTopRow.className, /shadow-\[inset_0_1px_0/);
    assert.ok(currentBar);
    assert.equal(
      currentBar.getAttribute("data-clip-current-bar-layout"),
      "identity-chip",
    );
    assert.match(currentBar.className, /text-slate-700/);
    assert.match(currentBar.className, /px-0/);
    assert.match(currentBar.className, /py-0/);
    assert.doesNotMatch(currentBar.className, /border-l-2/);
    assert.doesNotMatch(currentBar.className, /border-l-blue-500/);
    assert.doesNotMatch(currentBar.className, /border-slate-200/);
    assert.doesNotMatch(currentBar.className, /rounded-sm/);
    assert.doesNotMatch(currentBar.className, /bg-slate-50\/80/);
    assert.doesNotMatch(currentBar.className, /px-2/);
    assert.doesNotMatch(currentBar.className, /py-1/);
    assert.doesNotMatch(currentBar.className, /min-\[1040px\]:bg-transparent/);
    assert.doesNotMatch(currentBar.className, /shadow-\[inset_3px_0_0/);
    assert.doesNotMatch(currentBar.className, /rounded-lg/);
    const inlineSupportPanel = dom.window.document.querySelector(
      '[data-clip-support-panel="inline"]',
    ) as HTMLElement | null;
    assert.ok(inlineSupportPanel);
    assert.equal(inlineSupportPanel.parentElement, productionTopRow);
    assert.match(inlineSupportPanel.className, /min-w-0/);
    assert.doesNotMatch(commandRail.className, /border-b/);
    const commandSurface = commandRail.querySelector(
      '[data-clip-command-surface="action-tray"]',
    );
    assert.ok(commandSurface);
    assert.equal(
      commandSurface.getAttribute("data-clip-command-surface-style"),
      "flat-action-cluster",
    );
    assert.equal(
      commandSurface.getAttribute("data-clip-command-density"),
      "readable",
    );
    assert.doesNotMatch(commandSurface.className, /overflow-hidden/);
    assert.match(commandSurface.className, /min-\[720px\]:rounded-md/);
    assert.match(commandSurface.className, /min-\[720px\]:border/);
    assert.match(commandSurface.className, /min-\[720px\]:border-slate-200/);
    assert.doesNotMatch(commandSurface.className, /bg-slate-50\/80/);
    assert.match(commandSurface.className, /bg-transparent/);
    assert.match(commandSurface.className, /p-0/);
    assert.match(commandSurface.className, /shadow-none/);
    assert.match(commandSurface.className, /min-\[720px\]:bg-white/);
    assert.match(commandSurface.className, /min-\[720px\]:p-0\.5/);
    assert.match(commandSurface.className, /min-\[720px\]:shadow-\[0_1px_2px/);
    assert.match(commandSurface.className, /720px/);
    assert.doesNotMatch(commandSurface.className, /rounded-lg/);
    assert.doesNotMatch(commandSurface.className, /p-px/);
    assert.doesNotMatch(commandSurface.className, /shadow-sm/);
    const commandGrid = commandSurface.firstElementChild as HTMLElement | null;
    assert.ok(commandGrid);
    assert.match(commandGrid.className, /grid-cols-2/);
    assert.match(commandGrid.className, /max-content_max-content/);
    assert.match(commandGrid.className, /minmax\(15rem,17rem\)/);
    assert.match(commandGrid.className, /justify-start/);
    assert.match(commandGrid.className, /gap-1/);
    assert.match(commandGrid.className, /min-\[720px\]:gap-0\.5/);
    assert.doesNotMatch(commandGrid.className, /divide-x/);
    assert.doesNotMatch(commandGrid.className, /divide-slate-200/);
    assert.doesNotMatch(commandGrid.className, /justify-end/);
    assert.doesNotMatch(commandGrid.className, /gap-px/);
    assert.doesNotMatch(commandGrid.className, /0\.9fr/);
    assert.doesNotMatch(commandGrid.className, /0\.68fr/);
    assert.doesNotMatch(commandGrid.className, /1\.62fr/);
    assert.doesNotMatch(commandGrid.className, /divide-gray-200/);
    assert.doesNotMatch(commandGrid.className, /1\.75fr/);
    const commandCards = Array.from(
      dom.window.document.querySelectorAll("[data-clip-command-card]"),
    ) as HTMLElement[];
    assert.equal(commandCards.length, 3);
    assert.deepEqual(
      commandCards.map((card) => card.getAttribute("data-clip-command-card")),
      ["storyboard", "keyframes", "video"],
    );
    assert.deepEqual(
      commandCards.map(
        (card) =>
          card
            .querySelector("[data-clip-command-step]")
            ?.getAttribute("data-clip-command-step"),
      ),
      ["1", "2", "3"],
    );
    assert.equal(
      dom.window.document.querySelectorAll(
        '[data-clip-command-card-header="step"]',
      ).length,
      3,
    );
    assert.equal(
      dom.window.document.querySelectorAll(
        '[data-clip-command-card-actions="inline"]',
      ).length,
      3,
    );
    commandCards.forEach((card) => {
      assert.equal(
        card.firstElementChild?.getAttribute("data-clip-command-card-actions"),
        "inline",
      );
    });
    Array.from(
      dom.window.document.querySelectorAll(
        '[data-clip-command-card-header="step"]',
      ),
    ).forEach((header) => {
      assert.match((header as HTMLElement).className, /hidden/);
    });
    Array.from(
      dom.window.document.querySelectorAll("[data-clip-command-step]"),
    ).forEach((step) => {
      assert.match(
        (step as HTMLElement).closest(".hidden")?.className || "",
        /hidden/,
      );
    });
    assert.equal(
      commandCards[0].getAttribute("data-clip-command-card-tone"),
      "default",
    );
    assert.equal(
      commandCards[2].getAttribute("data-clip-command-card-tone"),
      "primary",
    );
    assert.match(commandCards[0].className, /max-\[719px\]:order-1/);
    assert.match(commandCards[1].className, /max-\[719px\]:order-2/);
    assert.match(commandCards[2].className, /max-\[719px\]:order-3/);
    assert.match(commandCards[2].className, /max-\[719px\]:col-span-2/);
    assert.doesNotMatch(commandCards[0].className, /col-span-2/);
    assert.doesNotMatch(commandCards[1].className, /col-span-2/);
    commandCards.forEach((card) => {
      assert.doesNotMatch(card.className, /rounded-md/);
      assert.doesNotMatch(card.className, /border-/);
      assert.doesNotMatch(card.className, /bg-blue-50/);
      assert.doesNotMatch(card.className, /bg-white/);
    });
    assert.ok(
      dom.window.document.querySelector(
        '[data-clip-action-group="storyboard"]',
      ),
    );
    assert.match(
      dom.window.document.querySelector('[data-clip-action-group="storyboard"]')
        ?.className || "",
      /gap-0/,
    );
    assert.match(
      dom.window.document.querySelector('[data-clip-action-group="storyboard"]')
        ?.className || "",
      /w-auto/,
    );
    assert.match(
      dom.window.document.querySelector('[data-clip-action-group="storyboard"]')
        ?.className || "",
      /w-full/,
    );
    assert.ok(
      dom.window.document.querySelector('[data-clip-action-group="video"]'),
    );
    assert.ok(
      dom.window.document.querySelector('[data-clip-action-group="keyframes"]'),
    );
    assert.match(
      dom.window.document.querySelector('[data-clip-action-group="keyframes"]')
        ?.className || "",
      /w-auto/,
    );
    assert.doesNotMatch(
      dom.window.document.querySelector('[data-clip-action-group="keyframes"]')
        ?.className || "",
      /rounded-md/,
    );
    assert.match(
      dom.window.document.querySelector('[data-clip-action-group="video"]')
        ?.className || "",
      /gap-0/,
    );
    assert.match(
      dom.window.document.querySelector('[data-clip-action-group="video"]')
        ?.className || "",
      /w-auto/,
    );
    assert.match(
      dom.window.document.querySelector('[data-clip-action-group="video"]')
        ?.className || "",
      /w-full/,
    );
    assert.equal(
      dom.window.document.querySelectorAll(
        '[data-clip-parameter-details="compact"]',
      ).length,
      2,
    );
    const parameterSummaries = Array.from(
      dom.window.document.querySelectorAll(
        '[data-clip-parameter-details="compact"] summary',
      ),
    );
    const storyboardParameterSummary =
      utils.getByLabelText("展开分镜参数与参考");
    const videoParameterSummary = utils.getByLabelText("展开视频绑定与参数");
    parameterSummaries.forEach((summary) => {
      assert.equal(summary.textContent?.trim(), "");
      assert.equal(
        summary.getAttribute("data-clip-parameter-trigger-shape"),
        "attached-more",
      );
      const iconWrapper = summary.querySelector("[data-clip-parameter-icon]");
      assert.equal(
        iconWrapper?.getAttribute("data-clip-parameter-icon"),
        "controls",
      );
      const icon = iconWrapper?.querySelector("svg");
      assert.ok(icon);
      assert.equal(icon?.querySelectorAll("circle").length, 0);
      assert.ok(icon?.querySelector("path"));
      assert.match(summary.className, /h-8/);
      assert.match(summary.className, /w-7/);
      assert.match(summary.className, /rounded-l-none/);
      assert.match(summary.className, /rounded-r-md/);
      assert.match(summary.className, /border-l-0/);
      assert.match(summary.className, /px-0/);
      assert.doesNotMatch(summary.className, /min-w-\[3\.25rem\]/);
      assert.doesNotMatch(summary.className, /h-6/);
      assert.doesNotMatch(summary.className, /h-7/);
      assert.doesNotMatch(summary.className, /h-9/);
      assert.doesNotMatch(summary.className, /w-6/);
      assert.doesNotMatch(summary.className, /w-9/);
    });
    assert.equal(
      storyboardParameterSummary.getAttribute("data-clip-parameter-tone"),
      "default",
    );
    assert.match(storyboardParameterSummary.className, /border-slate-200/);
    assert.match(storyboardParameterSummary.className, /bg-white/);
    assert.match(storyboardParameterSummary.className, /text-slate-600/);
    assert.equal(
      videoParameterSummary.getAttribute("data-clip-parameter-tone"),
      "primary",
    );
    assert.doesNotMatch(videoParameterSummary.className, /bg-blue-50/);
    assert.match(videoParameterSummary.className, /bg-blue-600/);
    assert.match(videoParameterSummary.className, /text-white/);
    assert.match(videoParameterSummary.className, /border-blue-600/);
    assert.equal(utils.queryByText("绑定与参数"), null);
    assert.equal(utils.queryByText(/参数与参考/), null);
    assert.equal(utils.queryByText("参数"), null);
    const summary = dom.window.document.querySelector(
      "[data-clip-production-summary]",
    );
    const storyboardButton = utils.getByRole("button", {
      name: "生成片段分镜图",
    });
    const keyframeButton = utils.getByRole("button", {
      name: "生成首尾帧",
    });
    const videoButton = utils.getByRole("button", {
      name: "生成/重做此片段视频",
    });
    assert.equal(storyboardButton.textContent?.trim(), "生成片段分镜图");
    assert.equal(storyboardButton.getAttribute("title"), "生成片段分镜图");
    assert.equal(keyframeButton.textContent?.trim(), "生成首尾帧");
    assert.equal(videoButton.textContent?.trim(), "生成/重做此片段视频");
    assert.equal(
      videoButton.getAttribute("title"),
      "先完成片段分镜图和首尾帧后才能生视频",
    );
    assert.doesNotMatch(storyboardButton.textContent || "", /分镜图分镜图/);
    assert.doesNotMatch(keyframeButton.textContent || "", /首尾帧首尾帧/);
    assert.ok(storyboardButton.querySelector("svg"));
    assert.ok(keyframeButton.querySelector("svg"));
    assert.ok(videoButton.querySelector("svg"));
    assert.match(storyboardButton.className, /border-slate-200/);
    assert.match(keyframeButton.className, /border-slate-200/);
    assert.match(storyboardButton.className, /bg-white/);
    assert.match(keyframeButton.className, /bg-white/);
    assert.match(storyboardButton.className, /!h-8/);
    assert.match(storyboardButton.className, /whitespace-nowrap/);
    assert.match(keyframeButton.className, /!h-8/);
    assert.match(videoButton.className, /!h-8/);
    assert.match(storyboardButton.className, /min-w-0/);
    assert.match(storyboardButton.className, /flex-1/);
    assert.match(storyboardButton.className, /min-\[720px\]:min-w-\[9\.5rem\]/);
    assert.match(keyframeButton.className, /w-full/);
    assert.match(keyframeButton.className, /min-w-0/);
    assert.match(keyframeButton.className, /whitespace-nowrap/);
    assert.match(keyframeButton.className, /min-\[720px\]:min-w-\[8\.5rem\]/);
    assert.match(videoButton.className, /min-w-0/);
    assert.match(videoButton.className, /whitespace-nowrap/);
    assert.match(videoButton.className, /flex-1/);
    assert.match(videoButton.className, /min-\[720px\]:min-w-\[15rem\]/);
    assert.match(videoButton.className, /min-\[720px\]:max-w-\[17rem\]/);
    assert.match(storyboardButton.className, /rounded-l-md/);
    assert.match(storyboardButton.className, /rounded-r-none/);
    assert.match(keyframeButton.className, /rounded-md/);
    assert.match(videoButton.className, /rounded-l-md/);
    assert.match(videoButton.className, /rounded-r-none/);
    assert.match(videoButton.className, /border-blue-600/);
    assert.match(videoButton.className, /bg-blue-600/);
    assert.match(videoButton.className, /shadow-none/);
    assert.doesNotMatch(videoButton.className, /shadow-blue/);
    assert.ok(summary);
    assert.ok(Boolean(summary.compareDocumentPosition(storyboardButton) & 4));
    const text = dom.window.document.body.textContent || "";
    assert.ok(text.indexOf("首尾帧") < text.indexOf("场景环境"));
  });

  it("keeps engineering clip ids out of the default asset audit header", async () => {
    mockWorkspaceFetch();

    render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() =>
      assert.ok(
        dom.window.document.querySelector(
          '[data-clip-support-overflow="compact"]',
        ),
      ),
    );

    const supportOverflow = dom.window.document.querySelector(
      '[data-clip-support-overflow="compact"]',
    );
    assert.ok(supportOverflow);
    assert.equal(
      supportOverflow.getAttribute("data-clip-support-placement"),
      "environment",
    );
    assert.ok(supportOverflow.closest("[data-clip-environment-row]"));
    const assetAuditSummary = Array.from(
      supportOverflow.querySelectorAll("summary"),
    ).find((summary) => summary.textContent?.includes("资产审计"));
    assert.ok(assetAuditSummary);
    assert.equal(
      assetAuditSummary.textContent?.includes("video_scene_1_beat_1_001"),
      false,
    );
    assert.ok(assetAuditSummary.textContent?.includes("0 条"));

    const assetAuditDetails = assetAuditSummary.closest("details");
    const supportLayout = supportOverflow.closest("[data-clip-support-layout]");
    assert.equal(
      supportLayout?.getAttribute("data-clip-support-layout"),
      "compact",
    );
    assert.ok(supportOverflow.textContent?.includes("辅助"));
    assert.ok(supportOverflow.textContent?.includes("辅助操作"));
    assert.ok(supportOverflow.textContent?.includes("资产审计"));
    assert.ok(
      assetAuditDetails?.textContent?.includes(
        "片段 ID：video_scene_1_beat_1_001",
      ),
    );
  });

  it("promotes asset audit only when the selected clip has asset records", async () => {
    mockWorkspaceFetch({
      clipAssets: [
        {
          id: 11,
          business_id: "clip_asset_11",
          timeline_id: 8,
          timeline_version: 3,
          clip_id: "video_scene_1_beat_1_001",
          asset_role: "generated_video",
          media_asset_id: 99,
          media_asset: {
            id: 99,
            business_id: "asset_99",
            asset_type: "video",
            origin: "generated",
            file_url: "https://example.com/generated.mp4",
            created_at: "2026-06-12T00:00:00Z",
            updated_at: "2026-06-12T00:00:00Z",
          },
          source: "operator_rework",
          created_at: "2026-06-12T00:00:00Z",
        },
      ],
    });

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() =>
      assert.ok(
        dom.window.document.querySelector('[data-clip-support-layout="split"]'),
      ),
    );

    const assetAuditLabel = utils.getByText("资产审计");
    const supportLayout = assetAuditLabel.closest("[data-clip-support-layout]");
    assert.equal(
      supportLayout?.getAttribute("data-clip-support-layout"),
      "split",
    );
    assert.ok(dom.window.document.body.textContent?.includes("1 条"));
  });

  it("keeps secondary clip navigation behind a collapsed support disclosure", async () => {
    mockWorkspaceFetch();

    render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() =>
      assert.ok(
        dom.window.document.querySelector(
          '[data-clip-support-overflow="compact"]',
        ),
      ),
    );

    const supportDetails = dom.window.document.querySelector(
      '[data-clip-support-overflow="compact"]',
    ) as HTMLDetailsElement;
    assert.ok(supportDetails);
    assert.equal(supportDetails.open, false);
    assert.ok(supportDetails.closest("[data-clip-environment-row]"));
    const supportSummary = supportDetails.querySelector("summary");
    assert.equal(supportSummary?.textContent?.trim(), "");
    assert.ok(
      supportSummary?.querySelector('[data-clip-support-more-icon="dots"]'),
    );
    assert.ok(supportDetails.textContent?.includes("辅助操作"));
    assert.equal(supportDetails.textContent?.includes("剧本"), false);
    assert.ok(supportDetails.textContent?.includes("替换片段"));
    assert.ok(supportDetails.textContent?.includes("任务"));
  });

  it("keeps long episode Timeline lanes readable instead of squeezing them into one screen", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(longEpisodeTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
    });

    const timelineCanvas = dom.window.document.querySelector(
      "[data-timeline-canvas]",
    );
    assert.equal(
      timelineCanvas?.getAttribute("data-timeline-fit-to-width"),
      "true",
    );
    assert.equal(
      timelineCanvas?.getAttribute("data-timeline-scale-mode"),
      "readable-window",
    );
    assert.ok(utils.getByRole("button", { name: "重置为可读时间轴视图" }));
    const timelineViewport = dom.window.document.querySelector(
      "[data-timeline-viewport]",
    );
    const timelineContent = dom.window.document.querySelector(
      "[data-timeline-content]",
    ) as HTMLElement | null;
    assert.equal(
      timelineViewport?.getAttribute("data-timeline-scroll-mode"),
      "scrollable-readable-lanes",
    );
    assert.equal(
      timelineContent?.getAttribute("data-timeline-content-scale-mode"),
      "readable-window",
    );
    assert.ok(Number.parseFloat(timelineContent?.style.width || "0") > 1000);

    const firstClipButton = utils.getByLabelText(
      "在时间轴中选择 视频 1",
    ) as HTMLButtonElement;
    const lastClipButton = utils.getByLabelText(
      "在时间轴中选择 视频 2",
    ) as HTMLButtonElement;
    const firstClipWidth = Number.parseFloat(firstClipButton.style.width);
    const firstClipLeft = Number.parseFloat(firstClipButton.style.left);
    const lastClipLeft = Number.parseFloat(lastClipButton.style.left);
    assert.equal(firstClipButton.textContent?.trim(), "视频 1");
    assert.equal(firstClipWidth, 54);
    assert.equal(
      firstClipButton.getAttribute("data-timeline-item-visual"),
      "timeline-bar",
    );
    assert.equal(Number.parseFloat(firstClipButton.style.height), 44);
    assert.ok(lastClipLeft > 1000);
    assert.ok(firstClipLeft < lastClipLeft);
    assert.equal(firstClipButton.style.borderWidth, "2px");
    assert.match(firstClipButton.className, /ring-1/);
    assert.match(firstClipButton.className, /ring-blue-500\/55/);
    assert.match(firstClipButton.className, /ring-offset-1/);
    assert.match(firstClipButton.className, /shadow-sm/);
    assert.match(firstClipButton.style.backgroundColor, /219,\s*234,\s*254/);
    assert.match(firstClipButton.style.borderColor, /59,\s*130,\s*246/);
    assert.equal(
      firstClipButton.getAttribute("data-timeline-item-tone"),
      "primary-selected",
    );
    const selectedTopRail = firstClipButton.querySelector(
      '[data-timeline-video-clip-rail="top"]',
    );
    assert.equal(
      selectedTopRail?.getAttribute("data-timeline-video-clip-rail-tone"),
      "selected",
    );
    assert.match(selectedTopRail?.className || "", /bg-blue-600\/60/);
    assert.equal(lastClipButton.style.borderWidth, "1px");
    assert.equal(
      lastClipButton.getAttribute("data-timeline-item-tone"),
      "primary-muted",
    );
    const mutedTopRail = lastClipButton.querySelector(
      '[data-timeline-video-clip-rail="top"]',
    );
    assert.equal(
      mutedTopRail?.getAttribute("data-timeline-video-clip-rail-tone"),
      "muted",
    );
    assert.match(mutedTopRail?.className || "", /bg-teal-400\/35/);
    assert.doesNotMatch(mutedTopRail?.className || "", /bg-teal-500\/45/);
    assert.doesNotMatch(mutedTopRail?.className || "", /bg-slate-900/);
    assert.match(lastClipButton.className, /shadow-\[inset_0_0_0_1px/);
    assert.match(lastClipButton.style.backgroundColor, /240,\s*253,\s*250/);
    assert.match(lastClipButton.style.borderColor, /94,\s*234,\s*212/);
    assert.doesNotMatch(lastClipButton.className, /shadow-md/);
  });

  it("keeps long fitted video labels visible while suppressing cramped labels", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(denseFittedVideoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
    });

    const secondClipButton = utils.getByLabelText(
      "在时间轴中选择 视频 2",
    ) as HTMLButtonElement;
    const shortClipButton = utils.getByLabelText(
      "在时间轴中选择 视频 3",
    ) as HTMLButtonElement;
    const finalShortClipButton = utils.getByLabelText(
      "在时间轴中选择 视频 4",
    ) as HTMLButtonElement;
    assert.equal(secondClipButton.textContent?.trim(), "视频 2");
    assert.equal(
      secondClipButton.getAttribute("data-timeline-label-visibility"),
      "visible",
    );
    assert.equal(shortClipButton.textContent?.trim(), "");
    assert.equal(finalShortClipButton.textContent?.trim(), "");
    assert.equal(
      shortClipButton.getAttribute("data-timeline-label-visibility"),
      "hidden",
    );
    assert.equal(
      finalShortClipButton.getAttribute("data-timeline-label-visibility"),
      "hidden",
    );
    assert.match(shortClipButton.getAttribute("aria-label") || "", /视频 3/);
    assert.match(shortClipButton.getAttribute("title") || "", /视频 3/);
    assert.match(
      finalShortClipButton.getAttribute("aria-label") || "",
      /视频 4/,
    );
    assert.equal(
      shortClipButton
        .querySelector("[data-timeline-item-label-mode]")
        ?.getAttribute("data-timeline-item-label-mode") ?? null,
      null,
    );
    assert.ok(Number.parseFloat(shortClipButton.style.width) >= 24);
    assert.ok(Number.parseFloat(finalShortClipButton.style.width) >= 24);
  });

  it("suppresses cramped mobile fitted video labels without hiding readable clips", () => {
    const utils = render(
      <div>
        <TimelineItemButton
          item={{
            id: "selected",
            startMs: 0,
            endMs: 3320,
            label: "视频 1",
            displayLabel: "视频 1",
            type: "video",
          }}
          minStart={0}
          onSelect={() => {}}
          pxPerMs={0.01}
          selectedItemId="selected"
          trackId="video"
          trackColor="#2563eb"
          trackHeight={86}
          zoom={0.1}
        />
        <TimelineItemButton
          item={{
            id: "readable",
            startMs: 9000,
            endMs: 15500,
            label: "视频 4",
            displayLabel: "视频 4",
            type: "video",
          }}
          minStart={0}
          onSelect={() => {}}
          pxPerMs={0.01}
          selectedItemId="selected"
          trackId="video"
          trackColor="#2563eb"
          trackHeight={86}
          zoom={0.1}
        />
        <TimelineItemButton
          item={{
            id: "cramped",
            startMs: 6800,
            endMs: 7600,
            label: "视频 5",
            displayLabel: "视频 5",
            type: "video",
          }}
          minStart={0}
          onSelect={() => {}}
          pxPerMs={0.01}
          selectedItemId="selected"
          trackId="video"
          trackColor="#2563eb"
          trackHeight={86}
          zoom={0.1}
        />
      </div>,
      { container: dom.window.document.body },
    );

    const selected = utils.getByLabelText("在时间轴中选择 视频 1");
    const readable = utils.getByLabelText("在时间轴中选择 视频 4");
    const cramped = utils.getByLabelText("在时间轴中选择 视频 5");

    assert.equal(selected.textContent?.trim(), "视频 1");
    assert.equal(readable.textContent?.trim(), "视频 4");
    assert.equal(cramped.textContent?.trim(), "");
    assert.equal(
      readable.getAttribute("data-timeline-label-visibility"),
      "visible",
    );
    assert.equal(
      cramped.getAttribute("data-timeline-label-visibility"),
      "hidden",
    );
    assert.ok(Number.parseFloat((readable as HTMLElement).style.width) >= 46);
    assert.equal(Number.parseFloat((cramped as HTMLElement).style.width), 10);
  });

  it("keeps compact Timeline overview focused on a visible full-episode axis", () => {
    render(
      <TimelineOverview
        compact
        minStart={0}
        maxEnd={10000}
        selectedItemId="video-1"
        tracks={[
          {
            id: "video",
            label: "视频",
            items: [
              {
                id: "video-1",
                startMs: 0,
                endMs: 3000,
                label: "视频 1",
                type: "video",
              },
              {
                id: "video-2",
                startMs: 3000,
                endMs: 10000,
                label: "视频 2",
                type: "video",
              },
            ],
          },
        ]}
      />,
      { container: dom.window.document.body },
    );

    const overview = dom.window.document.querySelector(
      "[data-timeline-overview]",
    );
    const label = dom.window.document.querySelector(
      '[data-timeline-overview-track-label="video"]',
    );
    const range = dom.window.document.querySelector(
      "[data-timeline-overview-range-visibility]",
    );
    const rail = dom.window.document.querySelector(
      "[data-timeline-overview-rail]",
    );

    assert.ok(overview);
    assert.ok(label);
    assert.ok(range);
    assert.ok(rail);
    assert.equal(
      label.getAttribute("data-timeline-overview-track-label-visibility"),
      "visible",
    );
    assert.doesNotMatch(label.className, /sr-only/);
    assert.match(label.textContent || "", /总览/);
    assert.equal(label.getAttribute("title"), "全片时间轴 · 视频");
    assert.equal(
      range.getAttribute("data-timeline-overview-range-visibility"),
      "sr-only",
    );
    assert.match(range.className, /sr-only/);
    assert.equal(rail.parentElement?.children.length, 3);
    assert.match(
      rail.parentElement?.className || "",
      /grid-cols-\[auto_minmax\(0,1fr\)\]/,
    );
    assert.doesNotMatch(rail.parentElement?.className || "", /3\.5rem/);
    assert.equal(
      overview.getAttribute("data-timeline-overview-density"),
      "primary-navigation",
    );
    assert.match(rail.className, /h-7/);
    assert.match(rail.className, /border-slate-300/);
    assert.match(rail.className, /shadow-slate-200\/80/);
    assert.doesNotMatch(rail.className, /border-blue-300/);
    assert.doesNotMatch(rail.className, /shadow-blue-100/);
  });

  it("keeps distant support track clips readable in the scrollable Timeline", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(longEpisodeWithSupportTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
      assert.ok(utils.getByLabelText("在时间轴中选择 长对白提示"));
      assert.ok(utils.getByLabelText("在时间轴中选择 长分镜提示"));
    });

    const dialogueClipButton = utils.getByLabelText(
      "在时间轴中选择 长对白提示",
    ) as HTMLButtonElement;
    const storyboardClipButton = utils.getByLabelText(
      "在时间轴中选择 长分镜提示",
    ) as HTMLButtonElement;
    const videoClipButton = utils.getByLabelText(
      "在时间轴中选择 视频 2",
    ) as HTMLButtonElement;
    assert.equal(dialogueClipButton.textContent?.trim(), "");
    assert.equal(storyboardClipButton.textContent?.trim(), "");
    assert.match(
      dialogueClipButton.getAttribute("aria-label") || "",
      /长对白提示/,
    );
    assert.match(
      storyboardClipButton.getAttribute("aria-label") || "",
      /长分镜提示/,
    );
    assert.equal(videoClipButton.textContent?.trim(), "视频 2");
    assert.match(videoClipButton.getAttribute("aria-label") || "", /视频 2/);
    assert.equal(
      dialogueClipButton.getAttribute("data-timeline-item-visual"),
      "support-context",
    );
    assert.equal(
      storyboardClipButton.getAttribute("data-timeline-item-visual"),
      "support-context",
    );
    assert.match(dialogueClipButton.style.backgroundColor, /148,\s*163,\s*184/);
    assert.match(
      storyboardClipButton.style.backgroundColor,
      /148,\s*163,\s*184/,
    );
    assert.equal(dialogueClipButton.style.borderColor, "transparent");
    assert.equal(storyboardClipButton.style.borderColor, "transparent");
    assert.equal(dialogueClipButton.style.borderWidth, "0px");
    assert.equal(storyboardClipButton.style.borderWidth, "0px");
    assert.equal(Number.parseFloat(dialogueClipButton.style.height), 8);
    assert.equal(Number.parseFloat(storyboardClipButton.style.height), 8);
  });

  it("emphasizes the video track as the primary production lane", async () => {
    mockWorkspaceFetch();

    render(workspace(dialogueBeforeVideoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(dom.window.document.querySelector('[data-track-id="video"]'));
    });

    const videoTrack = dom.window.document.querySelector(
      '[data-track-id="video"]',
    );
    const dialogueTrack = dom.window.document.querySelector(
      '[data-track-id="dialogue"]',
    );
    assert.ok(videoTrack);
    assert.ok(dialogueTrack);
    assert.equal(
      videoTrack.getAttribute("data-timeline-primary-lane"),
      "video-production",
    );
    assert.equal(
      videoTrack.getAttribute("data-timeline-primary-lane-visual"),
      "dominant-time-axis",
    );
    assert.match(videoTrack.className, /border-slate-400/);
    assert.match(videoTrack.className, /bg-white/);
    assert.doesNotMatch(videoTrack.className, /bg-teal-50/);
    assert.doesNotMatch(videoTrack.className, /bg-slate-100/);
    assert.equal(
      dialogueTrack.getAttribute("data-timeline-support-lane-density"),
      "reference-strip",
    );
    assert.match(dialogueTrack.className, /border-slate-100/);
    assert.match(dialogueTrack.className, /bg-white\/50/);
    const dialogueTrackLabel = dialogueTrack.querySelector(
      '[data-timeline-track-label="dialogue"]',
    ) as HTMLElement | null;
    assert.ok(dialogueTrackLabel);
    assert.equal(
      dialogueTrackLabel.getAttribute("data-timeline-track-label-visual"),
      "support-muted",
    );
    assert.match(dialogueTrackLabel.className, /bg-transparent/);
    assert.match(dialogueTrackLabel.className, /border-transparent/);
    assert.match(dialogueTrackLabel.className, /text-\[10px\]/);
    assert.match(dialogueTrackLabel.className, /text-slate-400/);
    assert.match(dialogueTrackLabel.className, /font-medium/);
    assert.doesNotMatch(dialogueTrackLabel.className, /text-\[12px\]/);
    assert.doesNotMatch(dialogueTrackLabel.className, /bg-slate-50\/80/);
    assert.doesNotMatch(dialogueTrackLabel.className, /text-slate-500/);
    assert.notEqual(
      videoTrack.compareDocumentPosition(dialogueTrack) &
        dom.window.Node.DOCUMENT_POSITION_FOLLOWING,
      0,
    );
    assert.ok(videoTrack.querySelector('[data-timeline-track-label="video"]'));
    assert.ok(
      Number.parseFloat((videoTrack as HTMLElement).style.minHeight) >
        Number.parseFloat((dialogueTrack as HTMLElement).style.minHeight),
    );
    assert.match(
      videoTrack.querySelector('[data-timeline-track-label="video"]')
        ?.className || "",
      /bg-white/,
    );
    assert.match(
      videoTrack.querySelector('[data-timeline-track-label="video"]')
        ?.className || "",
      /border-slate-200/,
    );
    assert.match(
      videoTrack.querySelector('[data-timeline-track-label="video"]')
        ?.className || "",
      /text-slate-900/,
    );
    assert.match(
      videoTrack.querySelector('[data-timeline-track-label="video"]')
        ?.className || "",
      /inset_4px_0_0/,
    );
    assert.doesNotMatch(
      videoTrack.querySelector('[data-timeline-track-label="video"]')
        ?.className || "",
      /bg-slate-900/,
    );
    const primaryLaneLabel = videoTrack.querySelector(
      '[data-timeline-primary-lane-label="visible"]',
    ) as HTMLElement | null;
    assert.ok(primaryLaneLabel);
    assert.equal(primaryLaneLabel.textContent, "主时间轴");
    assert.match(primaryLaneLabel.className, /text-\[9px\]/);
    assert.match(primaryLaneLabel.className, /text-slate-500/);
    assert.doesNotMatch(primaryLaneLabel.className, /sr-only/);
    assert.match(
      videoTrack.querySelector('[data-timeline-track-label="video"]')
        ?.textContent || "",
      /视频/,
    );
    assert.match(
      videoTrack.querySelector('[data-timeline-track-label="video"]')
        ?.textContent || "",
      /主时间轴/,
    );
    const videoTrackMarker = videoTrack.querySelector(
      '[data-timeline-track-marker="primary"]',
    ) as HTMLElement | null;
    assert.ok(videoTrackMarker);
    assert.match(videoTrackMarker.className, /h-3/);
    assert.match(videoTrackMarker.className, /w-3/);
    assert.match(videoTrackMarker.className, /ring-2/);
    assert.ok(videoTrackMarker.style.backgroundColor);
    const videoAxisLine = videoTrack.querySelector(
      '[data-timeline-video-axis-line="true"]',
    ) as HTMLElement | null;
    assert.ok(videoAxisLine);
    assert.match(videoAxisLine.className, /h-7/);
    assert.match(videoAxisLine.className, /border-y/);
    assert.match(videoAxisLine.className, /bg-teal-500\/20/);
    const dialogueTrackMarker = dialogueTrack.querySelector(
      '[data-timeline-track-marker="support"]',
    ) as HTMLElement | null;
    assert.ok(dialogueTrackMarker);
    assert.match(dialogueTrackMarker.className, /h-px/);
    assert.match(dialogueTrackMarker.className, /w-1\.5/);
    assert.match(dialogueTrackMarker.className, /bg-slate-200/);
    assert.doesNotMatch(dialogueTrackMarker.className, /bg-slate-300/);
    assert.equal(dialogueTrackMarker.getAttribute("style"), null);
    assert.equal((videoTrack as HTMLElement).style.minHeight, "116px");
    assert.equal((dialogueTrack as HTMLElement).style.minHeight, "18px");
    assert.equal((dialogueTrack as HTMLElement).style.marginBottom, "2px");

    const videoClipButton = dom.window.document.querySelector(
      '[data-track-id="video"] button',
    ) as HTMLButtonElement | null;
    assert.ok(videoClipButton);
    assert.equal(
      videoClipButton.getAttribute("data-timeline-item-tone"),
      "primary-selected",
    );
    assert.match(videoClipButton.className, /ring-1/);
    assert.match(videoClipButton.className, /ring-blue-500\/55/);
    assert.match(videoClipButton.className, /shadow-sm/);
    assert.doesNotMatch(videoClipButton.className, /ring-blue-300\/45/);
    assert.equal(videoClipButton.style.borderWidth, "2px");
    assert.equal(
      videoClipButton.getAttribute("data-timeline-item-type"),
      "video",
    );
    assert.equal(
      videoClipButton.getAttribute("data-timeline-item-visual"),
      "timeline-bar",
    );
    assert.equal(Number.parseFloat(videoClipButton.style.height), 44);
    assert.equal(videoClipButton.textContent?.trim(), "视频 1");
    assert.ok(
      videoClipButton.querySelector(
        '[data-timeline-video-clip-frame="filmstrip"]',
      ),
    );
    const selectedVideoTopRail = videoClipButton.querySelector(
      '[data-timeline-video-clip-rail="top"]',
    );
    assert.ok(selectedVideoTopRail);
    assert.equal(
      selectedVideoTopRail.getAttribute("data-timeline-video-clip-rail-tone"),
      "selected",
    );
    assert.match(selectedVideoTopRail.className, /bg-blue-600\/60/);
    assert.ok(
      videoClipButton.querySelector('[data-timeline-video-clip-rail="bottom"]'),
    );
    const dialogueClipButton = dom.window.document.querySelector(
      '[data-track-id="dialogue"] button',
    ) as HTMLButtonElement | null;
    assert.ok(dialogueClipButton);
    assert.equal(
      dialogueClipButton.getAttribute("data-timeline-item-visual"),
      "clip-block",
    );
    assert.ok(Number.parseFloat(dialogueClipButton.style.height) >= 14);
    assert.equal(dialogueClipButton.style.borderWidth, "1px");
  });

  it("renders compact video labels on the Timeline while preserving full clip text", async () => {
    mockWorkspaceFetch();
    const longText = "懒惰是第一动力，但爱是最终目的";

    const utils = render(workspace(longLabelVideoTimeline(longText)), {
      container: dom.window.document.body,
    });

    const timelineButton = await waitFor(() =>
      utils.getByLabelText(`在时间轴中选择 ${longText}`),
    );
    assert.equal(timelineButton.textContent?.trim(), "视频 1");
    const productionTitle = dom.window.document.querySelector(
      '[data-clip-production-title="full"]',
    ) as HTMLElement | null;
    assert.ok(productionTitle);
    assert.equal(productionTitle.textContent, "视频 1");
    assert.equal(productionTitle.getAttribute("title"), longText);
    assert.match(productionTitle.className, /shrink-0/);
    assert.equal(utils.queryByText(longText), null);
  });

  it("keeps compact non-video labels at detailed zoom while preserving accessible clip selection", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(dialogueBeforeVideoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(utils.getByRole("heading", { name: "全片时间轴" }));
      assert.ok(utils.getByLabelText("在时间轴中选择 native dialogue"));
      assert.ok(utils.getAllByText("对白 1").length >= 1);
      assert.ok(utils.getAllByText("视频 1").length >= 1);
    });

    assert.equal(utils.queryByText("native dialogue"), null);
  });

  it("keeps provider generation hidden for non-video timeline clips", async () => {
    mockWorkspaceFetch();

    const utils = render(workspace(dialogueTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => assert.ok(utils.getByText("选中片段生产")));
    assert.ok(utils.getByLabelText("在时间轴中选择 native dialogue"));
    assert.ok(utils.getAllByText("对白 1").length >= 1);
    assert.equal(utils.queryByText("片段检查器"), null);
    assert.equal(utils.queryByRole("button", { name: "生成片段分镜图" }), null);
    assert.equal(
      utils.queryByRole("button", { name: "生成/重做此片段视频" }),
      null,
    );
  });

  it("keeps environment binding available for clips without normalized scenes", async () => {
    mockWorkspaceFetch({
      environments: [
        {
          id: 1,
          name: "办公室",
          created_at: "2026-06-09T00:00:00Z",
          updated_at: "2026-06-09T00:00:00Z",
        },
      ],
      environmentDetails: {
        1: {
          id: 1,
          name: "办公室",
          reference_images: ["https://cdn.example/office-env.png"],
          created_at: "2026-06-09T00:00:00Z",
          updated_at: "2026-06-09T00:00:00Z",
        },
      },
    });

    const utils = render(workspace(videoTimeline()), {
      container: dom.window.document.body,
    });

    await waitFor(() => {
      assert.ok(
        utils.getByText("未匹配规范化场景，当前环境仅用于片段生成参考。"),
      );
      assert.ok(utils.getByLabelText("片段环境"));
      assert.ok(utils.getByText("去临时角色绑定 IP"));
    });

    fireEvent.change(utils.getByLabelText("片段环境"), {
      target: { value: "1" },
    });

    await waitFor(() => assert.ok(utils.getByAltText("环境图 办公室 1")));
    await waitFor(() =>
      assert.equal(
        utils
          .getByLabelText("选择环境图 办公室 1")
          .getAttribute("aria-pressed"),
        "true",
      ),
    );

    assert.ok(utils.getByLabelText("视频生成绑定上下文"));
    assert.ok(utils.getAllByText("环境图：1 张").length >= 1);
  });

  it("labels the header primary action from clip-video readiness", () => {
    const selectedScript = script();
    const workflowStatus: WorkflowStatus = {
      script: "ready",
      timeline: "ready",
      storyboard: "ready",
    };

    const missing = render(
      <EpisodeWorkspaceHeader
        episode={episode()}
        script={selectedScript}
        scripts={[selectedScript]}
        selectedScriptId={selectedScript.id}
        workflowStatus={workflowStatus}
        resolvedVideos={resolvedVideosMissing()}
        activeTab="timeline"
        onTabChange={() => {}}
        onNavigateBack={() => {}}
        onGenerateScript={() => {}}
        onGenerateTimeline={() => {}}
        onSelectScript={() => {}}
        storyboardActionLabel="进入片段分镜"
        onOpenStoryboard={() => {}}
      />,
      { container: dom.window.document.body },
    );
    const missingAction = missing.getByRole("button", {
      name: "处理缺失片段",
    });
    assert.equal(missingAction.getAttribute("title"), "处理缺失片段");
    assert.equal(
      missingAction.querySelector('[data-missing-clips-icon="warning"]')
        ?.textContent,
      "",
    );
    const desktopLabel = missingAction.querySelector(
      '[data-workspace-primary-action-label="desktop-full"]',
    );
    const mobileLabel = missingAction.querySelector(
      '[data-workspace-primary-action-label="mobile-short"]',
    );
    assert.ok(desktopLabel);
    assert.ok(mobileLabel);
    assert.equal(desktopLabel.textContent, "处理缺失片段");
    assert.equal(mobileLabel.textContent, "缺片段");
    assert.match(desktopLabel.className, /hidden/);
    assert.match(desktopLabel.className, /min-\[760px\]:inline/);
    assert.match(mobileLabel.className, /min-\[760px\]:hidden/);
    assert.equal(mobileLabel.getAttribute("aria-hidden"), "true");
    assert.equal(
      missingAction.getAttribute("data-workspace-primary-action"),
      "open-clip",
    );
    assert.equal(
      missingAction.getAttribute("data-workspace-primary-action-emphasis"),
      "inline-warning",
    );
    assert.match(missingAction.className, /text-amber-700/);
    assert.doesNotMatch(missingAction.className, /bg-amber-50/);
    assert.doesNotMatch(missingAction.className, /border-amber-200/);
    assert.match(missingAction.className, /rounded-md/);
    assert.doesNotMatch(missingAction.className, /w-8/);
    assert.match(missingAction.className, /!h-6/);
    assert.match(missingAction.className, /min-\[760px\]:!h-8/);
    assert.match(missingAction.className, /gap-1/);
    assert.match(missingAction.className, /min-\[760px\]:gap-1\.5/);
    assert.match(missingAction.className, /whitespace-nowrap/);
    assert.match(missingAction.className, /px-1/);
    assert.match(missingAction.className, /min-\[760px\]:px-1\.5/);
    assert.match(missingAction.className, /text-\[11px\]/);
    assert.doesNotMatch(missingAction.className, /bg-blue-600/);
    cleanup();

    const ready = render(
      <EpisodeWorkspaceHeader
        episode={episode()}
        script={selectedScript}
        scripts={[selectedScript]}
        selectedScriptId={selectedScript.id}
        workflowStatus={workflowStatus}
        resolvedVideos={resolvedVideos("https://example.com/clip-ready.mp4")}
        activeTab="timeline"
        onTabChange={() => {}}
        onNavigateBack={() => {}}
        onGenerateScript={() => {}}
        onGenerateTimeline={() => {}}
        onSelectScript={() => {}}
        storyboardActionLabel="进入片段分镜"
        onOpenStoryboard={() => {}}
      />,
      { container: dom.window.document.body },
    );
    assert.match(
      ready.getByRole("button", { name: "渲染/导出" }).className,
      /bg-blue-600/,
    );
    cleanup();

    const dialogueOnlyTimeline = render(
      <EpisodeWorkspaceHeader
        episode={episode()}
        script={selectedScript}
        scripts={[selectedScript]}
        selectedScriptId={selectedScript.id}
        workflowStatus={workflowStatus}
        resolvedVideos={{
          ...resolvedVideosMissing(),
          video_clip_count: 0,
          missing_clip_count: 0,
          items: [],
        }}
        activeTab="timeline"
        onTabChange={() => {}}
        onNavigateBack={() => {}}
        onGenerateScript={() => {}}
        onGenerateTimeline={() => {}}
        onSelectScript={() => {}}
        storyboardActionLabel="打开分镜辅助"
        onOpenStoryboard={() => {}}
      />,
      { container: dom.window.document.body },
    );
    assert.match(
      dialogueOnlyTimeline.getByRole("button", { name: "生成 Timeline" })
        .className,
      /bg-blue-600/,
    );
  });
});

function workspace(
  selectedTimelineSpec: TimelineResponse,
  initialSelectedClipId?: string,
  resolvedVideosPayload: TimelineResolvedVideoListResponse | null = resolvedVideosMissing(),
  options: {
    normalizedScenes?: NormalizedScene[];
    selectedStoryboard?: Record<string, unknown> | null;
    onSelectedClipIdChange?: (clipId: string | null) => void;
    onNavigateToScript?: () => void;
  } = {},
) {
  return (
    <AlertModalProvider>
      <ToastProvider>
        <EpisodeTimelineWorkspace
          selectedScriptId={128}
          initialSelectedClipId={initialSelectedClipId}
          selectedScript={{ version: "1.0" } as Script}
          selectedTimelineSpec={selectedTimelineSpec}
          resolvedVideos={resolvedVideosPayload}
          onSelectedClipIdChange={options.onSelectedClipIdChange}
          selectedAudioTimeline={null}
          selectedStoryboard={options.selectedStoryboard ?? null}
          normalizedScenes={options.normalizedScenes ?? []}
          normalizedScenesLoading={false}
          normalizedScenesError={null}
          timingModel=""
          setTimingModel={() => {}}
          useDurationControl={false}
          setUseDurationControl={() => {}}
          onNavigateToTasks={() => {}}
          onNavigateToScript={options.onNavigateToScript ?? (() => {})}
          onNavigateToStoryboard={() => {}}
          onNavigateToCharacters={() => {}}
        />
      </ToastProvider>
    </AlertModalProvider>
  );
}

function episode(): Episode {
  return {
    id: 1,
    business_id: "episode_1",
    story_id: 7,
    episode_number: 1,
    title: "末日安全屋",
    duration_minutes: 3,
    status: "draft",
    created_at: "2026-06-11T00:00:00Z",
    updated_at: "2026-06-11T00:00:00Z",
  };
}

function script(): Script {
  return {
    id: 128,
    business_id: "script_128",
    episode_id: 1,
    title: "第1集剧本",
    format_type: "screenplay",
    language: "zh-CN",
    status: "draft",
    version: "1.0",
    created_at: "2026-06-11T00:00:00Z",
    updated_at: "2026-06-11T00:00:00Z",
  };
}

function mockWorkspaceFetch({
  environments = [],
  environmentDetails = {},
  resolvedVideos,
  renderJobs = [],
  clipAssets = [],
}: {
  environments?: unknown[];
  environmentDetails?: Record<number, unknown>;
  resolvedVideos?: unknown;
  renderJobs?: unknown[];
  clipAssets?: TimelineClipAssetResponse[];
} = {}) {
  globalThis.fetch = (async (url: RequestInfo | URL) => {
    const path = String(url);
    if (path.includes("/api/v1/ai/models/available")) {
      return jsonResponse({ models: [], default: "" });
    }
    if (path.includes("/characters")) {
      return jsonResponse({ items: [], total: 0, page: 1, page_size: 20 });
    }
    const environmentDetailMatch = path.match(
      /\/api\/v1\/story-structure\/environments\/(\d+)$/,
    );
    if (environmentDetailMatch) {
      return jsonResponse(
        environmentDetails[Number(environmentDetailMatch[1])] || {},
      );
    }
    if (path.includes("/api/v1/story-structure/environments")) {
      return jsonResponse(environments);
    }
    if (path.includes("/resolved-videos")) {
      return jsonResponse(resolvedVideos || resolvedVideosMissing());
    }
    if (path.includes("/render-jobs")) {
      return jsonResponse({ items: renderJobs });
    }
    if (path.includes("/clip-assets")) {
      return jsonResponse({ items: clipAssets });
    }
    return jsonResponse({});
  }) as typeof fetch;
}

function resolvedVideos(url: string): TimelineResolvedVideoListResponse {
  return {
    timeline_id: 8,
    timeline_version: 3,
    ready: true,
    video_clip_count: 1,
    missing_clip_count: 0,
    generating_clip_count: 0,
    items: [
      {
        clip_id: "video_scene_1_beat_1_001",
        status: "ready",
        url,
        source: "timeline_clip_asset:provider_rework",
        start_ms: 0,
        end_ms: 1200,
        duration_seconds: 1.2,
      },
    ],
  };
}

function resolvedVideosMissing(): TimelineResolvedVideoListResponse {
  return {
    timeline_id: 8,
    timeline_version: 3,
    ready: false,
    video_clip_count: 1,
    missing_clip_count: 1,
    generating_clip_count: 0,
    items: [
      {
        clip_id: "video_scene_1_beat_1_001",
        status: "missing",
        reason: "missing_video_url",
        start_ms: 0,
        end_ms: 1200,
        duration_seconds: 1.2,
      },
    ],
  };
}

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

function videoTimeline() {
  return baseTimeline([
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_1_beat_1_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 1200,
          text: "视频 1",
        },
      ],
    },
  ]);
}

function emptyTimeline() {
  return baseTimeline([]);
}

function longEpisodeTimeline() {
  const timeline = videoTimeline();
  timeline.spec = {
    ...timeline.spec,
    tracks: [
      {
        track_type: "video",
        clips: [
          {
            clip_id: "video_scene_1_beat_1_001",
            track_type: "video",
            start_ms: 0,
            end_ms: 3200,
            text: "视频 1",
          },
          {
            clip_id: "video_scene_1_beat_2_002",
            track_type: "video",
            start_ms: 148800,
            end_ms: 152000,
            text: "视频 2",
          },
        ],
      },
    ],
  };
  return timeline;
}

function denseFittedVideoTimeline() {
  const timeline = videoTimeline();
  timeline.spec = {
    ...timeline.spec,
    tracks: [
      {
        track_type: "video",
        clips: [
          {
            clip_id: "video_scene_1_beat_1_001",
            track_type: "video",
            start_ms: 0,
            end_ms: 3320,
            text: "视频 1",
          },
          {
            clip_id: "video_scene_1_beat_2_002",
            track_type: "video",
            start_ms: 8000,
            end_ms: 32000,
            text: "视频 2",
          },
          {
            clip_id: "video_scene_1_beat_3_003",
            track_type: "video",
            start_ms: 40000,
            end_ms: 43000,
            text: "视频 3",
          },
          {
            clip_id: "video_scene_1_beat_4_004",
            track_type: "video",
            start_ms: 148800,
            end_ms: 152000,
            text: "视频 4",
          },
        ],
      },
    ],
  };
  return timeline;
}

function longEpisodeWithSupportTimeline() {
  const timeline = longEpisodeTimeline();
  timeline.spec = {
    ...timeline.spec,
    tracks: [
      {
        track_type: "video",
        clips: [
          {
            clip_id: "video_scene_1_beat_1_001",
            track_type: "video",
            start_ms: 0,
            end_ms: 3200,
            text: "视频 1",
          },
          {
            clip_id: "video_scene_1_beat_2_002",
            track_type: "video",
            start_ms: 128000,
            end_ms: 152000,
            text: "视频 2",
          },
        ],
      },
      {
        track_type: "dialogue",
        clips: [
          {
            clip_id: "dialogue_long_001",
            track_type: "dialogue",
            start_ms: 148800,
            end_ms: 152000,
            text: "长对白提示",
          },
        ],
      },
      {
        track_type: "storyboard",
        clips: [
          {
            clip_id: "storyboard_long_001",
            track_type: "storyboard",
            start_ms: 148800,
            end_ms: 152000,
            text: "长分镜提示",
          },
        ],
      },
    ],
  };
  return timeline;
}

function longLabelVideoTimeline(label: string) {
  return baseTimeline([
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_1_beat_1_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 3200,
          text: label,
        },
      ],
    },
  ]);
}

function dialogueTimeline() {
  return baseTimeline([
    {
      track_type: "dialogue",
      clips: [
        {
          clip_id: "dialogue_scene_1_beat_1_001",
          track_type: "dialogue",
          start_ms: 0,
          end_ms: 1200,
          text: "native dialogue",
        },
      ],
    },
  ]);
}

function dialogueBeforeVideoTimeline() {
  return baseTimeline([
    {
      track_type: "dialogue",
      clips: [
        {
          clip_id: "dialogue_scene_1_beat_1_001",
          track_type: "dialogue",
          start_ms: 0,
          end_ms: 1200,
          text: "native dialogue",
        },
      ],
    },
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_1_beat_1_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 1200,
          text: "视频 1",
        },
      ],
    },
  ]);
}

function twoVideoTimeline() {
  return baseTimeline([
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_1_beat_1_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 1200,
          text: "第一个视频",
        },
        {
          clip_id: "video_scene_1_beat_2_002",
          track_type: "video",
          start_ms: 1300,
          end_ms: 2400,
          text: "第二个视频",
        },
      ],
    },
  ]);
}

function idOnlyVideoTimeline() {
  return baseTimeline([
    {
      track_type: "video",
      clips: [
        {
          id: "video_scene_legacy_id_001",
          track_type: "video",
          start_ms: 0,
          end_ms: 1200,
          text: "历史 id 视频",
        } as unknown as NonNullable<
          TimelineResponse["spec"]
        >["tracks"][number]["clips"][number],
      ],
    },
  ]);
}

function sceneIdTimeline() {
  return baseTimeline([
    {
      track_type: "video",
      clips: [
        {
          clip_id: "video_scene_580_beat_3923_001",
          track_type: "video",
          scene_id: 580,
          start_ms: 0,
          end_ms: 1200,
          text: "Scene DB id video",
        },
      ],
    },
  ]);
}

function baseTimeline(tracks: NonNullable<TimelineResponse["spec"]>["tracks"]) {
  return {
    id: 8,
    business_id: "timeline_8",
    episode_id: 1,
    script_id: 128,
    title: "Timeline",
    status: "draft",
    version: 3,
    created_at: "2026-06-04T00:00:00Z",
    updated_at: "2026-06-04T00:00:00Z",
    spec: {
      spec_version: "timeline.v1",
      episode_id: 1,
      script_id: 128,
      version: 3,
      tracks,
    },
  } satisfies TimelineResponse;
}
