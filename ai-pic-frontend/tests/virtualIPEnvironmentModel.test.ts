import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  availableEnvironmentOptions,
  uniqueEnvironmentLinks,
} from "../src/components/features/virtual-ip-detail/virtualIPEnvironmentModel";
import type { Environment, VirtualIPEnvironmentLink } from "../src/utils/api/types";

const env = (id: number, name: string): Environment => ({
  id,
  business_id: `env_${id}`,
  name,
  created_at: "2026-05-07T00:00:00Z",
  updated_at: "2026-05-07T00:00:00Z",
});

const link = (id: number, environmentId: number): VirtualIPEnvironmentLink => ({
  id,
  business_id: `link_${id}`,
  virtual_ip_id: 1,
  environment_id: environmentId,
  usage_type: "scene_pool",
  sort_order: 0,
  is_default: false,
  environment: env(environmentId, `环境 ${environmentId}`),
  created_at: "2026-05-07T00:00:00Z",
});

describe("virtual IP environment model", () => {
  it("dedupes linked environment rows by environment id", () => {
    assert.deepEqual(
      uniqueEnvironmentLinks([link(1, 2), link(2, 2)]).map((item) => item.id),
      [2],
    );
  });

  it("filters environments that are already linked to the IP", () => {
    assert.deepEqual(
      availableEnvironmentOptions([env(1, "A"), env(2, "B")], [link(1, 2)]).map(
        (item) => item.name,
      ),
      ["A"],
    );
  });
});
