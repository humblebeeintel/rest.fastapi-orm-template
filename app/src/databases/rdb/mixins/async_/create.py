# -*- coding: utf-8 -*-

from typing import Any, Dict, Union, List

from sqlalchemy import Result
from sqlalchemy.orm import DeclarativeBase, declarative_mixin
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import Insert, insert

from src.logger import logger

from .update import AsyncUpdateMixin


@declarative_mixin
class AsyncCreateMixin(AsyncUpdateMixin):
    @classmethod
    async def async_insert(
        cls,
        async_session: AsyncSession,
        orm_way: bool = False,
        auto_commit: bool = True,
        returning: bool = True,
        **kwargs: Dict[str, Any],
    ) -> DeclarativeBase:
        """Insert new data/ORM object into database.

        Args:
            async_session (AsyncSession  , required): SQLAlchemy async_session for database connection.
            orm_way       (bool          , optional): Use ORM way to insert object into database. Defaults to False.
            auto_commit   (bool          , optional): Auto commit. Defaults to True.
            returning     (bool          , optional): Return inserted ORM object from database. Defaults to True.
            **kwargs      (Dict[str, Any], required): Dictionary of object data.

        Raises:
            ValueError    : If no data provided to insert.
            IntegrityError: If object with same ID already exists in database.
            Exception     : If failed to save object into database.

        Returns:
            DeclarativeBase: New ORM object.
        """

        if not kwargs:
            raise ValueError("No data provided to insert!")

        _orm_object: Union[DeclarativeBase, None] = None
        try:
            if orm_way:
                _orm_object = cls(**kwargs)
                async_session.add(_orm_object)

                if auto_commit:
                    await async_session.commit()
                    if returning:
                        await async_session.refresh(_orm_object)
            else:
                if "id" not in kwargs:
                    kwargs["id"] = cls.create_unique_id()

                _stmt: Insert = insert(cls).values(**kwargs)
                if returning:
                    _stmt = _stmt.returning(cls)

                _result: Result = await async_session.execute(_stmt)
                if returning:
                    _orm_object: cls = _result.scalars().one()

                if auto_commit:
                    await async_session.commit()

                if not returning:
                    logger.debug(
                        f"Inserted '{_result.rowcount}' row(s) into '{cls.__name__}' table!"
                    )
        except IntegrityError:
            if auto_commit:
                await async_session.rollback()

            logger.warning(
                f"'{cls.__name__}' '{kwargs['id']}' ID already exists in database!"
            )
            raise
        except Exception:
            if auto_commit:
                await async_session.rollback()

            logger.error(
                f"Failed to save '{cls.__name__}' object '{kwargs['id']}' ID into database!"
            )
            raise

        return _orm_object

    async def async_save(
        self,
        async_session: AsyncSession,
        auto_commit: bool = True,
        returning: bool = False,
        **kwargs: Dict[str, Any],
    ) -> DeclarativeBase:
        """Save ORM object into database.

        Args:
            async_session (AsyncSession  , required): SQLAlchemy async_session for database connection.
            auto_commit   (bool          , optional): Auto commit. Defaults to True.
            **kwargs      (Dict[str, Any], optional): Dictionary of ORM object data.

        Raises:
            Exception: If failed to save object into database.

        Returns:
            DeclarativeBase: Created or updated ORM object.
        """

        try:
            for _key, _val in kwargs.items():
                setattr(self, _key, _val)

            _orm_object: Union[DeclarativeBase, None] = self.__class__.async_get(
                async_session=async_session, id=self.id
            )

            if not _orm_object:
                async_session.add(self)

            if auto_commit:
                await async_session.commit()
                if returning:
                    await async_session.refresh(self)

        except Exception:
            if auto_commit:
                await async_session.rollback()

            logger.error(
                f"Failed to save '{self.__class__.__name__}' object '{self.id}' ID into database!"
            )
            raise

        return self

    @classmethod
    async def async_upsert(
        cls,
        async_session: AsyncSession,
        orm_way: bool = False,
        auto_commit: bool = True,
        returning: bool = True,
        **kwargs: Dict[str, Any],
    ) -> Union[DeclarativeBase, None]:
        """Upsert data into database.

        Args:
            async_session (AsyncSession, required): SQLAlchemy async_session for database connection.
            orm_way     (bool        , optional): Check if object exists in database. Defaults to False.
            auto_commit   (bool        , optional): Auto commit. Defaults to True.
            returning     (bool        , optional): Return upserted ORM object from database. Defaults to True.
            **kwargs      (Dict        , required): Dictionary of object data.

        Raises:
            ValueError: If no data provided to upsert.
            Exception : If failed to upsert object into database.

        Returns:
            Union[DeclarativeBase, None]: Upserted ORM object.
        """

        if not kwargs:
            raise ValueError("No data provided to upsert!")

        _orm_object: Union[cls, None] = None
        try:
            if orm_way:
                if "id" in kwargs:
                    _orm_object: Union[cls, None] = await cls.async_get(
                        async_session=async_session, id=kwargs["id"]
                    )

                if _orm_object:
                    _orm_object: cls = await _orm_object.async_update(
                        async_session=async_session,
                        auto_commit=auto_commit,
                        returning=returning,
                        **kwargs,
                    )
                else:
                    _orm_object: cls = await cls.async_insert(
                        async_session=async_session,
                        orm_way=True,
                        auto_commit=auto_commit,
                        returning=returning,
                        **kwargs,
                    )
            else:
                if "id" not in kwargs:
                    kwargs["id"] = cls.create_unique_id()

                _update_set = {
                    key: value for key, value in kwargs.items() if key != "id"
                }

                # Only for PostgreSQL
                _stmt: Insert = (
                    insert(cls)
                    .values(**kwargs)
                    .on_conflict_do_update(index_elements=["id"], set_=_update_set)
                )
                if returning:
                    _stmt = _stmt.returning(cls)

                _result: Result = await async_session.execute(_stmt)
                if returning:
                    _orm_object: cls = _result.scalars().one()

                if auto_commit:
                    await async_session.commit()

                if not returning:
                    logger.debug(
                        f"Inserted '{_result.rowcount}' row(s) into '{cls.__name__}' table!"
                    )
        except Exception:
            if (not orm_way) and auto_commit:
                await async_session.rollback()

            logger.error(
                f"Failed to upsert '{cls.__name__}' object '{kwargs['id']}' ID into database!"
            )
            raise

        return _orm_object

    @classmethod
    async def async_bulk_insert(
        cls,
        async_session: AsyncSession,
        raw_data: List[Dict[str, Any]],
        auto_commit: bool = True,
        returning: bool = True,
    ) -> List[DeclarativeBase]:
        """Bulk insert data into database.

        Args:
            async_session (AsyncSession        , required): SQLAlchemy async_session for database connection.
            raw_data      (List[Dict[str, Any]], required): List of dictionary object data.
            auto_commit   (bool                , optional): Auto commit. Defaults to True.
            returning     (bool                , optional): Return inserted ORM objects from database. Defaults to True.

        Raises:
            Exception : If failed to bulk insert objects into database.

        Returns:
            List[DeclarativeBase]: List of inserted ORM objects.
        """

        for _data in raw_data:
            if "id" not in _data:
                _data["id"] = cls.create_unique_id()

        _orm_objects: List[cls] = []
        try:
            _stmt: Insert = insert(cls)
            if returning:
                _stmt = _stmt.returning(cls)

            _result: Result = await async_session.execute(_stmt, raw_data)
            if returning:
                _orm_objects: List[cls] = _result.scalars().all()

            if auto_commit:
                await async_session.commit()

            if not returning:
                logger.debug(
                    f"Inserted '{_result.rowcount}' row(s) into '{cls.__name__}' table!"
                )
        except Exception:
            if auto_commit:
                await async_session.rollback()

            logger.error(
                f"Failed to bulk insert '{cls.__name__}' objects into database!"
            )
            raise

        return _orm_objects


__all__ = ["AsyncCreateMixin"]
