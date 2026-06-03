import { describe, it, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { render, cleanup } from "@testing-library/react";
import { JSDOM } from "jsdom";

import { ImageGrid } from "../src/components/features/virtual-ip-images/ImageGrid";
import type { VirtualIP, VirtualIPImage } from "../src/utils/api/types";

const dom = new JSDOM("<!doctype html><html><body></body></html>");
(globalThis as any).window = dom.window;
(globalThis as any).document = dom.window.document;
(globalThis as any).HTMLElement = dom.window.HTMLElement;

const virtualIP: VirtualIP = {
  id: 1,
  business_id: "vip_test",
  name: "测试 IP",
  tags: [],
  is_active: true,
  is_public: false,
  created_at: "2026-06-03T00:00:00Z",
};

const image = (id: number): VirtualIPImage => ({
  id,
  business_id: `img_${id}`,
  virtual_ip_id: 1,
  file_path: `http://localhost:8000/uploads/${id}.png`,
  category: "portrait",
  tags: [],
  is_default: id === 1,
  created_at: "2026-06-03T00:00:00Z",
  updated_at: "2026-06-03T00:00:00Z",
});

describe("Virtual IP image grid layout", () => {
  afterEach(() => cleanup());

  it("uses adaptive columns so generated images do not crowd into a narrow rail", () => {
    const { container } = render(
      <ImageGrid
        images={[image(1), image(2), image(3)]}
        virtualIP={virtualIP}
        onPreview={() => undefined}
        onImg2Img={() => undefined}
        onDelete={() => undefined}
        onSetDefault={() => undefined}
      />,
      { container: dom.window.document.body },
    );

    const grid = container.firstElementChild;
    assert.ok(grid);
    const className = grid.getAttribute("class") || "";
    assert.match(className, /auto-fit/);
    assert.match(className, /minmax/);
    assert.doesNotMatch(className, /\bgrid-cols-2\b/);
  });

  it("keeps the generation form full width instead of using a narrow 2xl rail", () => {
    const source = readFileSync(
      new URL(
        "../src/components/features/virtual-ip-images/VirtualIPImageManager.tsx",
        import.meta.url,
      ),
      "utf8",
    );

    assert.doesNotMatch(
      source,
      /2xl:grid-cols-\[160px_minmax\(0,1fr\)_340px\]/,
    );
    assert.doesNotMatch(source, /2xl:col-span-1/);
    assert.match(source, /lg:col-span-2/);
  });

  it("forces the generation controls into one stable column inside the image manager", () => {
    const source = readFileSync(
      new URL(
        "../src/components/features/virtual-ip-images/ImageGenerationForm.tsx",
        import.meta.url,
      ),
      "utf8",
    );

    assert.match(source, /gridTemplateColumns:\s*"1fr"/);
    assert.match(source, /\[\&>\*\]:col-span-full/);
  });

  it("refreshes image assets when async generation tasks complete or the page regains focus", () => {
    const hookSource = readFileSync(
      new URL("../src/hooks/useVirtualIPImages.ts", import.meta.url),
      "utf8",
    );
    const taskRefreshSource = readFileSync(
      new URL(
        "../src/hooks/virtual-ip/useVirtualIPImageTaskRefresh.ts",
        import.meta.url,
      ),
      "utf8",
    );
    const dataSource = readFileSync(
      new URL(
        "../src/hooks/virtual-ip/useVirtualIPImageData.ts",
        import.meta.url,
      ),
      "utf8",
    );
    const generationSource = readFileSync(
      new URL(
        "../src/hooks/virtual-ip/useVirtualIPImageGeneration.ts",
        import.meta.url,
      ),
      "utf8",
    );

    assert.match(hookSource, /useVirtualIPImageTaskRefresh/);
    assert.match(hookSource, /onTaskCreated:\s*taskRefresh\.trackImageTask/);
    assert.match(taskRefreshSource, /taskAPI\.getTask/);
    assert.match(taskRefreshSource, /task\.status === "completed"/);
    assert.match(taskRefreshSource, /refreshImages\(\)/);
    assert.match(dataSource, /window\.addEventListener\("focus"/);
    assert.match(dataSource, /"visibilitychange"/);
    assert.match(
      generationSource,
      /onTaskCreated\?\.\(response\.data\.task_id\)/,
    );
  });
});
