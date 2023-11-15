# -*- coding: utf-8 -*-

from typing import List, Dict, Union, Any

from sqlalchemy import update, Update, ChunkedIteratorResult
from sqlalchemy.orm import DeclarativeBase, declarative_mixin
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import logger

from .read import ReadMixin


@declarative_mixin
class UpdateMixin(ReadMixin):
    async def async_update(
        self,
        async_session: AsyncSession,
        auto_commit: bool = True,
        returning: bool = False,
        **kwargs: Dict[str, Any],
    ) -> DeclarativeBase:
        """Update ORM object into database.

        Args:
            async_session (AsyncSession  , required): SQLAlchemy async_session for database connection.
            auto_commit   (bool          , optional): Auto commit. Defaults to True.
            returning     (bool          , optional): Return updated ORM object. Defaults to False.
            **kwargs      (Dict[str, Any], required): Dictionary of update data.

        Raises:
            ValueError: Raise error if no update data provided.

        Returns:
            DeclarativeBase: Updated ORM object.
        """

        if not kwargs:
            raise ValueError("No update data provided!")

        try:
            for _key, _val in kwargs.items():
                if _key == "id":
                    continue
                elif _val is not None:
                    setattr(self, _key, _val)

            if auto_commit:
                await async_session.commit()
                if returning:
                    await async_session.refresh(self)
        except Exception:
            if auto_commit:
                await async_session.rollback()
            logger.error(
                f"Failed to update '{self.__class__.__name__}' object '{self.id}' ID into database!"
            )
            raise

        return self

    @classmethod
    async def async_update_by_id(
        cls,
        async_session: AsyncSession,
        id: str,
        check_exists: bool = False,
        auto_commit: bool = True,
        returning: bool = True,
        **kwargs: Dict[str, Any],
    ) -> DeclarativeBase:
        """Update ORM object into database by ID.

        Args:
            async_session (AsyncSession  , required): SQLAlchemy async_session for database connection.
            id            (str           , required): ID of object.
            check_exists  (bool          , optional): Check if ORM object exists in database. Defaults to False.
            auto_commit   (bool          , optional): Auto commit. Defaults to True.
            returning     (bool          , optional): Return updated ORM object. Defaults to True.
            **kwargs      (Dict[str, Any], required): Dictionary of update data.

        Raises:
            ValueError: Raise error if no update data provided.
            NoResultFound: Raise error if ORM object ID not found in database.

        Returns:
            DeclarativeBase: Updated ORM object.
        """

        if not kwargs:
            raise ValueError("No update data provided!")

        _orm_object: Union[cls, None] = None
        try:
            if check_exists:
                _orm_object: cls = await cls.async_get(
                    async_session=async_session, id=id, allow_no_result=False
                )
                _orm_object: cls = await _orm_object.async_update(
                    async_session=async_session,
                    auto_commit=auto_commit,
                    returning=returning,
                    **kwargs,
                )
            else:
                _stmt: Update = update(cls).where(cls.id == id).values(**kwargs)
                if returning:
                    _stmt = _stmt.returning(cls)
                _result: ChunkedIteratorResult = await async_session.execute(_stmt)
                _orm_object: Union[cls, None] = _result.scalars().one_or_none()
                if auto_commit and _orm_object:
                    await async_session.commit()
                    # await async_session.refresh(_orm_object)
        except NoResultFound:
            raise
        except Exception:
            if auto_commit:
                await async_session.rollback()
            logger.error(
                f"Failed to update '{cls.__name__}' object '{id}' ID into database!"
            )
            raise

        return _orm_object

    @classmethod
    async def async_update_objects(
        cls,
        async_session: AsyncSession,
        orm_objects: List[DeclarativeBase],
        returning: bool = False,
        auto_commit: bool = True,
        **kwargs: Dict[str, Any],
    ) -> List[DeclarativeBase]:
        """Update ORM objects into database.

        Args:
            async_session (AsyncSession         , required): SQLAlchemy async_session for database connection.
            orm_objects   (List[DeclarativeBase], required): List of ORM objects.
            auto_commit   (bool                 , optional): Auto commit. Defaults to True.
            **kwargs      (Dict[str, Any]       , required): Dictionary of update data.

        Raises:
            ValueError: Raise error if no update data provided.

        Returns:
            List[DeclarativeBase]: List of updated ORM objects.
        """

        if not kwargs:
            raise ValueError("No update data provided!")

        try:
            if 0 < len(orm_objects):
                for _orm_object in orm_objects:
                    for _key, _val in kwargs.items():
                        if _key == "id":
                            continue
                        elif _val is not None:
                            setattr(_orm_object, _key, _val)

                if auto_commit:
                    await async_session.commit()
                    if returning:
                        for _orm_object in orm_objects:
                            await async_session.refresh(_orm_object)
        except Exception:
            if auto_commit:
                await async_session.rollback()
            logger.error(f"Failed to update '{cls.__name__}' objects into database!")
            raise

        return orm_objects

    @classmethod
    async def async_update_by_where(
        cls,
        async_session: AsyncSession,
        where: Union[List[Dict[str, Any]], Dict[str, Any]],
        check_exists: bool = True,
        returning: bool = False,
        auto_commit: bool = True,
        **kwargs: Dict[str, Any],
    ) -> List[DeclarativeBase]:
        """Update ORM objects into database by filter conditions.

        Args:
            async_session (AsyncSession              , required): SQLAlchemy async_session for database connection.
            where         (Union[List[Dict[str, Any]],
                                      Dict[str, Any]], required): List of filter conditions.
            auto_commit   (bool                      , optional): Auto commit. Defaults to True.
            **kwargs      (Dict[str, Any]            , required): Dictionary of update data.

        Raises:
            ValueError: Raise error if no update data provided.
            NoResultFound: Raise error if ORM object ID not found in database.

        Returns:
            List[DeclarativeBase]: List of updated ORM objects.
        """

        if not kwargs:
            raise ValueError("No update data provided!")

        _orm_objects: List[cls] = []
        try:
            if check_exists:
                _orm_objects: List[cls] = await cls.async_select_by_where(
                    async_session=async_session, where=where, disable_limit=True
                )

                _orm_objects: List[cls] = await cls.async_update_objects(
                    async_session=async_session,
                    objects=_orm_objects,
                    auto_commit=auto_commit,
                    **kwargs,
                )
            else:
                _stmt: Update = update(cls)
                _stmt = cls._build_where(_stmt, where)
                _stmt = _stmt.values(**kwargs)
                if returning:
                    _stmt = _stmt.returning(cls)
                _result: ChunkedIteratorResult = await async_session.execute(_stmt)
                _orm_objects: List[cls] = _result.scalars().all()
                if auto_commit:
                    await async_session.commit()
        except Exception:
            if auto_commit:
                await async_session.rollback()
            logger.error(
                f"Failed to update '{cls.__name__}' object by '{where}' filter into database!"
            )
            raise

        return _orm_objects

    @classmethod
    async def async_update_all(
        cls,
        async_session: AsyncSession,
        auto_commit: bool = True,
        **kwargs: Dict[str, Any],
    ):
        """Update all current table ORM objects in database.

        Args:
            async_session (AsyncSession  , required): SQLAlchemy async_session for database connection.
            auto_commit   (bool          , optional): Auto commit. Defaults to True.
            **kwargs      (Dict[str, Any], required): Dictionary of update data.

        Raises:
            ValueError: Raise error if no update data provided.
        """

        if not kwargs:
            raise ValueError("No update data provided!")

        try:
            _stmt: Update = update(cls).values(**kwargs)
            await async_session.execute(_stmt)
            if auto_commit:
                await async_session.commit()
        except Exception:
            if auto_commit:
                await async_session.rollback()
            logger.error(f"Failed to update '{cls.__name__}' objects into database!")
            raise


__all__ = ["UpdateMixin"]
