from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time
from pydantic import ValidationError
from src.app.core.config import settings
from src.app.core.schemas.global_value_objects import DateTimeValue, EntityUUID, LogicalDeletionMixin, TimestampedMixin
from src.utils.logger import get_logger

logger = get_logger(__name__)
PREDETERMINED_TIME: str = '2023-01-01 12:00:00'


@pytest.fixture
def expected_time():
    with freeze_time(PREDETERMINED_TIME):
        utc_time = datetime(2023, 1, 1, 12, 0, 0)
        return utc_time + timedelta(seconds=settings.DIFFERENCE_TIMESTAMP_JST)


class TestDateTimeValue:
    def test_creation(self):
        """DateTimeValueが正しく作成できることを検証"""
        now = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        date_value = DateTimeValue(value=now)
        assert date_value.value == now

    def test_immutability(self):
        """DateTimeValueが不変であることを検証"""
        now = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        date_value = DateTimeValue(value=now)

        with pytest.raises(ValidationError):
            date_value.value = datetime.now(tz=ZoneInfo('Asia/Tokyo'))

    def test_equality(self):
        """同じ値を持つDateTimeValueが等価であることを検証"""
        now = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        date_value1 = DateTimeValue(value=now)
        date_value2 = DateTimeValue(value=now)
        assert date_value1 == date_value2
        assert hash(date_value1) == hash(date_value2)

    def test_inequality_different_value(self):
        """異なる値を持つDateTimeValueが等価でないことを検証"""
        date_value1 = DateTimeValue(value=datetime(2023, 1, 1, tzinfo=ZoneInfo('Asia/Tokyo')))
        date_value2 = DateTimeValue(value=datetime(2023, 1, 2, tzinfo=ZoneInfo('Asia/Tokyo')))
        assert date_value1 != date_value2
        assert hash(date_value1) != hash(date_value2)

    def test_inequality_different_type(self):
        """異なる型とDateTimeValueが等価でないことを検証"""
        now = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
        date_value = DateTimeValue(value=now)
        assert date_value != now
        assert date_value != 'not a date'

    def test_serialization(self):
        """DateTimeValueが正しくシリアライズされることを検証"""
        dt = datetime(2023, 3, 15, 12, 30, 45, tzinfo=ZoneInfo('Asia/Tokyo'))
        date_value = DateTimeValue(value=dt)
        serialized = date_value.model_dump_json()
        assert '"value":"2023-03-15T12:30:45+09:00"' in serialized


class TestEntityUUID:
    def test_creation_with_uuid(self):
        """指定したUUIDでEntityUUIDが正しく作成できることを検証"""
        specific_uuid = uuid4()
        entity_id = EntityUUID(value=specific_uuid)
        assert entity_id.value == specific_uuid

    def test_generate_new_id(self):
        """新しいEntityUUIDが生成できることを検証"""
        entity_id = EntityUUID.generate()
        assert isinstance(entity_id, EntityUUID)
        assert isinstance(entity_id.value, UUID)

    def test_equality(self):
        """同じUUIDを持つEntityUUIDが等価であることを検証"""
        specific_uuid = uuid4()
        entity_id1 = EntityUUID(value=specific_uuid)
        entity_id2 = EntityUUID(value=specific_uuid)
        assert entity_id1 == entity_id2
        assert hash(entity_id1) == hash(entity_id2)

    def test_inequality_different_value(self):
        """異なるUUIDを持つEntityUUIDが等価でないことを検証"""
        entity_id1 = EntityUUID(value=uuid4())
        entity_id2 = EntityUUID(value=uuid4())
        assert entity_id1 != entity_id2
        assert hash(entity_id1) != hash(entity_id2)

    def test_inequality_different_type(self):
        """異なる型とEntityUUIDが等価でないことを検証"""
        entity_id = EntityUUID(value=uuid4())
        assert entity_id != 'not an entity id'
        assert entity_id != entity_id.value  # UUIDそのものとも等価ではない

    def test_string_representation(self):
        """EntityUUIDの文字列表現が正しいことを検証"""
        specific_uuid = uuid4()
        entity_id = EntityUUID(value=specific_uuid)
        assert str(entity_id) == str(specific_uuid)

    def test_immutability(self):
        """EntityUUIDが不変であることを検証"""
        entity_id = EntityUUID(value=uuid4())

        with pytest.raises(ValidationError):
            entity_id.value = uuid4()


# TimestampedMixinのテスト用クラス
class TimestampedEntity(TimestampedMixin):
    name: str


class TestTimestampedMixin:
    def test_default_creation(self, fixed_time):
        """TimestampedMixinが正しくcreated_atを設定することを検証"""
        entity = TimestampedEntity(name='Test Entity')
        logger.info(f'fixed_time: {fixed_time.replace(microsecond=0)}')
        logger.info(f'created_at: {entity.created_at.replace(microsecond=0, tzinfo=None)}')

        assert entity.created_at.replace(microsecond=0, tzinfo=None) == fixed_time.replace(microsecond=0)
        assert entity.updated_at is None

    def test_update_timestamp(self, fixed_time):
        """update_timestampが正しく動作することを検証"""
        entity = TimestampedEntity(name='Test Entity')
        # 1時間進める
        with freeze_time(timedelta(hours=1)):
            entity.update_timestamp()
        expected_update_time = fixed_time + timedelta(hours=1)
        logger.info(f'expected_update_time: {expected_update_time}')
        logger.info(f'updated_at: {entity.updated_at}')
        assert entity.updated_at.replace(microsecond=0, tzinfo=None) == expected_update_time.replace(microsecond=0)

    def test_serialization(self):
        """日付のシリアライズが正しく動作することを検証"""
        created_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=ZoneInfo('Asia/Tokyo'))
        updated_time = datetime(2023, 1, 2, 13, 0, 0, tzinfo=ZoneInfo('Asia/Tokyo'))

        entity = TimestampedEntity(name='Test Entity', created_at=created_time, updated_at=updated_time)

        serialized = entity.model_dump_json()
        assert '"created_at":"2023-01-01T12:00:00+09:00"' in serialized
        assert '"updated_at":"2023-01-02T13:00:00+09:00"' in serialized

        # updatedがNoneの場合
        entity = TimestampedEntity(name='Test Entity', created_at=created_time)
        serialized = entity.model_dump_json()
        assert '"updated_at":null' in serialized


# LogicalDeletionMixinのテスト用クラス
class DeletableEntity(LogicalDeletionMixin):
    name: str


class TestLogicalDeletionMixin:
    def test_default_state(self):
        """LogicalDeletionMixinのデフォルト状態を検証"""
        entity = DeletableEntity(name='Test Entity')
        assert entity.is_deleted is False
        assert entity.deleted_at is None

    def test_mark_as_deleted(self, fixed_time):
        """mark_as_deleted動作を検証"""
        entity = DeletableEntity(name='Test Entity')

        entity.mark_as_deleted()

        assert entity.is_deleted is True
        assert entity.deleted_at.replace(microsecond=0, tzinfo=None) == fixed_time.replace(microsecond=0)

    def test_restore(self):
        """restore動作を検証"""
        entity = DeletableEntity(name='Test Entity')
        entity.mark_as_deleted()

        entity.restore()

        assert entity.is_deleted is False
        assert entity.deleted_at is None

    def test_idempotency(self):
        """論理削除と復元の冪等性を検証"""
        # 同じ操作を複数回実行しても状態が一度だけ変更されることを確認
        entity = DeletableEntity(name='Test Entity')

        # 削除の冪等性
        entity.mark_as_deleted()
        first_deleted_at = entity.deleted_at

        entity.mark_as_deleted()  # 2回目の削除
        assert entity.deleted_at == first_deleted_at  # 削除日時が変わらない

        # 復元の冪等性
        entity.restore()
        assert entity.is_deleted is False
        assert entity.deleted_at is None

        entity.restore()  # 2回目の復元
        assert entity.is_deleted is False
        assert entity.deleted_at is None

    def test_serialization(self):
        """削除日時のシリアライズが正しく動作することを検証"""
        entity = DeletableEntity(name='Test Entity')

        with freeze_time('2023-01-01 12:00:00'):
            entity.mark_as_deleted()

        serialized = entity.model_dump_json()
        assert '"deleted_at":"2023-01-01T21:00:00+09:00"' in serialized
        assert '"is_deleted":true' in serialized

        # 復元後
        entity.restore()
        serialized = entity.model_dump_json()
        assert '"deleted_at":null' in serialized
        assert '"is_deleted":false' in serialized


# 両方のミックスインを組み合わせたテスト
class CompleteEntity(TimestampedMixin, LogicalDeletionMixin):
    name: str


class TestCombinedMixins:
    def test_combined_functionality(self, fixed_time):
        """TimestampedMixinとLogicalDeletionMixinの組み合わせを検証"""
        entity = CompleteEntity(name='Combined Entity')

        # 初期状態
        assert entity.is_deleted is False
        assert entity.deleted_at is None

        # 削除と更新日時
        with freeze_time(timedelta(hours=1)):
            entity.mark_as_deleted()
            entity.update_timestamp()

        expected_time = fixed_time + timedelta(hours=1)
        assert entity.is_deleted is True
        assert entity.deleted_at.replace(microsecond=0, tzinfo=None) == expected_time.replace(microsecond=0)
        assert entity.updated_at.replace(microsecond=0, tzinfo=None) == expected_time.replace(microsecond=0)

        # 復元と更新日時
        with freeze_time(timedelta(hours=2)):
            entity.restore()
            entity.update_timestamp()

        expected_time = fixed_time + timedelta(hours=2)
        assert entity.is_deleted is False
        assert entity.deleted_at is None
        assert entity.updated_at.replace(microsecond=0, tzinfo=None) == expected_time.replace(microsecond=0)
