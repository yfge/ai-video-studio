#!/usr/bin/env python3
"""
数据迁移脚本：将数据库中的 base64 图片数据上传到 OSS 并更新为 URL

此脚本扫描以下表中可能包含 base64 图片数据的字段：
- scripts.extra_metadata (JSON) - storyboard 中的 *_original 字段
- stories.extra_metadata (JSON)
- episodes.extra_metadata (JSON)
- scenes.metadata (JSON)
- shots.metadata (JSON)
- virtual_ip_images.file_path / oss_url
- images.file_path
- tasks.result_file_path
- virtual_ips.style_reference_images (JSON)
- environments.reference_images (JSON)

Usage:
    python scripts/migrate_base64_to_oss.py [--dry-run] [--table TABLE_NAME] [--batch-size N]

Options:
    --dry-run       只扫描不修改数据
    --table         只处理指定的表
    --batch-size    每批处理的记录数（默认 100）
"""

import argparse
import asyncio
import base64
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Base64ToOSSMigrator:
    """Base64 图片数据迁移器"""

    def __init__(self, dry_run: bool = False, batch_size: int = 100):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.engine = create_engine(settings.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.oss_service = None
        self.stats = {
            "scanned": 0,
            "base64_found": 0,
            "converted": 0,
            "failed": 0,
            "skipped": 0,
        }

    async def init_oss_service(self):
        """初始化 OSS 服务"""
        from app.services.storage.oss_service import oss_service

        if not oss_service:
            raise RuntimeError("OSS 服务未配置，请检查环境变量")
        self.oss_service = oss_service
        logger.info("OSS 服务初始化成功")

    def is_base64_image(self, value: str) -> bool:
        """检查字符串是否是 base64 图片格式"""
        if not isinstance(value, str):
            return False
        return value.startswith("data:image")

    async def convert_base64_to_oss(
        self, base64_data: str, prefix: str = "migrated"
    ) -> Optional[str]:
        """将 base64 图片上传到 OSS 并返回 URL"""
        if not self.is_base64_image(base64_data):
            return None

        try:
            # 解析 base64 数据
            # 格式: data:image/png;base64,iVBORw0KGgo...
            header, b64_data = base64_data.split(",", 1)
            mime_part = header.split(";")[0]  # "data:image/png"
            mime_type = mime_part.split(":")[1] if ":" in mime_part else "image/png"
            ext = mime_type.split("/")[1] if "/" in mime_type else "png"

            # 解码 base64
            image_bytes = base64.b64decode(b64_data)

            if self.dry_run:
                logger.info(f"[DRY-RUN] 将上传 {len(image_bytes)} 字节的图片到 OSS")
                return f"https://oss.example.com/{prefix}/migrated.{ext}"

            # 上传到 OSS
            upload_result = await self.oss_service.upload_file_content(
                file_content=image_bytes,
                filename=f"migrated.{ext}",
                file_type="image",
                prefix=prefix,
            )

            if upload_result.get("success"):
                oss_url = upload_result.get("file_url")
                logger.info(f"上传成功: {len(image_bytes)} 字节 -> {oss_url}")
                return oss_url
            else:
                logger.error(f"上传失败: {upload_result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"转换 base64 到 OSS 失败: {e}")
            return None

    async def migrate_string_field(
        self,
        table_name: str,
        id_column: str,
        field_name: str,
        prefix: str,
    ) -> Tuple[int, int, int]:
        """迁移字符串字段中的 base64 数据"""
        found = 0
        converted = 0
        failed = 0

        with self.Session() as session:
            # 查询可能包含 base64 的记录
            query = text(
                f"SELECT {id_column}, {field_name} FROM {table_name} "
                f"WHERE {field_name} LIKE 'data:image%' "
                f"LIMIT :limit"
            )
            results = session.execute(query, {"limit": self.batch_size}).fetchall()

            for row in results:
                record_id = row[0]
                field_value = row[1]
                found += 1
                self.stats["base64_found"] += 1

                if not self.is_base64_image(field_value):
                    continue

                oss_url = await self.convert_base64_to_oss(field_value, prefix)

                if oss_url:
                    if not self.dry_run:
                        update_query = text(
                            f"UPDATE {table_name} SET {field_name} = :url "
                            f"WHERE {id_column} = :id"
                        )
                        session.execute(update_query, {"url": oss_url, "id": record_id})
                        session.commit()
                    converted += 1
                    self.stats["converted"] += 1
                    logger.info(f"[{table_name}] ID={record_id}: 已转换 {field_name}")
                else:
                    failed += 1
                    self.stats["failed"] += 1
                    logger.warning(
                        f"[{table_name}] ID={record_id}: 转换失败 {field_name}"
                    )

        return found, converted, failed

    async def migrate_json_field(
        self,
        table_name: str,
        id_column: str,
        field_name: str,
        prefix: str,
    ) -> Tuple[int, int, int]:
        """迁移 JSON 字段中的 base64 数据（仅处理简单列表）"""
        found = 0
        converted = 0
        failed = 0

        with self.Session() as session:
            # 查询所有非空的 JSON 字段
            query = text(
                f"SELECT {id_column}, {field_name} FROM {table_name} "
                f"WHERE {field_name} IS NOT NULL "
                f"LIMIT :limit"
            )
            results = session.execute(query, {"limit": self.batch_size}).fetchall()

            for row in results:
                record_id = row[0]
                json_value = row[1]
                self.stats["scanned"] += 1

                if not json_value:
                    continue

                # 解析 JSON
                try:
                    if isinstance(json_value, str):
                        data = json.loads(json_value)
                    else:
                        data = json_value
                except json.JSONDecodeError:
                    continue

                # 检查是否是列表且包含 base64
                if not isinstance(data, list):
                    continue

                has_base64 = any(
                    self.is_base64_image(item) for item in data if isinstance(item, str)
                )
                if not has_base64:
                    continue

                found += 1
                self.stats["base64_found"] += 1

                # 转换列表中的 base64
                new_data = []
                all_converted = True

                for item in data:
                    if isinstance(item, str) and self.is_base64_image(item):
                        oss_url = await self.convert_base64_to_oss(item, prefix)
                        if oss_url:
                            new_data.append(oss_url)
                        else:
                            new_data.append(item)  # 保留原始数据
                            all_converted = False
                    else:
                        new_data.append(item)

                if all_converted:
                    if not self.dry_run:
                        update_query = text(
                            f"UPDATE {table_name} SET {field_name} = :data "
                            f"WHERE {id_column} = :id"
                        )
                        session.execute(
                            update_query,
                            {"data": json.dumps(new_data), "id": record_id},
                        )
                        session.commit()
                    converted += 1
                    self.stats["converted"] += 1
                    logger.info(
                        f"[{table_name}] ID={record_id}: 已转换 {field_name} 中的图片"
                    )
                else:
                    failed += 1
                    self.stats["failed"] += 1

        return found, converted, failed

    def _count_base64_in_json(self, data: Any) -> int:
        """递归统计 JSON 中的 base64 图片数量"""
        count = 0
        if isinstance(data, str):
            if self.is_base64_image(data):
                count += 1
        elif isinstance(data, list):
            for item in data:
                count += self._count_base64_in_json(item)
        elif isinstance(data, dict):
            for value in data.values():
                count += self._count_base64_in_json(value)
        return count

    async def _convert_base64_in_json(
        self, data: Any, prefix: str
    ) -> Tuple[Any, int, int]:
        """
        递归转换 JSON 中的所有 base64 图片为 OSS URL

        Returns:
            (converted_data, success_count, fail_count)
        """
        success = 0
        fail = 0

        if isinstance(data, str):
            if self.is_base64_image(data):
                oss_url = await self.convert_base64_to_oss(data, prefix)
                if oss_url:
                    return oss_url, 1, 0
                else:
                    return data, 0, 1
            return data, 0, 0

        elif isinstance(data, list):
            new_list = []
            for item in data:
                new_item, s, f = await self._convert_base64_in_json(item, prefix)
                new_list.append(new_item)
                success += s
                fail += f
            return new_list, success, fail

        elif isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_value, s, f = await self._convert_base64_in_json(value, prefix)
                new_dict[key] = new_value
                success += s
                fail += f
            return new_dict, success, fail

        else:
            return data, 0, 0

    async def migrate_nested_json_field(
        self,
        table_name: str,
        id_column: str,
        field_name: str,
        prefix: str,
    ) -> Tuple[int, int, int]:
        """迁移嵌套 JSON 字段中的 base64 数据（递归处理）"""
        found = 0
        converted = 0
        failed = 0

        with self.Session() as session:
            # 查询包含 base64 的记录
            query = text(
                f"SELECT {id_column}, {field_name} FROM {table_name} "
                f"WHERE {field_name} LIKE '%data:image%' "
                f"LIMIT :limit"
            )
            results = session.execute(query, {"limit": self.batch_size}).fetchall()

            for row in results:
                record_id = row[0]
                json_value = row[1]
                self.stats["scanned"] += 1

                if not json_value:
                    continue

                # 解析 JSON
                try:
                    if isinstance(json_value, str):
                        data = json.loads(json_value)
                    else:
                        data = json_value
                except json.JSONDecodeError:
                    continue

                # 统计 base64 数量
                base64_count = self._count_base64_in_json(data)
                if base64_count == 0:
                    continue

                found += 1
                self.stats["base64_found"] += base64_count
                logger.info(
                    f"[{table_name}] ID={record_id}: 发现 {base64_count} 个 base64 图片"
                )

                # 递归转换
                new_data, success, fail = await self._convert_base64_in_json(
                    data, prefix
                )

                if success > 0:
                    if not self.dry_run:
                        update_query = text(
                            f"UPDATE {table_name} SET {field_name} = :data "
                            f"WHERE {id_column} = :id"
                        )
                        session.execute(
                            update_query,
                            {
                                "data": json.dumps(new_data, ensure_ascii=False),
                                "id": record_id,
                            },
                        )
                        session.commit()
                    converted += success
                    self.stats["converted"] += success
                    logger.info(
                        f"[{table_name}] ID={record_id}: 成功转换 {success} 个图片"
                    )

                if fail > 0:
                    failed += fail
                    self.stats["failed"] += fail
                    logger.warning(
                        f"[{table_name}] ID={record_id}: {fail} 个图片转换失败"
                    )

        return found, converted, failed

    async def migrate_table(self, table_name: str) -> Dict[str, int]:
        """迁移指定表"""
        logger.info(f"开始处理表: {table_name}")
        results = {"found": 0, "converted": 0, "failed": 0}

        if table_name == "virtual_ip_images":
            # file_path 字段
            f, c, fa = await self.migrate_string_field(
                "virtual_ip_images", "id", "file_path", "migrated/virtual-ip-images"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

            # oss_url 字段
            f, c, fa = await self.migrate_string_field(
                "virtual_ip_images", "id", "oss_url", "migrated/virtual-ip-images"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "images":
            f, c, fa = await self.migrate_string_field(
                "images", "id", "file_path", "migrated/images"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "tasks":
            f, c, fa = await self.migrate_string_field(
                "tasks", "id", "result_file_path", "migrated/tasks"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "virtual_ips":
            f, c, fa = await self.migrate_json_field(
                "virtual_ips",
                "id",
                "style_reference_images",
                "migrated/virtual-ip-refs",
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "environments":
            f, c, fa = await self.migrate_json_field(
                "environments", "id", "reference_images", "migrated/environment-refs"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "scripts":
            # extra_metadata 是嵌套 JSON，包含 storyboard.frames[].image_url_original 等
            f, c, fa = await self.migrate_nested_json_field(
                "scripts", "id", "extra_metadata", "migrated/scripts-storyboard"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "stories":
            f, c, fa = await self.migrate_nested_json_field(
                "stories", "id", "extra_metadata", "migrated/stories"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "episodes":
            f, c, fa = await self.migrate_nested_json_field(
                "episodes", "id", "extra_metadata", "migrated/episodes"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "scenes":
            f, c, fa = await self.migrate_nested_json_field(
                "scenes", "id", "metadata", "migrated/scenes"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        elif table_name == "shots":
            f, c, fa = await self.migrate_nested_json_field(
                "shots", "id", "metadata", "migrated/shots"
            )
            results["found"] += f
            results["converted"] += c
            results["failed"] += fa

        else:
            logger.warning(f"未知的表: {table_name}")

        return results

    async def run(self, tables: Optional[List[str]] = None):
        """运行迁移"""
        await self.init_oss_service()

        all_tables = [
            "scripts",  # 最重要，包含 storyboard 的 base64 数据
            "stories",
            "episodes",
            "scenes",
            "shots",
            "virtual_ip_images",
            "images",
            "tasks",
            "virtual_ips",
            "environments",
        ]

        if tables:
            all_tables = [t for t in all_tables if t in tables]

        logger.info(f"{'[DRY-RUN] ' if self.dry_run else ''}开始迁移 base64 数据")
        logger.info(f"处理表: {', '.join(all_tables)}")
        logger.info(f"批次大小: {self.batch_size}")

        for table in all_tables:
            try:
                await self.migrate_table(table)
            except Exception as e:
                logger.error(f"处理表 {table} 失败: {e}")

        # 打印统计
        logger.info("=" * 50)
        logger.info("迁移统计:")
        logger.info(f"  扫描记录数: {self.stats['scanned']}")
        logger.info(f"  发现 base64: {self.stats['base64_found']}")
        logger.info(f"  成功转换: {self.stats['converted']}")
        logger.info(f"  转换失败: {self.stats['failed']}")
        logger.info(f"  跳过: {self.stats['skipped']}")
        if self.dry_run:
            logger.info("(DRY-RUN 模式，未实际修改数据)")


def main():
    parser = argparse.ArgumentParser(
        description="将数据库中的 base64 图片数据迁移到 OSS"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只扫描不修改数据",
    )
    parser.add_argument(
        "--table",
        type=str,
        action="append",
        help="只处理指定的表（可多次指定）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="每批处理的记录数（默认 100）",
    )

    args = parser.parse_args()

    migrator = Base64ToOSSMigrator(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )

    asyncio.run(migrator.run(tables=args.table))


if __name__ == "__main__":
    main()
