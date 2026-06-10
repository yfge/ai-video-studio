import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { autoCreatedCharactersFromScript } from "../src/components/features/episode/autoCreatedCharactersFromScript";
import type { Script } from "../src/utils/api/types";

const character = {
  episode_character_id: 11,
  episode_character_business_id: "epc_11",
  character_name: "快递员",
  virtual_ip_id: 32,
  importance: 2,
  needs_customization: true,
  generated_info: {
    personality: "热情",
    background: "片区老熟人",
    appearance_override: "蓝色制服",
    scene_appearances: [1],
    dialogue_count: 4,
  },
};

function script(extra: Record<string, unknown> | undefined): Script {
  return { id: 1, extra_metadata: extra } as unknown as Script;
}

describe("autoCreatedCharactersFromScript", () => {
  it("reads valid entries from script extra_metadata", () => {
    const result = autoCreatedCharactersFromScript(
      script({ auto_created_characters: [character] }),
    );
    assert.equal(result.length, 1);
    assert.equal(result[0].character_name, "快递员");
  });

  it("filters malformed entries and tolerates missing metadata", () => {
    assert.deepEqual(autoCreatedCharactersFromScript(null), []);
    assert.deepEqual(autoCreatedCharactersFromScript(script(undefined)), []);
    assert.deepEqual(
      autoCreatedCharactersFromScript(
        script({ auto_created_characters: "oops" }),
      ),
      [],
    );
    assert.deepEqual(
      autoCreatedCharactersFromScript(
        script({ auto_created_characters: [{ character_name: 5 }, null] }),
      ),
      [],
    );
  });
});
