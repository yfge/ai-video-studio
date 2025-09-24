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
INSERT INTO `alembic_version` VALUES ('e5f3948ee82e');
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `episodes`
--

LOCK TABLES `episodes` WRITE;
/*!40000 ALTER TABLE `episodes` DISABLE KEYS */;
INSERT INTO `episodes` VALUES (2,4,1,'新的开始','介绍主要角色和背景设定','[{\"timing\": \"开场\", \"description\": \"角色出场\"}, {\"timing\": \"前10分钟\", \"description\": \"背景介绍\"}, {\"timing\": \"中段\", \"description\": \"冲突铺垫\"}]','{\"protagonist\": \"初始状态展示\"}','[{\"intensity\": \"low\", \"description\": \"内心困扰的初步展现\"}]',30,5,'基于以下故事概要，生成1集的剧集大纲：\n\n故事信息:\n- 标题: 你好啊\n- 类型: drama\n- 主题: 你好\n- 故事概要: 主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。\n- 主要冲突: 主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。\n- 解决方案: 通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。\n\n剧集参数:\n- 总集数: 1集\n- 每集时长: 30分钟\n- 情节复杂度: medium\n- 节奏: medium\n\n主要角色:\n[\n  {\n    \"name\": \"主人公A\",\n    \"role\": \"protagonist\",\n    \"description\": \"积极向上的年轻人\"\n  },\n  {\n    \"name\": \"主人公B\",\n    \"role\": \"supporting\",\n    \"description\": \"智慧可靠的朋友\"\n  }\n]\n\n角色关系:\n{\n  \"group_dynamics\": \"团结互助的友好关系\",\n  \"protagonist_friend\": \"深厚的友谊，相互支持\"\n}\n\n请为每一集生成以下内容:\n1. 集数和标题\n2. 剧集概要 (summary)\n3. 主要情节点 (plot_points)\n4. 角色发展 (character_arcs)\n5. 冲突设置 (conflicts)\n6. 场景数量估计 (scene_count)\n\n要求:\n- 确保整体故事的连贯性和完整性\n- 每集都有明确的开始、发展、高潮和结尾\n- 角色发展要符合整体故事弧线\n- 冲突要逐步升级，最终在适当的集数达到高潮\n- 使用JSON格式返回，包含episodes数组\n\n额外要求: 重新生成第1集的内容','ai_episode_generation','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [], \"additional_requirements\": \"在\"}','draft',NULL,NULL,'2025-08-15 03:07:30','2025-08-15 03:07:56'),(3,1,1,'新的开始','小雅开始她的大学生活，遇到了李教授和一些有趣的同学，同时也开始感受到了学业压力。','[{\"timing\": \"开场\", \"description\": \"小雅入学，认识了李教授和新同学\"}, {\"timing\": \"中场\", \"description\": \"小雅开始感受到学业压力，李教授给予建议\"}, {\"timing\": \"结尾\", \"description\": \"小雅开始思考自己的理想和现实的关系\"}]','{\"小雅\": \"从无忧无虑的新生到开始面临学业压力的大学生\", \"李教授\": \"从小雅的导师到成为小雅的人生导师\"}','[{\"intensity\": \"medium\", \"description\": \"学业压力与个人理想的冲突开始显现\"}]',30,8,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：校园青春物语\n类型：青春\n故事概要：小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。\n主要冲突：学业压力与个人理想的冲突\n\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 特殊要求\n测试剧集生成功能\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n- episode_number: 集数\n- title: 剧集标题 \n- summary: 剧集概要\n- plot_points: 主要情节点列表\n- character_arcs: 角色发展安排\n- conflicts: 本集的冲突设置\n- scene_count: 预估场景数量\n\n示例格式：\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"新的开始\",\n            \"summary\": \"介绍主要角色和背景设定\",\n            \"plot_points\": [{\"description\": \"角色出场\", \"timing\": \"开场\"}],\n            \"character_arcs\": {\"protagonist\": \"初始状态展示\"},\n            \"conflicts\": [{\"description\": \"内心困扰\", \"intensity\": \"low\"}],\n            \"scene_count\": 5\n        }\n    ]\n}\n','ai_fallback','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [\"轻松\", \"有趣\"], \"additional_requirements\": \"测试剧集生成功能\"}','draft',NULL,NULL,'2025-08-20 06:26:03','2025-08-20 06:26:03'),(4,1,2,'探索与挑战','小雅开始在李教授的指导下探索自己的兴趣，并接受了一项挑战。','[{\"timing\": \"开场\", \"description\": \"小雅在李教授的指导下开始探索自己的兴趣\"}, {\"timing\": \"中场\", \"description\": \"小雅接受了一项挑战，开始努力准备\"}, {\"timing\": \"结尾\", \"description\": \"小雅完成挑战，收获成长\"}]','{\"小雅\": \"从被动应对学业压力到积极探索自我兴趣和接受挑战\", \"李教授\": \"从给予小雅建议到积极指导小雅的学习\"}','[{\"intensity\": \"medium\", \"description\": \"小雅面对挑战时的压力和不安\"}]',30,8,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：校园青春物语\n类型：青春\n故事概要：小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。\n主要冲突：学业压力与个人理想的冲突\n\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 特殊要求\n测试剧集生成功能\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n- episode_number: 集数\n- title: 剧集标题 \n- summary: 剧集概要\n- plot_points: 主要情节点列表\n- character_arcs: 角色发展安排\n- conflicts: 本集的冲突设置\n- scene_count: 预估场景数量\n\n示例格式：\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"新的开始\",\n            \"summary\": \"介绍主要角色和背景设定\",\n            \"plot_points\": [{\"description\": \"角色出场\", \"timing\": \"开场\"}],\n            \"character_arcs\": {\"protagonist\": \"初始状态展示\"},\n            \"conflicts\": [{\"description\": \"内心困扰\", \"intensity\": \"low\"}],\n            \"scene_count\": 5\n        }\n    ]\n}\n','ai_fallback','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [\"轻松\", \"有趣\"], \"additional_requirements\": \"测试剧集生成功能\"}','draft',NULL,NULL,'2025-08-20 06:26:03','2025-08-20 06:26:03'),(5,1,3,'成长与智慧','小雅在奶奶陈的故事中找到了对生活的新理解，成功应对了学业和个人理想的冲突。','[{\"timing\": \"开场\", \"description\": \"小雅听奶奶陈的故事，对生活有了新的理解\"}, {\"timing\": \"中场\", \"description\": \"小雅将新理解应用到学习和生活中，收获成长\"}, {\"timing\": \"结尾\", \"description\": \"小雅成功应对学业和个人理想的冲突，感悟到人生智慧\"}]','{\"小雅\": \"从面临挑战的焦虑到找到解决问题的智慧和勇气\", \"奶奶陈\": \"从小雅的长辈到小雅的人生导师\"}','[{\"intensity\": \"medium\", \"description\": \"小雅如何将新理解应用到学业和个人理想的冲突中\"}]',30,8,'你是一个专业的剧集编剧，擅长将故事概要分解为具体的剧集内容。请基于以下故事信息生成3集的剧集大纲：\n\n## 故事信息\n故事标题：校园青春物语\n类型：青春\n故事概要：小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。\n主要冲突：学业压力与个人理想的冲突\n\n## 剧集参数\n总集数：3集\n每集时长：30分钟\n情节复杂度：medium\n节奏控制：medium\n\n## 特殊要求\n测试剧集生成功能\n\n## 输出格式\n请以JSON格式返回，包含episodes数组，每集包含：\n- episode_number: 集数\n- title: 剧集标题 \n- summary: 剧集概要\n- plot_points: 主要情节点列表\n- character_arcs: 角色发展安排\n- conflicts: 本集的冲突设置\n- scene_count: 预估场景数量\n\n示例格式：\n{\n    \"episodes\": [\n        {\n            \"episode_number\": 1,\n            \"title\": \"新的开始\",\n            \"summary\": \"介绍主要角色和背景设定\",\n            \"plot_points\": [{\"description\": \"角色出场\", \"timing\": \"开场\"}],\n            \"character_arcs\": {\"protagonist\": \"初始状态展示\"},\n            \"conflicts\": [{\"description\": \"内心困扰\", \"intensity\": \"low\"}],\n            \"scene_count\": 5\n        }\n    ]\n}\n','ai_fallback','{\"pacing\": \"medium\", \"plot_complexity\": \"medium\", \"focus_characters\": [], \"style_preferences\": [\"轻松\", \"有趣\"], \"additional_requirements\": \"测试剧集生成功能\"}','draft',NULL,NULL,'2025-08-20 06:26:03','2025-08-20 06:26:03');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scripts`
--

LOCK TABLES `scripts` WRITE;
/*!40000 ALTER TABLE `scripts` DISABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stories`
--

LOCK TABLES `stories` WRITE;
/*!40000 ALTER TABLE `stories` DISABLE KEYS */;
INSERT INTO `stories` VALUES (1,'校园青春物语','青春','成长与友谊','年轻人',15,'讲述大学生活中的青春故事','小雅在大学里遇到了各种有趣的人和事，在李教授的指导下成长，同时也从奶奶陈那里学到了人生智慧。','学业压力与个人理想的冲突','通过努力和身边人的帮助，找到了平衡点',NULL,NULL,'现代','大学校园','现实主义风格的校园环境',NULL,NULL,NULL,'draft',1,'[\"校园\", \"青春\", \"成长\"]',NULL,'2025-08-12 07:46:26','2025-08-12 07:46:26'),(2,'测试故事','drama','友情','年轻人',30,'这是一个关于友情与成长的现代都市故事。','主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。','主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。','通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。','[{\"name\": \"主人公A\", \"role\": \"protagonist\", \"description\": \"积极向上的年轻人\"}, {\"name\": \"主人公B\", \"role\": \"supporting\", \"description\": \"智慧可靠的朋友\"}]','{\"group_dynamics\": \"团结互助的友好关系\", \"protagonist_friend\": \"深厚的友谊，相互支持\"}','现代','城市','现实世界','请为以下短剧创作一个完整的故事概要：\n\n标题: 测试故事\n类型: drama\n主题: 友情\n目标受众: 年轻人\n总时长: 30分钟\n\n主要角色:\n- 小雅: 一个活泼可爱的年轻女孩，充满好奇心和冒险精神 背景: 小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n- 李教授: 一位博学的中年教授，温和而富有智慧 背景: 李教授是一位45岁的大学教授，专门研究人工智能和机器学习。他为人温和，深受学生喜爱，经常在学术会议上发表演讲。他有一个幸福的家庭，业余时间喜欢阅读和园艺。\n\n设定:\n- 时间: 现代\n- 地点: 城市\n- 世界观: 现实世界\n\n请生成包含以下内容的故事概要:\n1. 故事前提 (premise)\n2. 详细概要 (synopsis)\n3. 主要冲突 (main_conflict)\n4. 解决方案 (resolution)\n5. 角色关系 (character_relationships)\n6. 主要角色信息 (main_characters)\n\n格式要求:\n- 使用JSON格式返回\n- 内容要符合drama类型的特点\n- 适合年轻人观看\n- 故事要有完整的起承转合结构\n\n额外要求: 积极向上','ai_story_generation','{\"character_ids\": [1, 2], \"style_preferences\": null, \"content_restrictions\": null, \"additional_requirements\": \"积极向上\"}','draft',0,'[\"测试\"]',NULL,'2025-08-13 17:23:46','2025-08-13 17:23:46'),(3,'为什么爱我是川普？','romance','霸总，美女，中国，古风','五十岁以下的红脖子',30,'这是一个关于友情与成长的现代都市故事。','主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。','主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。','通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。','[{\"name\": \"主人公A\", \"role\": \"protagonist\", \"description\": \"积极向上的年轻人\"}, {\"name\": \"主人公B\", \"role\": \"supporting\", \"description\": \"智慧可靠的朋友\"}]','{\"group_dynamics\": \"团结互助的友好关系\", \"protagonist_friend\": \"深厚的友谊，相互支持\"}','未来一年','华盛顿','中国龙牛逼，中国红傻逼','请为以下短剧创作一个完整的故事概要：\n\n标题: 为什么爱我是川普？\n类型: romance\n主题: 霸总，美女，中国，古风\n目标受众: 五十岁以下的红脖子\n总时长: 30分钟\n\n主要角色:\n- 小雅: 一个活泼可爱的年轻女孩，充满好奇心和冒险精神 背景: 小雅是一个22岁的大学生，主修艺术设计。她性格开朗，喜欢探索新事物，经常在社交媒体上分享她的日常生活和创作。她梦想成为一名知名的平面设计师。\n\n设定:\n- 时间: 未来一年\n- 地点: 华盛顿\n- 世界观: 中国龙牛逼，中国红傻逼\n\n请生成包含以下内容的故事概要:\n1. 故事前提 (premise)\n2. 详细概要 (synopsis)\n3. 主要冲突 (main_conflict)\n4. 解决方案 (resolution)\n5. 角色关系 (character_relationships)\n6. 主要角色信息 (main_characters)\n\n格式要求:\n- 使用JSON格式返回\n- 内容要符合romance类型的特点\n- 适合五十岁以下的红脖子观看\n- 故事要有完整的起承转合结构\n\n额外要求: 我永远是最美的','ai_story_generation','{\"character_ids\": [1], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"我永远是最美的\"}','draft',0,'[]',NULL,'2025-08-13 17:26:42','2025-08-13 17:26:42'),(4,'你好啊','drama','你好','你好',30,'这是一个关于友情与成长的现代都市故事。','主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。','主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。','通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。','[{\"name\": \"主人公A\", \"role\": \"protagonist\", \"description\": \"积极向上的年轻人\"}, {\"name\": \"主人公B\", \"role\": \"supporting\", \"description\": \"智慧可靠的朋友\"}]','{\"group_dynamics\": \"团结互助的友好关系\", \"protagonist_friend\": \"深厚的友谊，相互支持\"}','','','','请为以下短剧创作一个完整的故事概要：\n\n标题: 你好啊\n类型: drama\n主题: 你好\n目标受众: 你好\n总时长: 30分钟\n\n主要角色:\n- 宝宝: 一个美丽的中国女子，全世界都喜欢\n\n设定:\n- 时间: 现代\n- 地点: 待定\n- 世界观: 现实世界\n\n请生成包含以下内容的故事概要:\n1. 故事前提 (premise)\n2. 详细概要 (synopsis)\n3. 主要冲突 (main_conflict)\n4. 解决方案 (resolution)\n5. 角色关系 (character_relationships)\n6. 主要角色信息 (main_characters)\n\n格式要求:\n- 使用JSON格式返回\n- 内容要符合drama类型的特点\n- 适合你好观看\n- 故事要有完整的起承转合结构','ai_story_generation','{\"character_ids\": [5], \"style_preferences\": [], \"content_restrictions\": [], \"additional_requirements\": \"\"}','draft',0,'[]',NULL,'2025-08-15 03:07:12','2025-08-15 03:07:12');
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `story_characters`
--

LOCK TABLES `story_characters` WRITE;
/*!40000 ALTER TABLE `story_characters` DISABLE KEYS */;
INSERT INTO `story_characters` VALUES (1,2,1,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-08-13 17:23:46','2025-08-13 17:23:46'),(2,2,2,NULL,'supporting',3,NULL,NULL,NULL,NULL,NULL,'2025-08-13 17:23:46','2025-08-13 17:23:46'),(3,3,1,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-08-13 17:26:42','2025-08-13 17:26:42'),(4,4,5,NULL,'protagonist',5,NULL,NULL,NULL,NULL,NULL,'2025-08-15 03:07:12','2025-08-15 03:07:12');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
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
INSERT INTO `users` VALUES (1,'admin','admin@ai-video-studio.com','$2b$12$Odq0WQjeTOHTSav6MAZpu.anoBaF3zATFvCFI64n/ApIfq2EjQ1ny','系统管理员',1,1,'2025-08-13 16:49:33','2025-08-24 12:06:30',0,1,NULL,NULL,1,NULL,NULL,'2025-08-24 12:06:31',0,NULL,'zh-CN','Asia/Shanghai'),(2,'testuser123','testuser123@example.com','$2b$12$EIoCOLlIXIWVDoIesW77u.jTuFjnOxoofnwXRE8e/t9L0qBw/fkTi','Test User 123',1,0,'2025-08-24 08:27:43','2025-08-24 08:27:44',0,1,'2025-08-24 08:27:44',1,1,'008400f1-d918-48fa-aa4a-de851540991a','2025-08-25 08:27:44','2025-08-24 08:27:45',0,NULL,'zh-CN','Asia/Shanghai'),(3,'frontend_testuser','frontend_test@example.com','$2b$12$gNQAwu/TtuBeXXyLsrq1OebGRQkhBFIiYQkFuIKGgucMO0Ms43Hp6','Frontend Test User',1,0,'2025-08-24 08:46:11','2025-08-24 09:16:10',0,1,'2025-08-24 09:16:11',1,0,'6da0d152-0a1d-4067-b715-a5edd4820acf','2025-08-25 08:46:12',NULL,0,NULL,'zh-CN','Asia/Shanghai'),(4,'pending_user_test','pending_test@example.com','$2b$12$8jAeWKuSsFU/dRDMV9bnwe4V8JxdOMgDkO.gQubFEwn2EtpatA2NW','Pending Test User',1,0,'2025-08-24 08:57:01','2025-08-24 09:12:35',0,1,'2025-08-24 09:12:35',1,0,'c5d485f2-2d39-4dbf-a239-9172d57475a5','2025-08-25 08:57:02',NULL,0,NULL,'zh-CN','Asia/Shanghai');
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
  PRIMARY KEY (`id`),
  KEY `virtual_ip_id` (`virtual_ip_id`),
  KEY `ix_virtual_ip_images_id` (`id`),
  CONSTRAINT `virtual_ip_images_ibfk_1` FOREIGN KEY (`virtual_ip_id`) REFERENCES `virtual_ips` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `virtual_ip_images`
--

LOCK TABLES `virtual_ip_images` WRITE;
/*!40000 ALTER TABLE `virtual_ip_images` DISABLE KEYS */;
INSERT INTO `virtual_ip_images` VALUES (1,1,'9552b9cacf174e3cb43f50d8ceeb3a83.png','小雅_portrait_generated.png','/uploads/9552b9cacf174e3cb43f50d8ceeb3a83.png',1277356,'image/png','portrait',NULL,'[\"realistic\", \"portrait\", \"ai_generated\", \"openai_dalle\"]','A professional realistic portrait portrait of 小雅, 一个活泼可爱的年轻女孩，充满好奇心和冒险精神','dalle-3','{}',0,1,'2025-08-20 10:30:00'),(2,1,'101ebe2eec0d422d83419700a5c88559.png','小雅_portrait_generated.png','/uploads/101ebe2eec0d422d83419700a5c88559.png',929366,'image/png','portrait',NULL,'[\"realistic\", \"portrait\", \"ai_generated\", \"openai_dalle\"]','A professional realistic portrait portrait of 小雅, 一个活泼可爱的年轻女孩，充满好奇心和冒险精神','dalle-3','{}',0,1,'2025-08-20 14:34:37'),(3,10,'47de21707487470ebe535d0ab62f4485.png','老Ｋ_portrait_generated.png','/uploads/47de21707487470ebe535d0ab62f4485.png',1787655,'image/png','portrait',NULL,'[\"realistic\", \"portrait\", \"ai_generated\", \"openai_dalle\"]','A professional realistic portrait portrait of 老Ｋ, 老Ｋ，电子世界的神秘使者，披着未知的面纱，携带着无尽的智慧。他的眼神如同星空般深邃，思绪比电流更快。身穿时尚黑色外套，手持闪烁的键盘，仿佛随时能解锁未知的密码。老Ｋ是信息的守护者，技术的引领者，无所不能的数字化奇才。','dalle-3','{}',0,1,'2025-08-24 12:07:27');
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

-- Dump completed on 2025-08-25 10:01:33
