-- MySQL dump 10.13  Distrib 9.4.0, for macos15.4 (arm64)
--
-- Host: 127.0.0.1    Database: ai_video_studio
-- ------------------------------------------------------
-- Server version	8.0.32

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('fe284ccd1b92');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `episodes`
--

DROP TABLE IF EXISTS `episodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `episodes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `story_id` int NOT NULL COMMENT '故事ID',
  `episode_number` int NOT NULL COMMENT '集数',
  `title` varchar(255) NOT NULL COMMENT '剧集标题',
  `summary` text COMMENT '剧集概要',
  `plot_points` json DEFAULT NULL COMMENT '情节要点',
  `character_arcs` json DEFAULT NULL COMMENT '角色发展',
  `conflicts` json DEFAULT NULL COMMENT '冲突点',
  `duration_minutes` int DEFAULT NULL COMMENT '预计时长（分钟）',
  `scene_count` int DEFAULT NULL COMMENT '场景数量',
  `generation_prompt` text COMMENT '生成提示词',
  `ai_model` varchar(50) DEFAULT NULL COMMENT '使用的AI模型',
  `generation_params` json DEFAULT NULL COMMENT '生成参数',
  `status` varchar(20) DEFAULT NULL COMMENT '状态：draft, approved, published',
  `tags` json DEFAULT NULL COMMENT '标签列表',
  `extra_metadata` json DEFAULT NULL COMMENT '额外元数据',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `story_id` (`story_id`),
  KEY `ix_episodes_id` (`id`),
  CONSTRAINT `episodes_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `episodes`
--

LOCK TABLES `episodes` WRITE;
/*!40000 ALTER TABLE `episodes` DISABLE KEYS */;
INSERT INTO `episodes` VALUES (2,4,1,'新的开始','介绍主要角色和背景设定','[{\"timing\": \"开场\", \"description\": \"角色出场\"}, {\"timing\": \"前10分钟\", \"description\": \"背景介绍\"}, {\"timing\": \"中段\", \"description\": \"冲突铺垫\"}]','{\"protagonist\": \"初始状态展示\"}','[{\"intensity\": \"low\", \"description\": \"内心困扰的初步展现\"}]',30,5,'基于以下故事概要，生成1集的剧集大纲：\n\n故事信息:\n- 标题: 你好啊\n- 类型: drama\n- 主题: 你好\n- 故事概要: 主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。\n- 主要冲突: 主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。\n- 解决方案: 通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。\n\n剧集参数:\n- 总集数: 1集\n- 每集时长: 30分钟\n- 情节复杂度: medium\n- 节奏: medium\n\n主要角色:\n[\n  {\n    \"name\": \"主人公A\",\n    \"role\": \"protagonist\",\n    \"description\": \"积极向上的年轻人\"\n  },\n  {\n    \"name\": \"主人公B\",\n    \"role\": \"supporting\",\n    \"description\": \"智慧可靠的朋友\"\n  }\n]\n\n角色关系:\n{\n  \"group_dynamics\": \"团结互助的友好关系\",\n  \"protagonist_friend\": \"深厚的友谊，相互支持\"\n}\n\n请为每一集生成以下内容:\n1. 集数和标题\n2. 剧集概要 (summary)\n3. 主要情节点 (plot_points)\n4. 角色发展 (character_arcs)\n5. 冲突设置 (conflicts)\n6. 场景数量估计 (scene_count)\n\n要求:\n- 确保整体故事的连贯性和完整性\n- 每集都有明确的开始、发展、高潮和结尾\n- 角色发展要符合整体故事弧线\n- 冲突要逐步升级，最终在适当的集数达到高潮\n- 使用JSON格式返回，包含episodes数组\n\n额外要求: 重新生成第1集的内容','ai_episode_generation','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [], \"additional_requirements\": \"在\"}','draft',NULL,NULL,'2025-08-15 03:07:30','2025-08-15 03:07:56'),(3,1,1,'新的开始','小雅开始她的大学生活，遇到了李教授和一些有趣的同学，同时也开始感受到了学业压力。','[{\"timing\": \"开场\", \"description\": \"小雅入学，认识了李教授和新同学\"}, {\"timing\": \"中场\", \"description\": \"小雅开始感受到学业压力，李教授给予建议\"}, {\"timing\": \"结尾\", \"description\": \"小雅开始思考自己的理想和现实的关系\"}]','{\"小雅\": \"从无忧无虑的新生到开始面临学业压力的大学生\", \"李教授\": \"从小雅的导师到成为小雅的人生导师\"}','[{\"intensity\": \"medium\", \"description\": \"学业压力与个人理想的冲突开始显现\"}]',30,8,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：校园青春物语\n类型：青春\n故事概要：小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。\n主要冲突：学业压力与个人理想的冲突\n\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 特殊要求\n测试剧集生成功能\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n- episode_number: 集数\n- title: 剧集标题 \n- summary: 剧集概要\n- plot_points: 主要情节点列表\n- character_arcs: 角色发展安排\n- conflicts: 本集的冲突设置\n- scene_count: 预估场景数量\n\n示例格式：\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"新的开始\",\n            \"summary\": \"介绍主要角色和背景设定\",\n            \"plot_points\": [{\"description\": \"角色出场\", \"timing\": \"开场\"}],\n            \"character_arcs\": {\"protagonist\": \"初始状态展示\"},\n            \"conflicts\": [{\"description\": \"内心困扰\", \"intensity\": \"low\"}],\n            \"scene_count\": 5\n        }\n    ]\n}\n','ai_fallback','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [\"轻松\", \"有趣\"], \"additional_requirements\": \"测试剧集生成功能\"}','draft',NULL,NULL,'2025-08-20 06:26:03','2025-08-20 06:26:03'),(4,1,2,'探索与挑战','小雅开始在李教授的指导下探索自己的兴趣，并接受了一项挑战。','[{\"timing\": \"开场\", \"description\": \"小雅在李教授的指导下开始探索自己的兴趣\"}, {\"timing\": \"中场\", \"description\": \"小雅接受了一项挑战，开始努力准备\"}, {\"timing\": \"结尾\", \"description\": \"小雅完成挑战，收获成长\"}]','{\"小雅\": \"从被动应对学业压力到积极探索自我兴趣和接受挑战\", \"李教授\": \"从给予小雅建议到积极指导小雅的学习\"}','[{\"intensity\": \"medium\", \"description\": \"小雅面对挑战时的压力和不安\"}]',30,8,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：校园青春物语\n类型：青春\n故事概要：小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。\n主要冲突：学业压力与个人理想的冲突\n\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 特殊要求\n测试剧集生成功能\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n- episode_number: 集数\n- title: 剧集标题 \n- summary: 剧集概要\n- plot_points: 主要情节点列表\n- character_arcs: 角色发展安排\n- conflicts: 本集的冲突设置\n- scene_count: 预估场景数量\n\n示例格式：\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"新的开始\",\n            \"summary\": \"介绍主要角色和背景设定\",\n            \"plot_points\": [{\"description\": \"角色出场\", \"timing\": \"开场\"}],\n            \"character_arcs\": {\"protagonist\": \"初始状态展示\"},\n            \"conflicts\": [{\"description\": \"内心困扰\", \"intensity\": \"low\"}],\n            \"scene_count\": 5\n        }\n    ]\n}\n','ai_fallback','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [\"轻松\", \"有趣\"], \"additional_requirements\": \"测试剧集生成功能\"}','draft',NULL,NULL,'2025-08-20 06:26:03','2025-08-20 06:26:03'),(5,1,3,'成长与智慧','小雅在奶奶陈的故事中找到了对生活的新理解，成功应对了学业和个人理想的冲突。','[{\"timing\": \"开场\", \"description\": \"小雅听奶奶陈的故事，对生活有了新的理解\"}, {\"timing\": \"中场\", \"description\": \"小雅将新理解应用到学习和生活中，收获成长\"}, {\"timing\": \"结尾\", \"description\": \"小雅成功应对学业和个人理想的冲突，感悟到人生智慧\"}]','{\"小雅\": \"从面临挑战的焦虑到找到解决问题的智慧和勇气\", \"奶奶陈\": \"从小雅的长辈到小雅的人生导师\"}','[{\"intensity\": \"medium\", \"description\": \"小雅如何将新理解应用到学业和个人理想的冲突中\"}]',30,8,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：校园青春物语\n类型：青春\n故事概要：小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。\n主要冲突：学业压力与个人理想的冲突\n\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 特殊要求\n测试剧集生成功能\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n- episode_number: 集数\n- title: 剧集标题 \n- summary: 剧集概要\n- plot_points: 主要情节点列表\n- character_arcs: 角色发展安排\n- conflicts: 本集的冲突设置\n- scene_count: 预估场景数量\n\n示例格式：\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"新的开始\",\n            \"summary\": \"介绍主要角色和背景设定\",\n            \"plot_points\": [{\"description\": \"角色出场\", \"timing\": \"开场\"}],\n            \"character_arcs\": {\"protagonist\": \"初始状态展示\"},\n            \"conflicts\": [{\"description\": \"内心困扰\", \"intensity\": \"low\"}],\n            \"scene_count\": 5\n        }\n    ]\n}\n','ai_fallback','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [\"轻松\", \"有趣\"], \"additional_requirements\": \"测试剧集生成功能\"}','draft',NULL,NULL,'2025-08-20 06:26:03','2025-08-20 06:26:03'),(6,8,1,'遇见神秘老K','小雅，一个充满活力的大学生，梦想成为一名平面设计师。在学校的科技展上，她被一位神秘人物——老K的技术展示深深吸引。两人迅速成为朋友，老K开始教小雅一些基本的编程知识。小雅的好奇心和学习能力让老K印象深刻，而他们的友谊也在这过程中逐渐加深。故事通过展示小雅的日常生活和学习过程，逐步建立起故事的背景和角色关系。','[{\"timing\": \"开场\", \"purpose\": \"引入老K这一重要角色，建立两人初识的契机。\", \"escalation\": null, \"description\": \"小雅参加学校科技展，首次见到老K的技术展示。\"}, {\"timing\": \"前段\", \"purpose\": \"建立两人友谊的基础。\", \"escalation\": null, \"description\": \"小雅和老K在科技展后交谈，发现共同兴趣。\"}, {\"timing\": \"中段\", \"purpose\": \"推动小雅技能成长，深化角色关系。\", \"escalation\": null, \"description\": \"老K开始教小雅基础编程知识。\"}]','{\"老K\": \"从独行的技术高手到愿意分享知识，开始建立对人际关系的信任。\", \"小雅\": \"从对数字世界一知半解到开始学习编程，展现出强烈的好奇心和学习能力。\"}','[{\"parties\": null, \"intensity\": \"低\", \"description\": \"小雅在学习新技能时的自我怀疑。\"}]',30,5,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：HelloWorld\n类型：drama\n主题：友情\n故事概要：小雅是一个充满活力的大学生，梦想成为一名平面设计师。她的好奇心引领她探索数字世界，并偶然结识了神秘的老Ｋ，在一次学校的科技展上，小雅被老Ｋ的技术展示深深吸引。两人迅速成为好友，老Ｋ开始教小雅一些基本的编程知识。\n\n就在两人友谊加深之际，学校的网络系统遭到一次严重的黑客攻击，导致校园生活陷入混乱。小雅和老Ｋ必须联手，利用他们的技能和智慧来解决这个问题。小雅在学习过程中展现出非凡的学习能力，而老Ｋ也意识到这不仅仅是一次技术上的挑战，更是考验他们友谊的机会。\n\n在老Ｋ的指导下，小雅终于发现了黑客的漏洞，并勇敢地面对对手。通过两人的合作，成功地保护了学校的网络安全。\n\n事件过后，小雅更加坚定了自己的职业梦想，而老Ｋ则更加相信人与人之间的真实联系。在欢庆胜利的同时，他们也体会到了友谊的珍贵。\n主要冲突：学校的网络系统遭到黑客攻击，危及校园安全，小雅和老Ｋ必须联手解决。\n解决方案：小雅在老Ｋ的指导下，展现了非凡的学习能力。两人合作成功地修复了系统漏洞，保护了校园网络的安全。\n## 主要角色\n- 小雅: 一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n- 老Ｋ: 电子世界的神秘使者，技术高手，信息的守护者\n## 角色关系\n- 小雅: 年轻有活力的大学生，梦想成为设计师，与老Ｋ是忘年之交。\n- 老Ｋ: 电子世界的神秘使者，技术高手，与小雅建立了深厚的友谊。\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 生成要求\n请为每一集生成详细的内容规划，确保：\n\n1. **整体连贯性**: 所有剧集构成完整的故事弧线\n2. **节奏控制**: 根据\"medium\"节奏要求安排情节发展\n3. **复杂度适配**: 按照\"medium\"复杂度设计情节\n4. **角色发展**: 每个角色都有清晰的成长轨迹\n5. **冲突升级**: 冲突逐步升级，在适当时机达到高潮\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n\n1. **episode_number**: 集数\n2. **title**: 剧集标题\n3. **summary**: 剧集概要（150-300字）\n4. **plot_points**: 主要情节点列表\n5. **character_arcs**: 角色发展安排\n6. **conflicts**: 本集的冲突设置\n7. **scene_count**: 预估场景数量\n8. **emotional_tone**: 情感基调\n9. **key_moments**: 关键时刻描述\n10. **cliffhanger**: 悬念设置（如果适用）\n\n## 情节发展建议\n- 第1集：角色介绍和背景设定，建立世界观\n- 前1/3：角色关系建立，冲突铺垫\n- 中1/3：冲突发展，情节推进，角色成长\n- 后1/3：冲突高潮，问题解决，情感升华\n- 最后集：故事收尾，角色归宿，主题点题\n\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"...\",\n            \"summary\": \"...\",\n            \"plot_points\": [\n                {\n                    \"sequence\": 1,\n                    \"description\": \"...\",\n                    \"timing\": \"开场/前段/中段/后段/结尾\"\n                }\n            ],\n            \"character_arcs\": {\n                \"character_name\": \"本集的角色发展\"\n            },\n            \"conflicts\": [\n                {\n                    \"type\": \"内心冲突/人际冲突/环境冲突\",\n                    \"description\": \"...\",\n                    \"intensity\": \"低/中/高\"\n                }\n            ],\n            \"scene_count\": 5,\n            \"emotional_tone\": \"...\",\n            \"key_moments\": [\"...\"],\n            \"cliffhanger\": \"...\"\n        }\n    ]\n}','ai_deepseek','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": null, \"style_preferences\": [], \"additional_requirements\": \"\"}','draft',NULL,NULL,'2025-09-12 07:03:46','2025-09-12 07:03:46'),(7,8,2,'危机初现','就在小雅和老K的友谊加深之际，学校的网络系统遭到一次严重的黑客攻击，导致校园生活陷入混乱。小雅开始意识到问题的严重性，并决心帮助老K一起解决这个问题。两人联合起来，开始调查攻击的来源。小雅在老K的指导下，展现出非凡的学习能力，并逐渐发现了潜在的漏洞。','[{\"timing\": \"开场\", \"purpose\": \"引发主要冲突，推动剧情进入危机。\", \"escalation\": \"高\", \"description\": \"学校网络遭到黑客攻击，校园陷入混乱。\"}, {\"timing\": \"前段\", \"purpose\": \"展开主要剧情线，展示两人合作。\", \"escalation\": \"中\", \"description\": \"小雅和老K开始调查网络攻击的来源。\"}, {\"timing\": \"中段\", \"purpose\": \"展示小雅的成长和能力。\", \"escalation\": \"低\", \"description\": \"小雅发现一个潜在的漏洞。\"}]','{\"老K\": \"意识到需要依靠他人，开始更多地信任小雅。\", \"小雅\": \"面对危机，从学习者转变为积极的参与者。\"}','[{\"parties\": [\"学校\", \"黑客\"], \"intensity\": \"高\", \"description\": \"网络攻击带来的校园混乱与恐慌。\"}]',30,6,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：HelloWorld\n类型：drama\n主题：友情\n故事概要：小雅是一个充满活力的大学生，梦想成为一名平面设计师。她的好奇心引领她探索数字世界，并偶然结识了神秘的老Ｋ，在一次学校的科技展上，小雅被老Ｋ的技术展示深深吸引。两人迅速成为好友，老Ｋ开始教小雅一些基本的编程知识。\n\n就在两人友谊加深之际，学校的网络系统遭到一次严重的黑客攻击，导致校园生活陷入混乱。小雅和老Ｋ必须联手，利用他们的技能和智慧来解决这个问题。小雅在学习过程中展现出非凡的学习能力，而老Ｋ也意识到这不仅仅是一次技术上的挑战，更是考验他们友谊的机会。\n\n在老Ｋ的指导下，小雅终于发现了黑客的漏洞，并勇敢地面对对手。通过两人的合作，成功地保护了学校的网络安全。\n\n事件过后，小雅更加坚定了自己的职业梦想，而老Ｋ则更加相信人与人之间的真实联系。在欢庆胜利的同时，他们也体会到了友谊的珍贵。\n主要冲突：学校的网络系统遭到黑客攻击，危及校园安全，小雅和老Ｋ必须联手解决。\n解决方案：小雅在老Ｋ的指导下，展现了非凡的学习能力。两人合作成功地修复了系统漏洞，保护了校园网络的安全。\n## 主要角色\n- 小雅: 一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n- 老Ｋ: 电子世界的神秘使者，技术高手，信息的守护者\n## 角色关系\n- 小雅: 年轻有活力的大学生，梦想成为设计师，与老Ｋ是忘年之交。\n- 老Ｋ: 电子世界的神秘使者，技术高手，与小雅建立了深厚的友谊。\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 生成要求\n请为每一集生成详细的内容规划，确保：\n\n1. **整体连贯性**: 所有剧集构成完整的故事弧线\n2. **节奏控制**: 根据\"medium\"节奏要求安排情节发展\n3. **复杂度适配**: 按照\"medium\"复杂度设计情节\n4. **角色发展**: 每个角色都有清晰的成长轨迹\n5. **冲突升级**: 冲突逐步升级，在适当时机达到高潮\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n\n1. **episode_number**: 集数\n2. **title**: 剧集标题\n3. **summary**: 剧集概要（150-300字）\n4. **plot_points**: 主要情节点列表\n5. **character_arcs**: 角色发展安排\n6. **conflicts**: 本集的冲突设置\n7. **scene_count**: 预估场景数量\n8. **emotional_tone**: 情感基调\n9. **key_moments**: 关键时刻描述\n10. **cliffhanger**: 悬念设置（如果适用）\n\n## 情节发展建议\n- 第1集：角色介绍和背景设定，建立世界观\n- 前1/3：角色关系建立，冲突铺垫\n- 中1/3：冲突发展，情节推进，角色成长\n- 后1/3：冲突高潮，问题解决，情感升华\n- 最后集：故事收尾，角色归宿，主题点题\n\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"...\",\n            \"summary\": \"...\",\n            \"plot_points\": [\n                {\n                    \"sequence\": 1,\n                    \"description\": \"...\",\n                    \"timing\": \"开场/前段/中段/后段/结尾\"\n                }\n            ],\n            \"character_arcs\": {\n                \"character_name\": \"本集的角色发展\"\n            },\n            \"conflicts\": [\n                {\n                    \"type\": \"内心冲突/人际冲突/环境冲突\",\n                    \"description\": \"...\",\n                    \"intensity\": \"低/中/高\"\n                }\n            ],\n            \"scene_count\": 5,\n            \"emotional_tone\": \"...\",\n            \"key_moments\": [\"...\"],\n            \"cliffhanger\": \"...\"\n        }\n    ]\n}','ai_deepseek','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": null, \"style_preferences\": [], \"additional_requirements\": \"\"}','draft',NULL,NULL,'2025-09-12 07:03:46','2025-09-12 07:03:46'),(8,8,3,'联手反击','在老K的指导下，小雅进一步深入黑客的攻击路径，最终锁定了攻击者的身份。随着两人合作的深入，他们的友谊也经受住了考验。小雅勇敢地面对黑客，利用她新学的技能成功地修复了系统漏洞，保护了学校的网络安全。事件过后，小雅更加坚定了自己的职业梦想，而老K则更加相信人与人之间的真实联系。','[{\"timing\": \"开场\", \"purpose\": \"推进剧情至高潮，揭示解决方案。\", \"escalation\": \"高\", \"description\": \"小雅和老K锁定黑客身份。\"}, {\"timing\": \"中段\", \"purpose\": \"展示小雅的成长与胜利。\", \"escalation\": \"高\", \"description\": \"小雅面对黑客，展示出色的编程技能。\"}, {\"timing\": \"后段\", \"purpose\": \"解决主要冲突，主题升华。\", \"escalation\": \"中\", \"description\": \"两人修复系统漏洞，恢复校园秩序。\"}]','{\"老K\": \"通过事件的合作，强化了对友谊和信任的理解。\", \"小雅\": \"从初学者成长为解决问题的关键人物，坚定了职业理想。\"}','[{\"parties\": [\"小雅\", \"黑客\"], \"intensity\": \"高\", \"description\": \"小雅面对黑客的直接对抗。\"}]',30,7,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：HelloWorld\n类型：drama\n主题：友情\n故事概要：小雅是一个充满活力的大学生，梦想成为一名平面设计师。她的好奇心引领她探索数字世界，并偶然结识了神秘的老Ｋ，在一次学校的科技展上，小雅被老Ｋ的技术展示深深吸引。两人迅速成为好友，老Ｋ开始教小雅一些基本的编程知识。\n\n就在两人友谊加深之际，学校的网络系统遭到一次严重的黑客攻击，导致校园生活陷入混乱。小雅和老Ｋ必须联手，利用他们的技能和智慧来解决这个问题。小雅在学习过程中展现出非凡的学习能力，而老Ｋ也意识到这不仅仅是一次技术上的挑战，更是考验他们友谊的机会。\n\n在老Ｋ的指导下，小雅终于发现了黑客的漏洞，并勇敢地面对对手。通过两人的合作，成功地保护了学校的网络安全。\n\n事件过后，小雅更加坚定了自己的职业梦想，而老Ｋ则更加相信人与人之间的真实联系。在欢庆胜利的同时，他们也体会到了友谊的珍贵。\n主要冲突：学校的网络系统遭到黑客攻击，危及校园安全，小雅和老Ｋ必须联手解决。\n解决方案：小雅在老Ｋ的指导下，展现了非凡的学习能力。两人合作成功地修复了系统漏洞，保护了校园网络的安全。\n## 主要角色\n- 小雅: 一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n- 老Ｋ: 电子世界的神秘使者，技术高手，信息的守护者\n## 角色关系\n- 小雅: 年轻有活力的大学生，梦想成为设计师，与老Ｋ是忘年之交。\n- 老Ｋ: 电子世界的神秘使者，技术高手，与小雅建立了深厚的友谊。\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 生成要求\n请为每一集生成详细的内容规划，确保：\n\n1. **整体连贯性**: 所有剧集构成完整的故事弧线\n2. **节奏控制**: 根据\"medium\"节奏要求安排情节发展\n3. **复杂度适配**: 按照\"medium\"复杂度设计情节\n4. **角色发展**: 每个角色都有清晰的成长轨迹\n5. **冲突升级**: 冲突逐步升级，在适当时机达到高潮\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n\n1. **episode_number**: 集数\n2. **title**: 剧集标题\n3. **summary**: 剧集概要（150-300字）\n4. **plot_points**: 主要情节点列表\n5. **character_arcs**: 角色发展安排\n6. **conflicts**: 本集的冲突设置\n7. **scene_count**: 预估场景数量\n8. **emotional_tone**: 情感基调\n9. **key_moments**: 关键时刻描述\n10. **cliffhanger**: 悬念设置（如果适用）\n\n## 情节发展建议\n- 第1集：角色介绍和背景设定，建立世界观\n- 前1/3：角色关系建立，冲突铺垫\n- 中1/3：冲突发展，情节推进，角色成长\n- 后1/3：冲突高潮，问题解决，情感升华\n- 最后集：故事收尾，角色归宿，主题点题\n\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"...\",\n            \"summary\": \"...\",\n            \"plot_points\": [\n                {\n                    \"sequence\": 1,\n                    \"description\": \"...\",\n                    \"timing\": \"开场/前段/中段/后段/结尾\"\n                }\n            ],\n            \"character_arcs\": {\n                \"character_name\": \"本集的角色发展\"\n            },\n            \"conflicts\": [\n                {\n                    \"type\": \"内心冲突/人际冲突/环境冲突\",\n                    \"description\": \"...\",\n                    \"intensity\": \"低/中/高\"\n                }\n            ],\n            \"scene_count\": 5,\n            \"emotional_tone\": \"...\",\n            \"key_moments\": [\"...\"],\n            \"cliffhanger\": \"...\"\n        }\n    ]\n}','ai_deepseek','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": null, \"style_preferences\": [], \"additional_requirements\": \"\"}','draft',NULL,NULL,'2025-09-12 07:03:46','2025-09-12 07:03:46');
/*!40000 ALTER TABLE `episodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `file_path` varchar(512) NOT NULL,
  `file_size` int NOT NULL,
  `mime_type` varchar(100) NOT NULL,
  `description` text,
  `prompt` text,
  `user_id` int NOT NULL,
  `created_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `ix_images_id` (`id`),
  CONSTRAINT `images_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `images`
--

LOCK TABLES `images` WRITE;
/*!40000 ALTER TABLE `images` DISABLE KEYS */;
/*!40000 ALTER TABLE `images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `script_templates`
--

DROP TABLE IF EXISTS `script_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `script_templates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL COMMENT '模板名称',
  `category` varchar(50) DEFAULT NULL COMMENT '模板分类',
  `template_content` text COMMENT '模板内容',
  `structure` json DEFAULT NULL COMMENT '结构定义',
  `variables` json DEFAULT NULL COMMENT '变量定义',
  `usage_count` int DEFAULT NULL COMMENT '使用次数',
  `rating` float DEFAULT NULL COMMENT '评分',
  `is_active` tinyint(1) DEFAULT NULL COMMENT '是否激活',
  `is_public` tinyint(1) DEFAULT NULL COMMENT '是否公开',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_script_templates_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `script_templates`
--

LOCK TABLES `script_templates` WRITE;
/*!40000 ALTER TABLE `script_templates` DISABLE KEYS */;
/*!40000 ALTER TABLE `script_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `scripts`
--

DROP TABLE IF EXISTS `scripts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scripts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `episode_id` int NOT NULL COMMENT '剧集ID',
  `title` varchar(255) NOT NULL COMMENT '剧本标题',
  `content` text COMMENT '剧本内容',
  `scenes` json DEFAULT NULL COMMENT '场景列表',
  `dialogues` json DEFAULT NULL COMMENT '对话列表',
  `stage_directions` json DEFAULT NULL COMMENT '舞台指示',
  `format_type` varchar(50) DEFAULT NULL COMMENT '剧本格式类型',
  `language` varchar(10) DEFAULT NULL COMMENT '语言',
  `page_count` int DEFAULT NULL COMMENT '页数',
  `word_count` int DEFAULT NULL COMMENT '字数',
  `character_count` int DEFAULT NULL COMMENT '字符数',
  `generation_prompt` text COMMENT '生成提示词',
  `ai_model` varchar(50) DEFAULT NULL COMMENT '使用的AI模型',
  `generation_params` json DEFAULT NULL COMMENT '生成参数',
  `status` varchar(20) DEFAULT NULL COMMENT '状态：draft, approved, published',
  `version` varchar(20) DEFAULT NULL COMMENT '版本号',
  `tags` json DEFAULT NULL COMMENT '标签列表',
  `extra_metadata` json DEFAULT NULL COMMENT '额外元数据',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `episode_id` (`episode_id`),
  KEY `ix_scripts_id` (`id`),
  CONSTRAINT `scripts_ibfk_1` FOREIGN KEY (`episode_id`) REFERENCES `episodes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scripts`
--

LOCK TABLES `scripts` WRITE;
/*!40000 ALTER TABLE `scripts` DISABLE KEYS */;
INSERT INTO `scripts` VALUES (1,6,'遇见神秘老K - 剧本','\n\n**剧本标题：HelloWorld**  \n**剧集标题：第1集 - 遇见神秘老K**  \n\n---\n\n**场景 1**  \n\n**场景标题：学校科技展**  \n\n**外景 - 日**  \n\n一片繁忙的校园，一年一度的科技展正在热烈进行。各个展位上，学生们展示着自己最新的科技创意。人群中，小雅兴奋地穿梭在各个展位之间。\n\n**场景描述：**  \n学校的操场上，搭建了多个帐篷，展台上摆满了各种科技产品和模型。学生们聚集在不同的展位前，讨论着最新的技术。\n\n**道具：**  \n展台、电子产品、宣传手册\n\n**出场角色：**  \n小雅、老K、其他学生\n\n---\n\n**场景 2**  \n\n**场景标题：科技展幕后交流**  \n\n**内景 - 日**  \n\n展览结束后，小雅和老K在一个安静的角落交谈，讨论技术和未来的可能性。\n\n**场景描述：**  \n展览会场的一个角落，背景是其他展台在收拾的声音，气氛稍显安静而神秘。\n\n**道具：**  \n笔记本电脑、咖啡杯\n\n**出场角色：**  \n小雅、老K\n\n---\n\n**场景 3**  \n\n**场景标题：编程初探**  \n\n**内景 - 夜**  \n\n老K的工作室，小雅坐在电脑前，老K在旁边指导着她。\n\n**场景描述：**  \n一个简洁的工作室，墙上贴满了代码和科技海报。灯光柔和，电脑屏幕的光照亮了小雅认真学习的脸。\n\n**道具：**  \n电脑、键盘、便签纸\n\n**出场角色：**  \n小雅、老K\n\n---\n\n**场景 4**  \n\n**场景标题：小雅的自我怀疑**  \n\n**内景 - 夜**  \n\n小雅在宿舍，面对电脑屏幕，她看上去有些沮丧。\n\n**场景描述：**  \n宿舍内安静的环境，小雅坐在桌前，手指在键盘上停顿，脸上流露出犹豫和不安。\n\n**道具：**  \n电脑、书、笔记本\n\n**出场角色：**  \n小雅\n\n---\n\n**场景 5**  \n\n**场景标题：新一天的开始**  \n\n**外景 - 早晨**  \n\n阳光洒在校园，小雅充满期待地走向老K的工作室。\n\n**场景描述：**  \n清晨的校园，学生们三三两两地走向教室，小雅步伐轻快，脸上带着微笑。\n\n**道具：**  \n书包、早餐\n\n**出场角色：**  \n小雅\n\n---\n\n**对话列表：**\n\n1. **场景 1**\n   - **小雅**:  \n     今天的科技展真是太精彩了！\n   - **老K**:  \n     （微笑）你是对科技感兴趣吗？\n\n2. **场景 2**\n   - **小雅**:  \n     老K，你的展示让我大开眼界。\n   - **老K**:  \n     喜欢就好，如果感兴趣，我可以教你一些基础。\n\n3. **场景 3**\n   - **老K**:  \n     编程并不难，关键是要理解逻辑。\n   - **小雅**:  \n     （认真）我会努力学的。\n\n4. **场景 4**\n   - **小雅**:  \n     （自言自语）我能做到吗？\n\n5. **场景 5**\n   - **小雅**:  \n     今天一定会更好！\n\n---\n\n**舞台指示：**\n\n1. **场景 1**\n   - **对话前**: 小雅兴奋地穿过人群。\n\n2. **场景 2**\n   - **对话中**: 老K递给小雅一本笔记。\n\n3. **场景 3**\n   - **对话后**: 小雅在键盘上打字，老K在一旁微笑。\n\n4. **场景 4**\n   - **对话前**: 小雅坐在电脑前，眉头紧锁。\n\n5. **场景 5**\n   - **对话后**: 小雅迎着朝阳走去，显得充满信心。\n\n---\n\n**剧本元数据：**\n\n```json\n{\n    \"total_scenes\": 5,\n    \"total_dialogues\": 10,\n    \"estimated_duration\": \"30分钟\",\n    \"shooting_locations\": [\"学校操场\", \"展览会场\", \"老K的工作室\", \"小雅的宿舍\"],\n    \"main_characters\": [\"小雅\", \"老K\"],\n    \"special_effects\": []\n}\n```\n\n---\n\n**剧本结构：**\n\n1. **开场 (前10%)**: 小雅出现在科技展，第一次被老K的技术展示吸引。\n2. **发展 (中70%)**: 小雅和老K建立联系，老K开始教授编程，小雅面临自我怀疑。\n3. **高潮 (后15%)**: 小雅在怀疑中找到自信，决心继续学习。\n4. **结尾 (最后5%)**: 新的一天开始，小雅充满期待地走向老K的工作室，为下集埋下伏笔。\n\n---\n\n**说明：**\n\n该剧本以现代校园为背景，通过小雅和老K的相识和互动，展现科技与人际关系的融合。每个场景都围绕角色的成长与互动展开，旨在激励观众对科技和学习的兴趣。','[{\"time\": \"日\", \"notes\": \"需要布置多个科技展台，背景音效可加入学生的讨论声。\", \"props\": [\"展台\", \"电子产品\", \"宣传手册\"], \"location\": \"学校操场\", \"characters\": [\"小雅\", \"老K\", \"其他学生\"], \"description\": \"学校的操场上，搭建了多个帐篷，展台上摆满了各种科技产品和模型。学生们聚集在不同的展位前，讨论着最新的技术。\", \"scene_number\": 1}, {\"time\": \"日\", \"notes\": \"该场景需要捕捉学生们撤展的背景音效。\", \"props\": [\"笔记本电脑\", \"咖啡杯\"], \"location\": \"展览会场\", \"characters\": [\"小雅\", \"老K\"], \"description\": \"展览会场的一个角落，背景是其他展台在收拾的声音，气氛稍显安静而神秘。\", \"scene_number\": 2}, {\"time\": \"夜\", \"notes\": \"工作室环境需营造科技感，光线柔和以突出人物面部表情。\", \"props\": [\"电脑\", \"键盘\", \"便签纸\"], \"location\": \"老K的工作室\", \"characters\": [\"小雅\", \"老K\"], \"description\": \"一个简洁的工作室，墙上贴满了代码和科技海报。灯光柔和，电脑屏幕的光照亮了小雅认真学习的脸。\", \"scene_number\": 3}, {\"time\": \"夜\", \"notes\": \"宿舍布景简单，重点突出小雅内心的犹豫。\", \"props\": [\"电脑\", \"书\", \"笔记本\"], \"location\": \"小雅的宿舍\", \"characters\": [\"小雅\"], \"description\": \"宿舍内安静的环境，小雅坐在桌前，手指在键盘上停顿，脸上流露出犹豫和不安。\", \"scene_number\": 4}, {\"time\": \"早晨\", \"notes\": \"需拍摄清晨的自然光线，小雅的面部表情要传达出自信。\", \"props\": [\"书包\", \"早餐\"], \"location\": \"校园\", \"characters\": [\"小雅\"], \"description\": \"清晨的校园，学生们三三两两地走向教室，小雅步伐轻快，脸上带着微笑。\", \"scene_number\": 5}]','[{\"notes\": \"表现出对科技的热情。\", \"action\": \"穿梭在展位之间\", \"content\": \"今天的科技展真是太精彩了！\", \"emotion\": \"兴奋\", \"character\": \"小雅\", \"scene_number\": 1}, {\"notes\": \"表现出对小雅的好奇。\", \"action\": \"微笑着看着小雅\", \"content\": \"（微笑）你是对科技感兴趣吗？\", \"emotion\": \"友好\", \"character\": \"老K\", \"scene_number\": 1}, {\"notes\": \"表现出对老K的尊敬。\", \"action\": \"认真倾听\", \"content\": \"老K，你的展示让我大开眼界。\", \"emotion\": \"钦佩\", \"character\": \"小雅\", \"scene_number\": 2}, {\"notes\": \"表现出愿意分享知识的态度。\", \"action\": \"递给小雅一本笔记\", \"content\": \"喜欢就好，如果感兴趣，我可以教你一些基础。\", \"emotion\": \"开放\", \"character\": \"老K\", \"scene_number\": 2}, {\"notes\": \"用轻松的语气鼓励小雅。\", \"action\": \"指着电脑屏幕\", \"content\": \"编程并不难，关键是要理解逻辑。\", \"emotion\": \"鼓励\", \"character\": \"老K\", \"scene_number\": 3}, {\"notes\": \"表现出对学习的决心。\", \"action\": \"专心打字\", \"content\": \"（认真）我会努力学的。\", \"emotion\": \"坚定\", \"character\": \"小雅\", \"scene_number\": 3}, {\"notes\": \"表现出内心的挣扎。\", \"action\": \"停顿在键盘前\", \"content\": \"（自言自语）我能做到吗？\", \"emotion\": \"怀疑\", \"character\": \"小雅\", \"scene_number\": 4}, {\"notes\": \"面带微笑，表现出积极的情绪。\", \"action\": \"大步走向前\", \"content\": \"今天一定会更好！\", \"emotion\": \"自信\", \"character\": \"小雅\", \"scene_number\": 5}]','[{\"type\": \"动作\", \"timing\": \"对话前\", \"content\": \"小雅兴奋地穿过人群。\", \"scene_number\": 1}, {\"type\": \"动作\", \"timing\": \"对话中\", \"content\": \"老K递给小雅一本笔记。\", \"scene_number\": 2}, {\"type\": \"动作\", \"timing\": \"对话后\", \"content\": \"小雅在键盘上打字，老K在一旁微笑。\", \"scene_number\": 3}, {\"type\": \"表情\", \"timing\": \"对话前\", \"content\": \"小雅坐在电脑前，眉头紧锁。\", \"scene_number\": 4}, {\"type\": \"动作\", \"timing\": \"对话后\", \"content\": \"小雅迎着朝阳走去，显得充满信心。\", \"scene_number\": 5}]','screenplay','zh-CN',1,190,2049,'你是一个专业的剧本编剧，擅长将剧集大纲转化为详细的可拍摄剧本。请基于以下信息生成完整的screenplay格式剧本：\n\n## 故事背景\n故事标题：HelloWorld\n类型：drama\n时间设定：现代\n地点设定：学校\n## 剧集信息\n剧集标题：第1集 - 遇见神秘老K\n剧集概要：小雅，一个充满活力的大学生，梦想成为一名平面设计师。在学校的科技展上，她被一位神秘人物——老K的技术展示深深吸引。两人迅速成为朋友，老K开始教小雅一些基本的编程知识。小雅的好奇心和学习能力让老K印象深刻，而他们的友谊也在这过程中逐渐加深。故事通过展示小雅的日常生活和学习过程，逐步建立起故事的背景和角色关系。\n预计时长：30分钟\n场景数量：5个\n## 情节要点\n1. 小雅参加学校科技展，首次见到老K的技术展示。 (开场)\n2. 小雅和老K在科技展后交谈，发现共同兴趣。 (前段)\n3. 老K开始教小雅基础编程知识。 (中段)\n## 角色发展\n- 老K: 从独行的技术高手到愿意分享知识，开始建立对人际关系的信任。\n- 小雅: 从对数字世界一知半解到开始学习编程，展现出强烈的好奇心和学习能力。\n## 冲突设置\n- : 小雅在学习新技能时的自我怀疑。 (强度: 低)\n## 主要角色\n小雅：一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n老Ｋ：电子世界的神秘使者，技术高手，信息的守护者\n## 剧本参数\n格式类型：screenplay\n语言：zh-CN\n对话风格：natural\n场景描述详细程度：medium\n\n## 生成要求\n请生成一个完整的可拍摄剧本，包含：\n\n1. **完整剧本内容**: 标准screenplay格式\n2. **场景列表**: 所有拍摄场景\n3. **对话列表**: 所有角色对话\n4. **舞台指示**: 详细的拍摄指导\n\n## 格式要求\n- 使用标准screenplay格式\n- 对话要natural，符合角色性格\n- 场景描述要medium详细\n- 确保剧本结构完整：开场→发展→高潮→结尾\n- 时长控制在30分钟左右\n\n## 剧本结构指导\n### 开场 (前10%)\n- 建立场景和氛围\n- 介绍主要角色状态\n- 引入本集核心问题\n\n### 发展 (中70%)\n- 情节逐步推进\n- 角色冲突展开\n- 悬念和张力建立\n\n### 高潮 (后15%)\n- 冲突达到顶点\n- 关键选择时刻\n- 情感爆发点\n\n### 结尾 (最后5%)\n- 问题解决或转折\n- 为下集埋下伏笔\n- 情感落地\n\n## 输出格式\n请以JSON格式返回：\n\n{\n    \"content\": \"完整的剧本内容，使用screenplay标准格式\",\n    \"scenes\": [\n        {\n            \"scene_number\": 1,\n            \"location\": \"拍摄地点\",\n            \"time\": \"时间（日/夜/黄昏等）\",\n            \"description\": \"场景描述\",\n            \"characters\": [\"出场角色\"],\n            \"props\": [\"需要的道具\"],\n            \"notes\": \"拍摄注意事项\"\n        }\n    ],\n    \"dialogues\": [\n        {\n            \"scene_number\": 1,\n            \"character\": \"角色名\",\n            \"content\": \"对话内容\",\n            \"emotion\": \"情感状态\",\n            \"action\": \"伴随动作\",\n            \"notes\": \"表演提示\"\n        }\n    ],\n    \"stage_directions\": [\n        {\n            \"scene_number\": 1,\n            \"timing\": \"对话前/对话中/对话后\",\n            \"content\": \"舞台指示内容\",\n            \"type\": \"动作/表情/环境/效果\"\n        }\n    ],\n    \"metadata\": {\n        \"total_scenes\": 0,\n        \"total_dialogues\": 0,\n        \"estimated_duration\": \"30分钟\",\n        \"shooting_locations\": [],\n        \"main_characters\": [],\n        \"special_effects\": []\n    }\n}','ai_openai','{\"model\": null, \"temperature\": 0.7, \"dialogue_style\": \"natural\", \"style_preferences\": [], \"scene_detail_level\": \"medium\", \"additional_requirements\": \"\"}','draft','1.0',NULL,'{\"storyboard\": {\"frames\": [{\"ai_prompt\": \"学校的操场上，搭建了多个帐篷，展台上摆满了各种科技产品和模型。学生们聚集在不同的展位前，讨论着最新的技术。\", \"shot_type\": \"中景\", \"composition\": null, \"description\": \"学校的操场上，搭建了多个帐篷，展台上摆满了各种科技产品和模型。学生们聚集在不同的展位前，讨论着最新的技术。\", \"frame_number\": 1, \"scene_number\": 1, \"camera_movement\": null, \"duration_seconds\": 3, \"reference_images\": []}, {\"ai_prompt\": \"展览会场的一个角落，背景是其他展台在收拾的声音，气氛稍显安静而神秘。\", \"shot_type\": \"中景\", \"composition\": null, \"description\": \"展览会场的一个角落，背景是其他展台在收拾的声音，气氛稍显安静而神秘。\", \"frame_number\": 2, \"scene_number\": 2, \"camera_movement\": null, \"duration_seconds\": 3, \"reference_images\": []}, {\"ai_prompt\": \"一个简洁的工作室，墙上贴满了代码和科技海报。灯光柔和，电脑屏幕的光照亮了小雅认真学习的脸。\", \"shot_type\": \"中景\", \"composition\": null, \"description\": \"一个简洁的工作室，墙上贴满了代码和科技海报。灯光柔和，电脑屏幕的光照亮了小雅认真学习的脸。\", \"frame_number\": 3, \"scene_number\": 3, \"camera_movement\": null, \"duration_seconds\": 3, \"reference_images\": []}, {\"ai_prompt\": \"宿舍内安静的环境，小雅坐在桌前，手指在键盘上停顿，脸上流露出犹豫和不安。\", \"shot_type\": \"中景\", \"composition\": null, \"description\": \"宿舍内安静的环境，小雅坐在桌前，手指在键盘上停顿，脸上流露出犹豫和不安。\", \"frame_number\": 4, \"scene_number\": 4, \"camera_movement\": null, \"duration_seconds\": 3, \"reference_images\": []}, {\"ai_prompt\": \"清晨的校园，学生们三三两两地走向教室，小雅步伐轻快，脸上带着微笑。\", \"shot_type\": \"中景\", \"composition\": null, \"description\": \"清晨的校园，学生们三三两两地走向教室，小雅步伐轻快，脸上带着微笑。\", \"frame_number\": 5, \"scene_number\": 5, \"camera_movement\": null, \"duration_seconds\": 3, \"reference_images\": []}]}}','2025-09-12 07:17:00','2025-09-12 11:04:17');
/*!40000 ALTER TABLE `scripts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stories`
--

DROP TABLE IF EXISTS `stories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL COMMENT '故事标题',
  `genre` varchar(50) NOT NULL COMMENT '故事类型',
  `theme` varchar(255) DEFAULT NULL COMMENT '故事主题',
  `target_audience` varchar(100) DEFAULT NULL COMMENT '目标受众',
  `duration_minutes` int DEFAULT NULL COMMENT '预计总时长（分钟）',
  `premise` text COMMENT '故事前提',
  `synopsis` text COMMENT '故事概要',
  `main_conflict` text COMMENT '主要冲突',
  `resolution` text COMMENT '解决方案',
  `main_characters` json DEFAULT NULL COMMENT '主要角色列表',
  `character_relationships` json DEFAULT NULL COMMENT '角色关系',
  `setting_time` varchar(100) DEFAULT NULL COMMENT '时间设定',
  `setting_location` varchar(255) DEFAULT NULL COMMENT '地点设定',
  `world_building` text COMMENT '世界观设定',
  `generation_prompt` text COMMENT '生成提示词',
  `ai_model` varchar(50) DEFAULT NULL COMMENT '使用的AI模型',
  `generation_params` json DEFAULT NULL COMMENT '生成参数',
  `status` varchar(20) DEFAULT NULL COMMENT '状态：draft, approved, published',
  `is_public` tinyint(1) DEFAULT NULL COMMENT '是否公开',
  `tags` json DEFAULT NULL COMMENT '标签列表',
  `extra_metadata` json DEFAULT NULL COMMENT '额外元数据',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_stories_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stories`
--

LOCK TABLES `stories` WRITE;
/*!40000 ALTER TABLE `stories` DISABLE KEYS */;
INSERT INTO `stories` VALUES (1,'校园青春物语','青春','成长与友谊','年轻人',15,'讲述大学生活中的青春故事','小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。','学业压力与个人理想的冲突','通过努力和身边人的帮助，找到了平衡点',NULL,NULL,'现代','大学校园','现实主义风格的校园环境',NULL,NULL,NULL,'draft',1,'[\"校园\", \"青春\", \"成长\"]',NULL,'2025-08-12 07:46:26','2025-08-12 07:46:26'),(2,'测试故事','drama','友情','年轻人',30,'这是一个关于友情与成长的现代都市故事。','主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。','主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。','通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。','[{\"name\": \"主人公A\", \"role\": \"protagonist\", \"description\": \"积极向上的年轻人\"}, {\"name\": \"主人公B\", \"role\": \"supporting\", \"description\": \"智慧可靠的朋友\"}]','{\"group_dynamics\": \"团结互助的友好关系\", \"protagonist_friend\": \"深厚的友谊，相互支持\"}','现代','城市','现实世界','请为以下短剧创作一个完整的故事概要：\n\n标题: 测试故事\n类型: drama\n主题: 友情\n目标受众: 年轻人\n总时长: 30分钟\n\n主要角色:\n- 小雅: 一个活泼可爱的年轻女孩，充满好奇心和冒险精神 背景: 小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n- 李教授: 一位博学的中年教授，温和而富有智慧 背景: 李教授是一位45岁的大学教授，专门研究人工智能和机器学习。他为人温和，深受学生喜爱，经常在学术会议上发表演讲。他有一个幸福的家庭，业余时间喜欢阅读和园艺。\n\n设定:\n- 时间: 现代\n- 地点: 城市\n- 世界观: 现实世界\n\n请生成包含以下内容的故事概要:\n1. 故事前提 (premise)\n2. 详细概要 (synopsis)\n3. 主要冲突 (main_conflict)\n4. 解决方案 (resolution)\n5. 角色关系 (character_relationships)\n6. 主要角色信息 (main_characters)\n\n格式要求:\n- 使用JSON格式返回\n- 内容要符合drama类型的特点\n- 适合年轻人观看\n- 故事要有完整的起承转合结构\n\n额外要求: 积极向上','ai_story_generation','{\"character_ids\": [1, 2], \"style_preferences\": null, \"content_restrictions\": null, \"additional_requirements\": \"积极向上\"}','draft',0,'[\"测试\"]',NULL,'2025-08-13 17:23:46','2025-08-13 17:23:46'),(3,'为什么爱我是川普？','romance','霸总，美女，中国，古风','五十岁以下的红脖子',30,'这是一个关于友情与成长的现代都市故事。','主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。','主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。','通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。','[{\"name\": \"主人公A\", \"role\": \"protagonist\", \"description\": \"积极向上的年轻人\"}, {\"name\": \"主人公B\", \"role\": \"supporting\", \"description\": \"智慧可靠的朋友\"}]','{\"group_dynamics\": \"团结互助的友好关系\", \"protagonist_friend\": \"深厚的友谊，相互支持\"}','未来一年','华盛顿','中国龙牛逼，中国红傻逼','请为以下短剧创作一个完整的故事概要：\n\n标题: 为什么爱我是川普？\n类型: romance\n主题: 霸总，美女，中国，古风\n目标受众: 五十岁以下的红脖子\n总时长: 30分钟\n\n主要角色:\n- 小雅: 一个活泼可爱的年轻女孩，充满好奇心和冒险精神 背景: 小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n\n设定:\n- 时间: 未来一年\n- 地点: 华盛顿\n- 世界观: 中国龙牛逼，中国红傻逼\n\n请生成包含以下内容的故事概要:\n1. 故事前提 (premise)\n2. 详细概要 (synopsis)\n3. 主要冲突 (main_conflict)\n4. 解决方案 (resolution)\n5. 角色关系 (character_relationships)\n6. 主要角色信息 (main_characters)\n\n格式要求:\n- 使用JSON格式返回\n- 内容要符合romance类型的特点\n- 适合五十岁以下的红脖子观看\n- 故事要有完整的起承转合结构\n\n额外要求: 我永远是最美的','ai_story_generation','{\"character_ids\": [1], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"我永远是最美的\"}','draft',0,'[]',NULL,'2025-08-13 17:26:42','2025-08-13 17:26:42'),(4,'你好啊','drama','你好','你好',30,'这是一个关于友情与成长的现代都市故事。','主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。','主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。','通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。','[{\"name\": \"主人公A\", \"role\": \"protagonist\", \"description\": \"积极向上的年轻人\"}, {\"name\": \"主人公B\", \"role\": \"supporting\", \"description\": \"智慧可靠的朋友\"}]','{\"group_dynamics\": \"团结互助的友好关系\", \"protagonist_friend\": \"深厚的友谊，相互支持\"}','','','','请为以下短剧创作一个完整的故事概要：\n\n标题: 你好啊\n类型: drama\n主题: 你好\n目标受众: 你好\n总时长: 30分钟\n\n主要角色:\n- 宝宝: 一个美丽的中国女子，全世界都喜欢\n\n设定:\n- 时间: 现代\n- 地点: 待定\n- 世界观: 现实世界\n\n请生成包含以下内容的故事概要:\n1. 故事前提 (premise)\n2. 详细概要 (synopsis)\n3. 主要冲突 (main_conflict)\n4. 解决方案 (resolution)\n5. 角色关系 (character_relationships)\n6. 主要角色信息 (main_characters)\n\n格式要求:\n- 使用JSON格式返回\n- 内容要符合drama类型的特点\n- 适合你好观看\n- 故事要有完整的起承转合结构','ai_story_generation','{\"character_ids\": [5], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"\"}','draft',0,'[]',NULL,'2025-08-15 03:07:12','2025-08-15 03:07:12'),(5,'３３','drama','３３','３３',30,NULL,'```json\n{\n    \"premise\": \"在一个充满未知与挑战的电子时代，年轻的大学生小雅、博学的李教授和神秘的老K共同面对一场威胁整个电子世界的黑客攻击。他们需要发挥各自的特长，携手合作，保护数字世界的安全与稳定。\",\n    \n    \"synopsis\": \"小雅是一名充满活力的艺术设计学生，偶然间她在一次校园讲座中结识了李教授。李教授提到了一场即将到来的关于人工智能与安全的研讨会，并邀请小雅参加。在研讨会上，他们遇到了神秘的老K，这位电子世界的传奇人物。就在此时，整个电子世界遭遇了史无前例的黑客攻击，威胁到人类的生活和信息安全。小雅、李教授和老K决定联合起来，利用他们各自的专业知识和技能，抵御这场攻击。小雅用她的设计天赋帮助设计出直观的用户界面，李教授提供了深厚的理论支持，老K则用他的技术天赋破解黑客的种种诡计。经过一场惊心动魄的斗智斗勇，他们成功化解了危机，恢复了电子世界的和平。\",\n    \n    \"main_conflict\": \"一场突如其来的黑客攻击威胁着电子世界的安全，所有的信息和系统面临崩溃的风险。小雅、李教授和老K必须在时间有限的情况下合作，阻止这场危机。\",\n    \n    \"resolution\": \"三人合力，通过技术手段和创新设计成功阻止了黑客的攻击，恢复了系统的正常运作，并加强了安全措施，确保未来的数字安全。\",\n    \n    \"character_relationships\": {\n        \"小雅和李教授\": \"师生关系，李教授是小雅的导师，给予她学术上的指引。\",\n        \"小雅和老K\": \"合作伙伴关系，老K欣赏小雅的创造力，小雅对老K的技术能力充满敬意。\",\n        \"李教授和老K\": \"同行者，尽管领域不同，但在此次事件中形成了深厚的友谊。\"\n    },\n    \n    \"main_characters\": [\n        {\n            \"name\": \"小雅\",\n            \"description\": \"活泼可爱的年轻女孩，充满好奇心和冒险精神。22岁的大学生，主修艺术设计。\"\n        },\n        {\n            \"name\": \"李教授\",\n            \"description\": \"博学的中年教授，温和而富有智慧。45岁的大学教授，研究人工智能和机器学习。\"\n        },\n        {\n            \"name\": \"老K\",\n            \"description\": \"电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。\"\n        }\n    ],\n    \n    \"plot_structure\": {\n        \"act1\": \"小雅与李教授在校园中相遇，并被邀请参加关于人工智能的研讨会。\",\n        \"act2\": \"在研讨会上，黑客攻击突如其来，三人决定携手应对危机。\",\n        \"act3\": \"通过团队合作，成功阻止攻击，恢复电子世界的安全，并收获了彼此之间的信任和友谊。\"\n    },\n    \n    \"core_values\": \"团结与合作、科技的力量、勇气与智慧在面对危机时的重要性。\",\n    \n    \"visual_style\": \"现代科技感与创新设计融合，色彩鲜明且具有未来感的视觉呈现。\",\n    \n    \"selling_points\": [\n        \"结合现代科技与艺术设计的跨界合作。\",\n        \"充满悬疑与紧张的黑客对决。\",\n        \"年轻人和专家的协作展现出智慧与勇气的力量。\"\n    ]\n}\n```',NULL,NULL,'null','null','','','','你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据以下信息创作一个完整的故事概要：\n\n## 基本信息\n故事标题：３３\n类型：drama\n主题：３３\n目标受众：３３\n总时长：30分钟\n## 主要角色\n### 小雅\n描述：一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n背景：小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n### 李教授\n描述：一位博学的中年教授，温和而富有智慧\n背景：李教授是一位45岁的大学教授，专门研究人工智能和机器学习。他为人温和，深受学生喜爱，经常在学术会议上发表演讲。他有一个幸福的家庭，业余时间喜欢阅读和园艺。\n### 老Ｋ\n描述：老Ｋ，电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。他的眼神如同星空般深邃，思绪比电流更快。身穿时尚黑色外套，手持闪烁的键盘，仿佛随时能解锁未知的密码。老Ｋ是信息的守护者，技术的引领者，无所不能的数字化奇才。\n背景：在电子世界的边缘，存在着一个神秘的使者，人们称之为老Ｋ。他是信息的守护者，技术的引领者，仿佛是数字世界的主宰。穿着时尚黑色外套的老Ｋ总是手持闪烁的键盘，那键盘上的每一个按键都是他与世界对话的媒介。\n\n起初，老Ｋ只是一个普通的程序员，生活在一个被遗忘的小镇上。但一次偶然的机会，他发现了一本神秘的电子笔记本，里面记载着无数未知的密码与智慧。从那一刻起，老Ｋ的生活发生了翻天覆地的变化。\n\n经过数月的研究与实践，老Ｋ掌握了超越常人的技术，成为了电子世界的传奇人物。他的眼神如同星空般深邃，思绪比电流更快，仿佛是连接着现实与虚拟的桥梁。在他的指引下，电子世界变得更加繁荣与安全。\n\n然而，正当人们认为老Ｋ已经掌握了一切的时候，一场突如其来的黑客攻击危及了整个电子世界的安全。面对这一挑战，老Ｋ毫不犹豫地投身战斗之中。他用自己的智慧和技术，与黑客展开了一场惊心动魄的较量。最终，老Ｋ凭借着无与伦比的能力，保护了电子世界的和平与稳定。\n\n从此以后，老Ｋ成为了电子世界的传说。人们传颂着他的勇气和智慧，他的名字永远镌刻在电子世界的史册之中。身披时尚黑色外套的老Ｋ，继续守护着这个\n\n## 设定信息\n## 创作要求\n## 生成内容\n请创作一个完整的故事概要，以JSON格式返回，包含以下内容：\n\n1. **故事前提** (premise): 故事的核心概念和基础设定\n2. **详细概要** (synopsis): 完整的故事梗概，包含起承转合\n3. **主要冲突** (main_conflict): 故事的核心冲突和矛盾\n4. **解决方案** (resolution): 冲突的解决方式和故事结局\n5. **角色关系** (character_relationships): 主要角色之间的关系网\n6. **主角信息** (main_characters): 重新整理的主要角色信息\n7. **情节结构** (plot_structure): 故事的三幕式结构划分\n8. **核心价值** (core_values): 故事要传达的价值观和意义\n9. **视觉风格** (visual_style): 适合的视觉呈现风格建议\n10. **营销卖点** (selling_points): 故事的亮点和吸引观众的要素\n\n## 创作原则\n- 确保故事结构完整，有明确的开始、发展、高潮和结局\n- 角色设定要符合drama类型的特点\n- 适合３３观看\n- 内容积极向上，传播正能量\n- 具有可操作性，适合视频制作\n\n## 输出格式\n{\n    \"premise\": \"...\",\n    \"synopsis\": \"...\",\n    \"main_conflict\": \"...\",\n    \"resolution\": \"...\",\n    \"character_relationships\": {...},\n    \"main_characters\": [...],\n    \"plot_structure\": {\n        \"act1\": \"...\",\n        \"act2\": \"...\",\n        \"act3\": \"...\"\n    },\n    \"core_values\": \"...\",\n    \"visual_style\": \"...\",\n    \"selling_points\": [...]\n}','ai_openai','{\"model\": \"\", \"temperature\": 0.7, \"character_ids\": [1, 2, 10], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"\"}','draft',0,'[]',NULL,'2025-09-12 05:35:21','2025-09-12 05:35:21'),(6,'商锋','drama','商业，职场','成人，白领',30,NULL,'```json\n{\n    \"premise\": \"在一个高度信息化的未来，北京、上海和香港成为了全球商业的中枢。李教授、小雅和老Ｋ在一次意外事件中被卷入了一场关于人工智能和商业竞争的较量，他们需要合作应对来自技术世界的巨大挑战。\",\n    \"synopsis\": \"故事发生在2025年，当全球商业竞争愈发激烈，李教授在北京的一次人工智能与商业会议上发表了关于AI发展的演讲，吸引了众多商业领袖和技术专家的关注。美丽的宝宝是这次会议的主持人，她因其出色的组织能力和魅力倍受赞赏。小雅作为李教授的学生，随他一同参会，渴望在这个平台上展示自己的设计才能。神秘的老Ｋ通过网络直播关注着这场会议，突然，一场前所未有的黑客攻击席卷而来，威胁到整个会议乃至全球的商业安全。老Ｋ意识到这是来自一个强大的黑客组织的袭击，他决定亲自出手。李教授凭借其深厚的专业知识，与老Ｋ展开合作，而小雅则利用她的设计能力为他们提供视觉化的技术支持。经过一番波折和智慧的较量，他们终于成功瓦解了黑客的攻击，保护了电子世界的安全。通过这次事件，他们意识到技术的力量和协作的重要性。\",\n    \"main_conflict\": \"李教授和团队需要制止一场致命的黑客攻击，这将影响全球商业和技术安全。\",\n    \"resolution\": \"通过团队的协作和老Ｋ的技术引领，成功瓦解了黑客的攻击，确保了商业和技术的安全。\",\n    \"character_relationships\": {\n        \"李教授\": {\n            \"小雅\": \"师生关系，李教授是小雅的导师。\",\n            \"宝宝\": \"因会议结识，互相尊重。\",\n            \"老Ｋ\": \"合作伙伴，共同应对黑客攻击。\"\n        },\n        \"小雅\": {\n            \"李教授\": \"导师，崇拜和学习对象。\",\n            \"宝宝\": \"因会议结识，成为朋友。\",\n            \"老Ｋ\": \"敬佩其技术才能。\"\n        },\n        \"老Ｋ\": {\n            \"李教授\": \"尊重其专业知识，合作伙伴。\",\n            \"小雅\": \"欣赏她的创意和勇气。\",\n            \"宝宝\": \"通过网络认识，保持联系。\"\n        },\n        \"宝宝\": {\n            \"李教授\": \"尊重其学术成就。\",\n            \"小雅\": \"欣赏她的活力和创意。\",\n            \"老Ｋ\": \"崇拜其技术能力。\"\n        }\n    },\n    \"main_characters\": [\n        {\n            \"name\": \"李教授\",\n            \"description\": \"一位博学的中年教授，温和而富有智慧，专注于AI研究。\"\n        },\n        {\n            \"name\": \"宝宝\",\n            \"description\": \"一个美丽的中国女子，全世界都喜欢，擅长组织和协调。\"\n        },\n        {\n            \"name\": \"小雅\",\n            \"description\": \"一个活泼可爱的年轻女孩，充满好奇心和冒险精神，主修艺术设计。\"\n        },\n        {\n            \"name\": \"老Ｋ\",\n            \"description\": \"电子世界的神秘使者，技术奇才，信息的守护者。\"\n        }\n    ],\n    \"plot_structure\": {\n        \"act1\": \"李教授在北京的人工智能会议上发言，会议开始时受到广泛关注。\",\n        \"act2\": \"突然的黑客袭击导致技术和商业安全危机，李教授、小雅和老Ｋ展开合作。\",\n        \"act3\": \"经过一系列的智慧与技术的较量，团队成功阻止了黑客攻击，确保了安全。\"\n    },\n    \"core_values\": \"技术与智慧的结合，团队合作的重要性，面对危机时的勇气和责任感。\",\n    \"visual_style\": \"现代都市风格，科技感与未来感兼备，展现电子世界的紧张与活力。\",\n    \"marketing_points\": [\n        \"结合商业与科技的紧张剧情。\",\n        \"角色设定丰富，具备深度与层次。\",\n        \"现代都市与未来科技的视觉冲击。\",\n        \"涉及AI和黑客攻击的严肃主题，贴合当下热点。\"\n    ]\n}\n```',NULL,NULL,'null','null','２０２５','北京，上海，香港','Ｃ端游戏','你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据以下信息创作一个完整的故事概要：\n\n## 基本信息\n故事标题：商锋\n类型：drama\n主题：商业，职场\n目标受众：成人，白领\n总时长：30分钟\n## 主要角色\n### 李教授\n描述：一位博学的中年教授，温和而富有智慧\n背景：李教授是一位45岁的大学教授，专门研究人工智能和机器学习。他为人温和，深受学生喜爱，经常在学术会议上发表演讲。他有一个幸福的家庭，业余时间喜欢阅读和园艺。\n### 宝宝\n描述：一个美丽的中国女子，全世界都喜欢\n### 小雅\n描述：一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n背景：小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n### 老Ｋ\n描述：老Ｋ，电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。他的眼神如同星空般深邃，思绪比电流更快。身穿时尚黑色外套，手持闪烁的键盘，仿佛随时能解锁未知的密码。老Ｋ是信息的守护者，技术的引领者，无所不能的数字化奇才。\n背景：在电子世界的边缘，存在着一个神秘的使者，人们称之为老Ｋ。他是信息的守护者，技术的引领者，仿佛是数字世界的主宰。穿着时尚黑色外套的老Ｋ总是手持闪烁的键盘，那键盘上的每一个按键都是他与世界对话的媒介。\n\n起初，老Ｋ只是一个普通的程序员，生活在一个被遗忘的小镇上。但一次偶然的机会，他发现了一本神秘的电子笔记本，里面记载着无数未知的密码与智慧。从那一刻起，老Ｋ的生活发生了翻天覆地的变化。\n\n经过数月的研究与实践，老Ｋ掌握了超越常人的技术，成为了电子世界的传奇人物。他的眼神如同星空般深邃，思绪比电流更快，仿佛是连接着现实与虚拟的桥梁。在他的指引下，电子世界变得更加繁荣与安全。\n\n然而，正当人们认为老Ｋ已经掌握了一切的时候，一场突如其来的黑客攻击危及了整个电子世界的安全。面对这一挑战，老Ｋ毫不犹豫地投身战斗之中。他用自己的智慧和技术，与黑客展开了一场惊心动魄的较量。最终，老Ｋ凭借着无与伦比的能力，保护了电子世界的和平与稳定。\n\n从此以后，老Ｋ成为了电子世界的传说。人们传颂着他的勇气和智慧，他的名字永远镌刻在电子世界的史册之中。身披时尚黑色外套的老Ｋ，继续守护着这个\n\n## 设定信息\n时间背景：２０２５\n地点设定：北京，上海，香港\n世界观：Ｃ端游戏\n## 创作要求\n额外要求：一波三折\n## 生成内容\n请创作一个完整的故事概要，以JSON格式返回，包含以下内容：\n\n1. **故事前提** (premise): 故事的核心概念和基础设定\n2. **详细概要** (synopsis): 完整的故事梗概，包含起承转合\n3. **主要冲突** (main_conflict): 故事的核心冲突和矛盾\n4. **解决方案** (resolution): 冲突的解决方式和故事结局\n5. **角色关系** (character_relationships): 主要角色之间的关系网\n6. **主角信息** (main_characters): 重新整理的主要角色信息\n7. **情节结构** (plot_structure): 故事的三幕式结构划分\n8. **核心价值** (core_values): 故事要传达的价值观和意义\n9. **视觉风格** (visual_style): 适合的视觉呈现风格建议\n10. **营销卖点** (selling_points): 故事的亮点和吸引观众的要素\n\n## 创作原则\n- 确保故事结构完整，有明确的开始、发展、高潮和结局\n- 角色设定要符合drama类型的特点\n- 适合成人，白领观看\n- 内容积极向上，传播正能量\n- 具有可操作性，适合视频制作\n\n## 输出格式\n{\n    \"premise\": \"...\",\n    \"synopsis\": \"...\",\n    \"main_conflict\": \"...\",\n    \"resolution\": \"...\",\n    \"character_relationships\": {...},\n    \"main_characters\": [...],\n    \"plot_structure\": {\n        \"act1\": \"...\",\n        \"act2\": \"...\",\n        \"act3\": \"...\"\n    },\n    \"core_values\": \"...\",\n    \"visual_style\": \"...\",\n    \"selling_points\": [...]\n}','ai_openai','{\"model\": \"\", \"temperature\": 0.7, \"character_ids\": [2, 5, 1, 10], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"一波三折\"}','draft',0,'[]',NULL,'2025-09-12 05:53:16','2025-09-12 05:53:16'),(7,'333','drama','333','33',30,'在一个充满挑战的数字世界中，三位性格迥异的角色——热爱冒险的小雅、神秘的老K和全球瞩目的宝宝，携手应对突如其来的网络危机，探索彼此的内心世界，最终实现自我成长。','故事发生在一个科技发达的现代世界。小雅是一位充满活力和创意的大学生，她热衷于艺术设计和社交分享。一次偶然的机会，小雅结识了神秘的网络天才老K，并被卷入了一场意料之外的网络危机中。与此同时，全球瞩目的明星宝宝也因网络攻击而面临个人信息泄露的风险。\n\n随着危机的加深，小雅、宝宝和老K三人决定联手解决问题。小雅利用她的设计才能帮助老K分析黑客的攻击模式，而老K则运用他的技术智慧领导反击。在此过程中，宝宝通过她的影响力召集全球的注意力，将事件的真相广而告之。\n\n三人的合作逐渐顺利，他们不仅挫败了黑客的阴谋，还揭示了危机背后的深层次问题：虚拟世界的信任危机和信息安全的重要性。最终，小雅通过这次经历获得了成长，老K进一步巩固了他在数字世界的传奇地位，而宝宝也重新定义了自己的公众角色。','网络攻击导致的信息安全危机，三位角色必须联手阻止黑客的进一步破坏。','通过小雅的设计能力、老K的技术智慧和宝宝的公众影响力，三人成功化解危机，揭示了黑客的真实身份，并在全球范围内提升了信息安全意识。','[{\"name\": \"小雅\", \"role\": \"大学生/艺术设计师\", \"description\": \"一个活泼可爱的年轻女孩，充满好奇心和冒险精神\"}, {\"name\": \"宝宝\", \"role\": \"明星\", \"description\": \"一个美丽的中国女子，全世界都喜欢\"}, {\"name\": \"老K\", \"role\": \"网络天才\", \"description\": \"电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧\"}]','{\"老K\": \"作为团队领袖，以技术智慧指导小雅和宝宝。\", \"宝宝\": \"与小雅和老K联手，通过个人影响力帮助解决危机。\", \"小雅\": \"与老K和宝宝结成伙伴关系，共同应对网络危机。\"}','333','13','32','你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据以下信息创作一个完整的故事概要：\n\n## 基本信息\n故事标题：333\n类型：drama\n主题：333\n目标受众：33\n总时长：30分钟\n## 主要角色\n### 小雅\n描述：一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n背景：小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n### 宝宝\n描述：一个美丽的中国女子，全世界都喜欢\n### 老Ｋ\n描述：老Ｋ，电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。他的眼神如同星空般深邃，思绪比电流更快。身穿时尚黑色外套，手持闪烁的键盘，仿佛随时能解锁未知的密码。老Ｋ是信息的守护者，技术的引领者，无所不能的数字化奇才。\n背景：在电子世界的边缘，存在着一个神秘的使者，人们称之为老Ｋ。他是信息的守护者，技术的引领者，仿佛是数字世界的主宰。穿着时尚黑色外套的老Ｋ总是手持闪烁的键盘，那键盘上的每一个按键都是他与世界对话的媒介。\n\n起初，老Ｋ只是一个普通的程序员，生活在一个被遗忘的小镇上。但一次偶然的机会，他发现了一本神秘的电子笔记本，里面记载着无数未知的密码与智慧。从那一刻起，老Ｋ的生活发生了翻天覆地的变化。\n\n经过数月的研究与实践，老Ｋ掌握了超越常人的技术，成为了电子世界的传奇人物。他的眼神如同星空般深邃，思绪比电流更快，仿佛是连接着现实与虚拟的桥梁。在他的指引下，电子世界变得更加繁荣与安全。\n\n然而，正当人们认为老Ｋ已经掌握了一切的时候，一场突如其来的黑客攻击危及了整个电子世界的安全。面对这一挑战，老Ｋ毫不犹豫地投身战斗之中。他用自己的智慧和技术，与黑客展开了一场惊心动魄的较量。最终，老Ｋ凭借着无与伦比的能力，保护了电子世界的和平与稳定。\n\n从此以后，老Ｋ成为了电子世界的传说。人们传颂着他的勇气和智慧，他的名字永远镌刻在电子世界的史册之中。身披时尚黑色外套的老Ｋ，继续守护着这个\n\n## 设定信息\n时间背景：333\n地点设定：13\n世界观：32\n## 创作要求\n## 生成内容\n请创作一个完整的故事概要，以JSON格式返回，包含以下内容：\n\n1. **故事前提** (premise): 故事的核心概念和基础设定\n2. **详细概要** (synopsis): 完整的故事梗概，包含起承转合\n3. **主要冲突** (main_conflict): 故事的核心冲突和矛盾\n4. **解决方案** (resolution): 冲突的解决方式和故事结局\n5. **角色关系** (character_relationships): 主要角色之间的关系网\n6. **主角信息** (main_characters): 重新整理的主要角色信息\n7. **情节结构** (plot_structure): 故事的三幕式结构划分\n8. **核心价值** (core_values): 故事要传达的价值观和意义\n9. **视觉风格** (visual_style): 适合的视觉呈现风格建议\n10. **营销卖点** (selling_points): 故事的亮点和吸引观众的要素\n\n## 创作原则\n- 确保故事结构完整，有明确的开始、发展、高潮和结局\n- 角色设定要符合drama类型的特点\n- 适合33观看\n- 内容积极向上，传播正能量\n- 具有可操作性，适合视频制作\n\n## 输出格式\n{\n    \"premise\": \"...\",\n    \"synopsis\": \"...\",\n    \"main_conflict\": \"...\",\n    \"resolution\": \"...\",\n    \"character_relationships\": {...},\n    \"main_characters\": [...],\n    \"plot_structure\": {\n        \"act1\": \"...\",\n        \"act2\": \"...\",\n        \"act3\": \"...\"\n    },\n    \"core_values\": \"...\",\n    \"visual_style\": \"...\",\n    \"selling_points\": [...]\n}','ai_openai','{\"model\": \"\", \"temperature\": 0.7, \"character_ids\": [1, 5, 10], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"\"}','draft',0,'[]',NULL,'2025-09-12 06:48:00','2025-09-12 06:48:00'),(8,'HelloWorld','drama','友情','少年',30,'在现代学校的背景下，一个充满好奇心的年轻女孩小雅与电子世界的神秘使者老Ｋ联手，探索友谊的真谛，同时保护电子世界的安全。','小雅是一个充满活力的大学生，梦想成为一名平面设计师。她的好奇心引领她探索数字世界，并偶然结识了神秘的老Ｋ，在一次学校的科技展上，小雅被老Ｋ的技术展示深深吸引。两人迅速成为好友，老Ｋ开始教小雅一些基本的编程知识。\n\n就在两人友谊加深之际，学校的网络系统遭到一次严重的黑客攻击，导致校园生活陷入混乱。小雅和老Ｋ必须联手，利用他们的技能和智慧来解决这个问题。小雅在学习过程中展现出非凡的学习能力，而老Ｋ也意识到这不仅仅是一次技术上的挑战，更是考验他们友谊的机会。\n\n在老Ｋ的指导下，小雅终于发现了黑客的漏洞，并勇敢地面对对手。通过两人的合作，成功地保护了学校的网络安全。\n\n事件过后，小雅更加坚定了自己的职业梦想，而老Ｋ则更加相信人与人之间的真实联系。在欢庆胜利的同时，他们也体会到了友谊的珍贵。','学校的网络系统遭到黑客攻击，危及校园安全，小雅和老Ｋ必须联手解决。','小雅在老Ｋ的指导下，展现了非凡的学习能力。两人合作成功地修复了系统漏洞，保护了校园网络的安全。','[{\"name\": \"小雅\", \"role\": \"大学生，主修艺术设计\", \"description\": \"一个活泼可爱的年轻女孩，充满好奇心和冒险精神\"}, {\"name\": \"老Ｋ\", \"role\": \"技术引领者，数字化奇才\", \"description\": \"电子世界的神秘使者，技术高手，信息的守护者\"}]','{\"小雅\": \"年轻有活力的大学生，梦想成为设计师，与老Ｋ是忘年之交。\", \"老Ｋ\": \"电子世界的神秘使者，技术高手，与小雅建立了深厚的友谊。\"}','现代','学校','','你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据以下信息创作一个完整的故事概要：\n\n## 基本信息\n故事标题：HelloWorld\n类型：drama\n主题：友情\n目标受众：少年\n总时长：30分钟\n## 主要角色\n### 小雅\n描述：一个活泼可爱的年轻女孩，充满好奇心和冒险精神\n背景：小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n### 老Ｋ\n描述：老Ｋ，电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。他的眼神如同星空般深邃，思绪比电流更快。身穿时尚黑色外套，手持闪烁的键盘，仿佛随时能解锁未知的密码。老Ｋ是信息的守护者，技术的引领者，无所不能的数字化奇才。\n背景：在电子世界的边缘，存在着一个神秘的使者，人们称之为老Ｋ。他是信息的守护者，技术的引领者，仿佛是数字世界的主宰。穿着时尚黑色外套的老Ｋ总是手持闪烁的键盘，那键盘上的每一个按键都是他与世界对话的媒介。\n\n起初，老Ｋ只是一个普通的程序员，生活在一个被遗忘的小镇上。但一次偶然的机会，他发现了一本神秘的电子笔记本，里面记载着无数未知的密码与智慧。从那一刻起，老Ｋ的生活发生了翻天覆地的变化。\n\n经过数月的研究与实践，老Ｋ掌握了超越常人的技术，成为了电子世界的传奇人物。他的眼神如同星空般深邃，思绪比电流更快，仿佛是连接着现实与虚拟的桥梁。在他的指引下，电子世界变得更加繁荣与安全。\n\n然而，正当人们认为老Ｋ已经掌握了一切的时候，一场突如其来的黑客攻击危及了整个电子世界的安全。面对这一挑战，老Ｋ毫不犹豫地投身战斗之中。他用自己的智慧和技术，与黑客展开了一场惊心动魄的较量。最终，老Ｋ凭借着无与伦比的能力，保护了电子世界的和平与稳定。\n\n从此以后，老Ｋ成为了电子世界的传说。人们传颂着他的勇气和智慧，他的名字永远镌刻在电子世界的史册之中。身披时尚黑色外套的老Ｋ，继续守护着这个\n\n## 设定信息\n时间背景：现代\n地点设定：学校\n## 创作要求\n## 生成内容\n请创作一个完整的故事概要，以JSON格式返回，包含以下内容：\n\n1. **故事前提** (premise): 故事的核心概念和基础设定\n2. **详细概要** (synopsis): 完整的故事梗概，包含起承转合\n3. **主要冲突** (main_conflict): 故事的核心冲突和矛盾\n4. **解决方案** (resolution): 冲突的解决方式和故事结局\n5. **角色关系** (character_relationships): 主要角色之间的关系网\n6. **主角信息** (main_characters): 重新整理的主要角色信息\n7. **情节结构** (plot_structure): 故事的三幕式结构划分\n8. **核心价值** (core_values): 故事要传达的价值观和意义\n9. **视觉风格** (visual_style): 适合的视觉呈现风格建议\n10. **营销卖点** (selling_points): 故事的亮点和吸引观众的要素\n\n## 创作原则\n- 确保故事结构完整，有明确的开始、发展、高潮和结局\n- 角色设定要符合drama类型的特点\n- 适合少年观看\n- 内容积极向上，传播正能量\n- 具有可操作性，适合视频制作\n\n## 输出格式\n{\n    \"premise\": \"...\",\n    \"synopsis\": \"...\",\n    \"main_conflict\": \"...\",\n    \"resolution\": \"...\",\n    \"character_relationships\": {...},\n    \"main_characters\": [...],\n    \"plot_structure\": {\n        \"act1\": \"...\",\n        \"act2\": \"...\",\n        \"act3\": \"...\"\n    },\n    \"core_values\": \"...\",\n    \"visual_style\": \"...\",\n    \"selling_points\": [...]\n}','ai_openai','{\"model\": \"\", \"temperature\": 0.7, \"character_ids\": [1, 10], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"\"}','draft',0,'[]',NULL,'2025-09-12 06:52:33','2025-09-12 06:52:33');
/*!40000 ALTER TABLE `stories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `story_characters`
--

DROP TABLE IF EXISTS `story_characters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `story_characters` (
  `id` int NOT NULL AUTO_INCREMENT,
  `story_id` int NOT NULL COMMENT '故事ID',
  `virtual_ip_id` int NOT NULL COMMENT '虚拟IP ID',
  `character_name` varchar(100) DEFAULT NULL COMMENT '角色名称',
  `role_type` varchar(50) DEFAULT NULL COMMENT '角色类型：protagonist, antagonist, supporting',
  `importance` int DEFAULT NULL COMMENT '重要度：1-5',
  `personality` text COMMENT '性格特点',
  `background` text COMMENT '背景故事',
  `motivation` text COMMENT '动机',
  `character_arc` text COMMENT '角色发展弧线',
  `relationships` json DEFAULT NULL COMMENT '与其他角色的关系',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `story_id` (`story_id`),
  KEY `virtual_ip_id` (`virtual_ip_id`),
  KEY `ix_story_characters_id` (`id`),
  CONSTRAINT `story_characters_ibfk_1` FOREIGN KEY (`story_id`) REFERENCES `stories` (`id`),
  CONSTRAINT `story_characters_ibfk_2` FOREIGN KEY (`virtual_ip_id`) REFERENCES `virtual_ips` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `story_characters`
--

LOCK TABLES `story_characters` WRITE;
/*!40000 ALTER TABLE `story_characters` DISABLE KEYS */;
INSERT INTO `story_characters` VALUES (1,2,1,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-08-13 17:23:46','2025-08-13 17:23:46'),(2,2,2,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-08-13 17:23:46','2025-08-13 17:23:46'),(3,3,1,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-08-13 17:26:42','2025-08-13 17:26:42'),(4,4,5,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-08-15 03:07:12','2025-08-15 03:07:12'),(5,5,1,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-09-12 05:35:21','2025-09-12 05:35:21'),(6,5,2,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 05:35:21','2025-09-12 05:35:21'),(7,5,10,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 05:35:21','2025-09-12 05:35:21'),(8,6,2,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-09-12 05:53:16','2025-09-12 05:53:16'),(9,6,5,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 05:53:16','2025-09-12 05:53:16'),(10,6,1,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 05:53:16','2025-09-12 05:53:16'),(11,6,10,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 05:53:16','2025-09-12 05:53:16'),(12,7,1,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-09-12 06:48:00','2025-09-12 06:48:00'),(13,7,5,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 06:48:00','2025-09-12 06:48:00'),(14,7,10,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 06:48:00','2025-09-12 06:48:00'),(15,8,1,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-09-12 06:52:33','2025-09-12 06:52:33'),(16,8,10,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-09-12 06:52:33','2025-09-12 06:52:33');
/*!40000 ALTER TABLE `story_characters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` text,
  `task_type` enum('IMAGE_GENERATION','IMAGE_EDIT','IMAGE_ENHANCEMENT') NOT NULL,
  `status` enum('PENDING','PROCESSING','COMPLETED','FAILED') DEFAULT NULL,
  `prompt` text,
  `parameters` text,
  `result_file_path` varchar(512) DEFAULT NULL,
  `error_message` text,
  `user_id` int NOT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `ix_tasks_id` (`id`),
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
INSERT INTO `tasks` VALUES (1,'生成故事 - ３３','异步故事生成','IMAGE_GENERATION','COMPLETED','Story outline: ３３','{\"title\": \"\\uff13\\uff13\", \"genre\": \"drama\", \"theme\": \"\\uff13\\uff13\", \"target_audience\": \"\\uff13\\uff13\", \"duration_minutes\": 30, \"character_ids\": [1, 2, 10], \"setting_time\": \"\", \"setting_location\": \"\", \"world_building\": \"\", \"additional_requirements\": \"\", \"style_preferences\": [], \"content_restrictions\": [], \"model\": \"\", \"temperature\": 0.7, \"tags\": []}','story:5',NULL,1,'2025-09-12 05:35:04','2025-09-12 05:35:21'),(2,'生成故事 - 商锋','异步故事生成','IMAGE_GENERATION','COMPLETED','Story outline: 商锋','{\"title\": \"\\u5546\\u950b\", \"genre\": \"drama\", \"theme\": \"\\u5546\\u4e1a\\uff0c\\u804c\\u573a\", \"target_audience\": \"\\u6210\\u4eba\\uff0c\\u767d\\u9886\", \"duration_minutes\": 30, \"character_ids\": [2, 5, 1, 10], \"setting_time\": \"\\uff12\\uff10\\uff12\\uff15\", \"setting_location\": \"\\u5317\\u4eac\\uff0c\\u4e0a\\u6d77\\uff0c\\u9999\\u6e2f\", \"world_building\": \"\\uff23\\u7aef\\u6e38\\u620f\", \"additional_requirements\": \"\\u4e00\\u6ce2\\u4e09\\u6298\", \"style_preferences\": [], \"content_restrictions\": [], \"model\": \"\", \"temperature\": 0.7, \"tags\": []}','story:6',NULL,1,'2025-09-12 05:53:00','2025-09-12 05:53:16'),(3,'生成故事 - 333','异步故事生成','IMAGE_GENERATION','COMPLETED','Story outline: 333','{\"title\": \"333\", \"genre\": \"drama\", \"theme\": \"333\", \"target_audience\": \"33\", \"duration_minutes\": 30, \"character_ids\": [1, 5, 10], \"setting_time\": \"333\", \"setting_location\": \"13\", \"world_building\": \"32\", \"additional_requirements\": \"\", \"style_preferences\": [], \"content_restrictions\": [], \"model\": \"\", \"temperature\": 0.7, \"tags\": []}','story:7',NULL,1,'2025-09-12 06:47:40','2025-09-12 06:47:59'),(4,'生成故事 - HelloWorld','异步故事生成','IMAGE_GENERATION','COMPLETED','Story outline: HelloWorld','{\"title\": \"HelloWorld\", \"genre\": \"drama\", \"theme\": \"\\u53cb\\u60c5\", \"target_audience\": \"\\u5c11\\u5e74\", \"duration_minutes\": 30, \"character_ids\": [1, 10], \"setting_time\": \"\\u73b0\\u4ee3\", \"setting_location\": \"\\u5b66\\u6821\", \"world_building\": \"\", \"additional_requirements\": \"\", \"style_preferences\": [], \"content_restrictions\": [], \"model\": \"\", \"temperature\": 0.7, \"tags\": []}','story:8',NULL,1,'2025-09-12 06:52:20','2025-09-12 06:52:33'),(5,'生成剧本 - 剧集6','异步剧本生成','IMAGE_GENERATION','COMPLETED','Script for episode 6','{\"episode_id\": 6, \"format_type\": \"screenplay\", \"language\": \"zh-CN\", \"dialogue_style\": \"natural\", \"scene_detail_level\": \"medium\", \"additional_requirements\": \"\", \"style_preferences\": [], \"model\": null, \"temperature\": 0.7}','script:1',NULL,1,'2025-09-12 07:16:13','2025-09-12 07:16:59'),(6,'生成剧本 - 剧集6','异步剧本生成','IMAGE_GENERATION','PROCESSING','Script for episode 6','{\"episode_id\": 6, \"format_type\": \"screenplay\", \"language\": \"zh-CN\", \"dialogue_style\": \"natural\", \"scene_detail_level\": \"detailed\", \"additional_requirements\": \"\", \"style_preferences\": [], \"model\": null, \"temperature\": 0.7}',NULL,NULL,1,'2025-09-24 04:35:51','2025-09-24 04:35:51');
/*!40000 ALTER TABLE `tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_audit_logs`
--

DROP TABLE IF EXISTS `user_audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_audit_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '被操作用户ID',
  `admin_user_id` int DEFAULT NULL COMMENT '操作管理员ID',
  `action` varchar(50) NOT NULL COMMENT '操作类型',
  `old_values` text COMMENT '操作前的值(JSON)',
  `new_values` text COMMENT '操作后的值(JSON)',
  `ip_address` varchar(45) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` varchar(500) DEFAULT NULL COMMENT '用户代理',
  `created_at` datetime DEFAULT (now()) COMMENT '操作时间',
  PRIMARY KEY (`id`),
  KEY `admin_user_id` (`admin_user_id`),
  KEY `user_id` (`user_id`),
  KEY `ix_user_audit_logs_id` (`id`),
  CONSTRAINT `user_audit_logs_ibfk_1` FOREIGN KEY (`admin_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `user_audit_logs_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_audit_logs`
--

LOCK TABLES `user_audit_logs` WRITE;
/*!40000 ALTER TABLE `user_audit_logs` DISABLE KEYS */;
INSERT INTO `user_audit_logs` VALUES (1,2,1,'USER_APPROVED','{\"is_approved\": false, \"is_active\": false, \"approved_at\": null, \"approved_by_user_id\": null}','{\"is_approved\": true, \"is_active\": true, \"approved_at\": \"2025-08-24 08:27:44.429509\", \"approved_by_user_id\": 1, \"reason\": \"\\u81ea\\u52a8\\u5316\\u6d4b\\u8bd5\\u5ba1\\u6279\"}','127.0.0.1','python-requests/2.31.0','2025-08-24 08:27:44'),(2,2,1,'USER_UPDATED','{\"email_verified\": false}','{\"email_verified\": true}','127.0.0.1','python-requests/2.31.0','2025-08-24 08:27:44'),(3,4,1,'ROLE_UPDATED','{\"is_admin\": false, \"is_superuser\": false}','{\"is_admin\": false, \"is_superuser\": false}','127.0.0.1','python-requests/2.31.0','2025-08-24 09:02:30'),(4,4,1,'ROLE_UPDATED','{\"is_admin\": false, \"is_superuser\": false}','{\"is_admin\": false, \"is_superuser\": false}','127.0.0.1','python-requests/2.31.0','2025-08-24 09:03:18'),(5,4,1,'USER_SUSPENDED','{\"is_active\": false, \"account_locked_until\": null}','{\"is_active\": false, \"account_locked_until\": null, \"reason\": null, \"duration_hours\": null}','127.0.0.1','python-requests/2.31.0','2025-08-24 09:04:42'),(6,4,1,'USER_REACTIVATED','{\"is_active\": false, \"account_locked_until\": null, \"failed_login_attempts\": 0}','{\"is_active\": true, \"account_locked_until\": null, \"failed_login_attempts\": 0}','127.0.0.1','python-requests/2.31.0','2025-08-24 09:04:42'),(7,4,1,'USER_SUSPENDED','{\"is_active\": true, \"account_locked_until\": null}','{\"is_active\": false, \"account_locked_until\": null, \"reason\": null, \"duration_hours\": null}','127.0.0.1','python-requests/2.31.0','2025-08-24 09:04:42'),(8,4,1,'USER_APPROVED','{\"is_approved\": false, \"is_active\": false, \"approved_at\": null, \"approved_by_user_id\": null}','{\"is_approved\": true, \"is_active\": true, \"approved_at\": \"2025-08-24 09:12:35.336774\", \"approved_by_user_id\": 1, \"reason\": \"API\\u4fee\\u590d\\u6d4b\\u8bd5 - \\u81ea\\u52a8\\u5ba1\\u6279\"}','127.0.0.1','python-requests/2.31.0','2025-08-24 09:12:35'),(9,3,1,'USER_APPROVED','{\"is_approved\": false, \"is_active\": false, \"approved_at\": null, \"approved_by_user_id\": null}','{\"is_approved\": true, \"is_active\": true, \"approved_at\": \"2025-08-24 09:16:10.844531\", \"approved_by_user_id\": 1, \"reason\": \"\\u8d44\\u6599\\u5b8c\\u6574\\uff0c\\u7b26\\u5408\\u6ce8\\u518c\\u8981\\u6c42\"}','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36','2025-08-24 09:16:10');
/*!40000 ALTER TABLE `user_audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(64) NOT NULL,
  `email` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '0' COMMENT '账户是否激活（默认未激活）',
  `is_superuser` tinyint(1) DEFAULT NULL COMMENT '是否为超级用户',
  `created_at` datetime DEFAULT (now()) COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  `is_admin` tinyint(1) DEFAULT NULL COMMENT '是否为管理员',
  `is_approved` tinyint(1) DEFAULT NULL COMMENT '是否已审批通过',
  `approved_at` datetime DEFAULT NULL COMMENT '审批时间',
  `approved_by_user_id` int DEFAULT NULL COMMENT '审批人ID',
  `email_verified` tinyint(1) DEFAULT NULL COMMENT '邮箱是否已验证',
  `activation_token` varchar(255) DEFAULT NULL COMMENT '激活令牌',
  `activation_token_expires` datetime DEFAULT NULL COMMENT '激活令牌过期时间',
  `last_login_at` datetime DEFAULT NULL COMMENT '最后登录时间',
  `failed_login_attempts` int DEFAULT NULL COMMENT '失败登录次数',
  `account_locked_until` datetime DEFAULT NULL COMMENT '账户锁定到期时间',
  `language` varchar(10) DEFAULT NULL COMMENT '用户语言偏好',
  `timezone` varchar(50) DEFAULT NULL COMMENT '用户时区',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  UNIQUE KEY `ix_users_username` (`username`),
  KEY `ix_users_id` (`id`),
  KEY `fk_users_approved_by_user_id` (`approved_by_user_id`),
  CONSTRAINT `fk_users_approved_by_user_id` FOREIGN KEY (`approved_by_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','admin@ai-video-studio.com','$2b$12$Odq0WQjeTOHTSav6MAZpu.anoBaF3zATFvCFI64n/ApIfq2EjQ1ny','系统管理员',1,1,'2025-08-13 16:49:33','2025-09-24 04:34:54',0,1,NULL,NULL,1,NULL,NULL,'2025-09-24 04:34:54',0,NULL,'zh-CN','Asia/Shanghai'),(2,'testuser123','testuser123@example.com','$2b$12$EIoCOLlIXIWVDoIesW77u.jTuFjnOxoofnwXRE8e/t9L0qBw/fkTi','Test User 123',1,0,'2025-08-24 08:27:43','2025-08-24 08:27:44',0,1,'2025-08-24 08:27:44',1,1,'008400f1-d918-48fa-aa4a-de851540991a','2025-08-25 08:27:44','2025-08-24 08:27:45',0,NULL,'zh-CN','Asia/Shanghai'),(3,'frontend_testuser','frontend_test@example.com','$2b$12$gNQAwu/TtuBeXXyLsrq1OebGRQkhBFIiYQkFuIKGgucMO0Ms43Hp6','Frontend Test User',1,0,'2025-08-24 08:46:11','2025-08-24 09:16:10',0,1,'2025-08-24 09:16:11',1,0,'6da0d152-0a1d-4067-b715-a5edd4820acf','2025-08-25 08:46:12',NULL,0,NULL,'zh-CN','Asia/Shanghai'),(4,'pending_user_test','pending_test@example.com','$2b$12$8jAeWKuSsFU/dRDMV9bnwe4V8JxdOMgDkO.gQubFEwn2EtpatA2NW','Pending Test User',1,0,'2025-08-24 08:57:01','2025-08-24 09:12:35',0,1,'2025-08-24 09:12:35',1,0,'c5d485f2-2d39-4dbf-a239-9172d57475a5','2025-08-25 08:57:02',NULL,0,NULL,'zh-CN','Asia/Shanghai');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `virtual_ip_images`
--

DROP TABLE IF EXISTS `virtual_ip_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `virtual_ip_images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `virtual_ip_id` int NOT NULL,
  `filename` varchar(128) NOT NULL,
  `original_filename` varchar(128) NOT NULL,
  `file_path` varchar(256) NOT NULL,
  `file_size` int NOT NULL,
  `mime_type` varchar(64) NOT NULL,
  `category` varchar(32) NOT NULL,
  `subcategory` varchar(64) DEFAULT NULL,
  `tags` json DEFAULT NULL,
  `prompt` text,
  `ai_model` varchar(64) DEFAULT NULL,
  `generation_params` json DEFAULT NULL,
  `is_default` tinyint(1) DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `oss_url` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `virtual_ip_id` (`virtual_ip_id`),
  KEY `ix_virtual_ip_images_id` (`id`),
  CONSTRAINT `virtual_ip_images_ibfk_1` FOREIGN KEY (`virtual_ip_id`) REFERENCES `virtual_ips` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `virtual_ip_images`
--

LOCK TABLES `virtual_ip_images` WRITE;
/*!40000 ALTER TABLE `virtual_ip_images` DISABLE KEYS */;
INSERT INTO `virtual_ip_images` VALUES (1,1,'9552b9cacf174e3cb43f50d8ceeb3a83.png','小雅_portrait_generated.png','/uploads/9552b9cacf174e3cb43f50d8ceeb3a83.png',1277356,'image/png','portrait',NULL,'[\"realistic\", \"portrait\", \"ai_generated\", \"openai_dalle\"]','A professional realistic portrait portrait of 小雅, 一个活泼可爱的年轻女孩，充满好奇心和冒险精神','dalle-3','{}',0,1,'2025-08-20 10:30:00',NULL),(2,1,'101ebe2eec0d422d83419700a5c88559.png','小雅_portrait_generated.png','/uploads/101ebe2eec0d422d83419700a5c88559.png',929366,'image/png','portrait',NULL,'[\"realistic\", \"portrait\", \"ai_generated\", \"openai_dalle\"]','A professional realistic portrait portrait of 小雅, 一个活泼可爱的年轻女孩，充满好奇心和冒险精神','dalle-3','{}',0,1,'2025-08-20 14:34:37',NULL),(4,10,'456c93d97f6b45fe90c0366262ddac1b.png','老Ｋ_portrait_generated.png','/uploads/456c93d97f6b45fe90c0366262ddac1b.png',1453130,'image/png','portrait',NULL,'[\"realistic\", \"portrait\", \"ai_generated\", \"openai_dalle\"]','A professional realistic portrait portrait of 老Ｋ, 老Ｋ，电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。他的眼神如同星空般深邃，思绪比电流更快。身穿时尚黑色外套，手持闪烁的键盘，仿佛随时能解锁未知的密码。老Ｋ是信息的守护者，技术的引领者，无所不能的数字化奇才。','dalle-3','{}',1,1,'2025-09-12 04:32:42',NULL);
/*!40000 ALTER TABLE `virtual_ip_images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `virtual_ips`
--

DROP TABLE IF EXISTS `virtual_ips`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `virtual_ips` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `description` text,
  `tags` json DEFAULT NULL,
  `background_story` text,
  `style_prompt` text,
  `style_reference_images` json DEFAULT NULL,
  `default_avatar_url` varchar(256) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT NULL,
  `biography` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_virtual_ips_name` (`name`),
  KEY `ix_virtual_ips_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `virtual_ips`
--

LOCK TABLES `virtual_ips` WRITE;
/*!40000 ALTER TABLE `virtual_ips` DISABLE KEYS */;
INSERT INTO `virtual_ips` VALUES (1,'小雅','一个活泼可爱的年轻女孩，充满好奇心和冒险精神','[\"年轻\", \"活泼\", \"女性\", \"现代\"]','小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。','年轻亚洲女性，22岁，长黑发，大眼睛，甜美笑容，现代时尚穿着，充满活力',NULL,NULL,1,1,'2025-08-12 07:46:26',NULL,NULL),(2,'李教授','一位博学的中年教授，温和而富有智慧','[\"中年\", \"教授\", \"男性\", \"知识分子\"]','李教授是一位45岁的大学教授，专门研究人工智能和机器学习。他为人温和，深受学生喜爱，经常在学术会议上发表演讲。他有一个幸福的家庭，业余时间喜欢阅读和园艺。','中年亚洲男性，45岁，戴眼镜，温和表情，学者气质，正装或休闲装',NULL,NULL,1,1,'2025-08-12 07:46:26',NULL,NULL),(3,'奶奶陈','一位慈祥的老奶奶，充满人生智慧','[\"老年\", \"奶奶\", \"女性\", \"慈祥\"]','陈奶奶今年70岁，是一位退休的小学老师。她有三个孙子孙女，非常疼爱他们。她喜欢做饭、织毛衣，经常给邻居的孩子们讲故事。她的人生阅历丰富，总是能给年轻人很好的建议。','亚洲老年女性，70岁，银白头发，慈祥笑容，传统或舒适穿着，温暖气质',NULL,NULL,1,1,'2025-08-12 07:46:26',NULL,NULL),(4,'测试IP','测试描述','[\"测试\"]',NULL,NULL,'[]',NULL,1,1,'2025-08-13 17:02:13',NULL,NULL),(5,'宝宝','一个美丽的中国女子，全世界都喜欢','[\"大女主\"]','',NULL,'[]',NULL,1,0,'2025-08-13 17:14:34',NULL,NULL),(7,'测试角色','这是一个测试角色','[\"测试\", \"角色\"]',NULL,NULL,'[]',NULL,1,0,'2025-08-13 17:16:13',NULL,NULL),(9,'老拐','一个程序员','[\"男\"]','程序员',NULL,'[]',NULL,1,0,'2025-08-24 09:53:29',NULL,NULL),(10,'老Ｋ','老Ｋ，电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。他的眼神如同星空般深邃，思绪比电流更快。身穿时尚黑色外套，手持闪烁的键盘，仿佛随时能解锁未知的密码。老Ｋ是信息的守护者，技术的引领者，无所不能的数字化奇才。','[\"极客\"]','在电子世界的边缘，存在着一个神秘的使者，人们称之为老Ｋ。他是信息的守护者，技术的引领者，仿佛是数字世界的主宰。穿着时尚黑色外套的老Ｋ总是手持闪烁的键盘，那键盘上的每一个按键都是他与世界对话的媒介。\n\n起初，老Ｋ只是一个普通的程序员，生活在一个被遗忘的小镇上。但一次偶然的机会，他发现了一本神秘的电子笔记本，里面记载着无数未知的密码与智慧。从那一刻起，老Ｋ的生活发生了翻天覆地的变化。\n\n经过数月的研究与实践，老Ｋ掌握了超越常人的技术，成为了电子世界的传奇人物。他的眼神如同星空般深邃，思绪比电流更快，仿佛是连接着现实与虚拟的桥梁。在他的指引下，电子世界变得更加繁荣与安全。\n\n然而，正当人们认为老Ｋ已经掌握了一切的时候，一场突如其来的黑客攻击危及了整个电子世界的安全。面对这一挑战，老Ｋ毫不犹豫地投身战斗之中。他用自己的智慧和技术，与黑客展开了一场惊心动魄的较量。最终，老Ｋ凭借着无与伦比的能力，保护了电子世界的和平与稳定。\n\n从此以后，老Ｋ成为了电子世界的传说。人们传颂着他的勇气和智慧，他的名字永远镌刻在电子世界的史册之中。身披时尚黑色外套的老Ｋ，继续守护着这个',NULL,'[]',NULL,1,0,'2025-08-24 11:31:44',NULL,'**外貌特征**：老Ｋ身着一件时尚的黑色外套，搭配一条精致的银色领带。他戴着一副深邃的黑色眼镜，眼神中透露出无尽的智慧。长发披肩，微微随风飘动，仿佛在舞动着数字编码的旋律。\n\n**性格特点**：老Ｋ沉稳且神秘，总是保持着冷静的态度。他的思维敏捷，善于分析问题，解决难题如探囊取物。虽然看似高冷，但内心却充满了对未知世界的好奇和探索欲望。在与他交流时，会感受到一股强大的电子能量，仿佛置身于信息流的海洋之中。\n\n**兴趣爱好**：老Ｋ热爱探索新技术，喜欢研究数字世界的奥秘。他喜欢独自思考，在代码的世界里寻找灵感。除此之外，老Ｋ还喜欢观察星空，对宇宙的未知充满着向往和敬畏。\n\n**特长技能**：老Ｋ是信息安全领域的专家，精通网络安全、密码学等领域。他拥有超凡的编程能力，能够轻松破解复杂的密码和系统。除此之外，老Ｋ还擅长数据分析和人工智能技术，是数字化世界中的一把利剑。\n\n**人际关系**：老Ｋ独来独往，很少与他人交往。但在网络世界中，他拥有许多信任的合作伙伴，他们共同探索着信息的边界，保护着数字世界的安全。老Ｋ的存在如同一座高塔，守护着信息的安全，引领着科技的发展。\n\n**背景经历**：老Ｋ的身世众说纷纭，传言他曾经是某大型科技公司的顶尖工程师，也有人说他是某个神秘组织的核心成员。无论真相如何，老Ｋ的身份始终笼罩在神秘的面纱之下，成为电子世界中的传说。他的一举一动都引起了无数人的关注和猜测，但老Ｋ似乎对这一切视若无睹，继续默默守护着数字的秘密。');
/*!40000 ALTER TABLE `virtual_ips` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'ai_video_studio'
--
--
-- WARNING: can't read the INFORMATION_SCHEMA.libraries table. It's most probably an old server 8.0.32.
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-24 12:36:56
