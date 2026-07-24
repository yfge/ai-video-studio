## User Prompt

长篇生成时加入之前的记忆和 facts；每章通过状态门禁后抽取 Narrative Memory。

## Goals

- 主角等持久化 StoryCharacter 的 typed knowledge grant 必须唯一绑定。
- Canon 中没有 StoryCharacter/Virtual IP 行的临时 NPC 仍保留在状态账本，
  但不伪造 Character Memory 候选。
- 不因 Canon NPC 无持久化角色行而阻塞整章候选提取。

## Changes

- Narrative Memory 只要求“能匹配持久化 StoryCharacter”的 knowledge grant
  唯一绑定；无候选的 Canon NPC grant 跳过 Character Memory 映射。
- 有候选但无法唯一绑定的 grant 仍 fail closed。
- typed state delta、知识边界和章节 ledger 不做删改。

## Validation

- Task 6647 第 1 章已 ready，3386 非空白字符，state validation passed；
  候选阶段因 `char-harbor-supervisor` 没有 StoryCharacter 行而失败。
- Story 80 只有王明、老拐两条 StoryCharacter；Canon 还包含港务监理等 NPC。
- focused：24 passed。
- Narrative Memory + Story Novel 联合单测：465 passed，1 skipped。
- 精确 `isort`、`black`、repo docs、repo contracts diff 与
  `git diff --check` 均通过；源码 96 行，测试 247 行。
- 多架构推送构建连续两次被 Docker Hub anonymous-token TLS handshake
  timeout 阻断；随后使用本地已存在的同版本 python/node 基础镜像完成
  `BUILD_PUSH=false ./docker/build_prod_images.sh`：
  - backend image `d8349a83fd5a`
  - frontend image `4fdcef8f3cc2`

## Next Steps

- 运行 Narrative Memory focused、完整小说单测、格式、contracts 和生产构建。
- 正式 Resume 应只补候选抽取，不重写第 1 章正文/hash。

## Linked Commits

- Pending.
