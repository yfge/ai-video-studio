import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  operatorShellActionsClass,
  operatorShellHeaderClass,
  operatorShellLogoutButtonClass,
  operatorShellMainClass,
  operatorShellSidebarHeaderClass,
  operatorShellTitleClass,
  operatorShellUserClass,
} from "../src/components/shared/operator/OperatorShellLayout";

describe("OperatorShell layout classes", () => {
  it("uses tighter chrome when compact navigation is enabled", () => {
    assert.match(operatorShellHeaderClass(true), /h-8/);
    assert.match(operatorShellHeaderClass(true), /min-\[760px\]:h-10/);
    assert.doesNotMatch(operatorShellHeaderClass(true), /h-12/);
    assert.doesNotMatch(operatorShellHeaderClass(true), /h-14/);
    assert.match(operatorShellHeaderClass(true), /justify-end/);
    assert.match(
      operatorShellHeaderClass(true),
      /min-\[760px\]:justify-between/,
    );
    assert.match(operatorShellHeaderClass(true), /px-3/);
    assert.equal(operatorShellMainClass(true), "px-4 py-2 sm:px-5 sm:py-3");
    assert.match(operatorShellSidebarHeaderClass(true), /h-10/);
    assert.match(operatorShellTitleClass(true), /max-\[760px\]:sr-only/);
    assert.match(operatorShellActionsClass(true), /gap-1\.5/);
    assert.match(operatorShellActionsClass(true), /min-\[760px\]:gap-2/);
    assert.doesNotMatch(operatorShellActionsClass(true), /gap-3/);
    assert.match(operatorShellUserClass(true), /max-w-24/);
    assert.match(operatorShellUserClass(true), /h-6/);
    assert.match(operatorShellUserClass(true), /min-\[760px\]:h-7/);
    assert.match(operatorShellUserClass(true), /text-\[11px\]/);
    assert.match(operatorShellLogoutButtonClass(true), /!h-6/);
    assert.match(operatorShellLogoutButtonClass(true), /!px-1\.5/);
    assert.match(operatorShellLogoutButtonClass(true), /min-\[760px\]:!h-7/);
  });

  it("keeps the default shell rhythm for non-compact pages", () => {
    assert.match(operatorShellHeaderClass(false), /h-14/);
    assert.doesNotMatch(operatorShellHeaderClass(false), /h-12/);
    assert.doesNotMatch(operatorShellHeaderClass(false), /h-10/);
    assert.doesNotMatch(operatorShellHeaderClass(false), /h-8/);
    assert.match(operatorShellHeaderClass(false), /justify-between/);
    assert.doesNotMatch(operatorShellHeaderClass(false), /justify-end/);
    assert.equal(operatorShellMainClass(false), "px-4 py-4 sm:px-5");
    assert.match(operatorShellSidebarHeaderClass(false), /h-14/);
    assert.equal(operatorShellTitleClass(false), "min-w-0");
    assert.match(operatorShellActionsClass(false), /gap-3/);
    assert.match(operatorShellUserClass(false), /px-3/);
    assert.equal(operatorShellLogoutButtonClass(false), "");
  });
});
