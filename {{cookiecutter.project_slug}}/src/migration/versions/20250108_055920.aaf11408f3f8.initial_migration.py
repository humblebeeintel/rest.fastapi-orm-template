"""Initial migration.

Revision ID: aaf11408f3f8
Revises: None
Create Date: 2025-01-08 05:59:20.803120+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from alembic import context

from migration import functions
from migration import triggers


# revision identifiers, used by Alembic.
revision: str = "aaf11408f3f8"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    schema_upgrades()
    if context.get_x_argument(as_dictionary=True).get("data", None):
        data_upgrades()

    return


def downgrade() -> None:
    if context.get_x_argument(as_dictionary=True).get("data", None):
        data_downgrades()
    schema_downgrades()

    return


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""

    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "{{cookiecutter.project_abbr}}_table_stat",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("table_name", sa.String(length=64), nullable=False),
        sa.Column(
            "insert_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "delete_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "row_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk__{{cookiecutter.project_abbr}}_table_stat")
        ),
        sa.UniqueConstraint(
            "table_name",
            name=op.f("uq__{{cookiecutter.project_abbr}}_table_stat__table_name"),
        ),
    )
    op.create_index(
        op.f("ix__{{cookiecutter.project_abbr}}_table_stat__created_at"),
        "{{cookiecutter.project_abbr}}_table_stat",
        ["created_at"],
        unique=False,
    )
    op.create_table(
        "{{cookiecutter.project_abbr}}_task",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("point", sa.Integer(), server_default=sa.text("70"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk__{{cookiecutter.project_abbr}}_task")
        ),
    )
    op.create_index(
        op.f("ix__{{cookiecutter.project_abbr}}_task__created_at"),
        "{{cookiecutter.project_abbr}}_task",
        ["created_at"],
        unique=False,
    )
    # ### end Alembic commands ###

    ## Functions
    functions.create_fn_generate_pk()
    functions.create_fn_updated_at()
    functions.create_fn_stat_count(
        table_name="{{cookiecutter.project_abbr}}_table_stat"
    )

    ## Triggers
    _stat_table_names = [
        "{{cookiecutter.project_abbr}}_task",
    ]
    _all_table_names = _stat_table_names + ["{{cookiecutter.project_abbr}}_table_stat"]
    triggers.create_tr_generate_pk(table_names=_all_table_names)
    triggers.create_tr_updated_at(table_names=_all_table_names)
    triggers.create_tr_stat_count(table_names=_all_table_names)

    return


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix__{{cookiecutter.project_abbr}}_task__created_at"),
        table_name="{{cookiecutter.project_abbr}}_task",
    )
    op.drop_table("{{cookiecutter.project_abbr}}_task")
    op.drop_index(
        op.f("ix__{{cookiecutter.project_abbr}}_table_stat__created_at"),
        table_name="{{cookiecutter.project_abbr}}_table_stat",
    )
    op.drop_table("{{cookiecutter.project_abbr}}_table_stat")
    # ### end Alembic commands ###

    ## Drop functions
    functions.drop_fn_all()

    return


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""

    return


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""

    return
