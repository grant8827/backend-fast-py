"""Add dedicated stream provisioning tables

Revision ID: 2025_01_28_0800_stream_provisioning
Revises: 1122a1baa528
Create Date: 2025-01-28 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2025_01_28_0800_stream_provisioning'
down_revision: Union[str, None] = '1122a1baa528'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create shoutcast_servers table
    op.create_table('shoutcast_servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('admin_port', sa.Integer(), nullable=False),
        sa.Column('admin_username', sa.String(100), nullable=False),
        sa.Column('admin_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('max_ports', sa.Integer(), nullable=True, default=100),
        sa.Column('port_range_start', sa.Integer(), nullable=True, default=8100),
        sa.Column('port_range_end', sa.Integer(), nullable=True, default=8200),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shoutcast_servers_id'), 'shoutcast_servers', ['id'], unique=False)

    # Create port_pool table
    op.create_table('port_pool',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('port_number', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('is_allocated', sa.Boolean(), nullable=True, default=False),
        sa.Column('allocated_at', sa.DateTime(), nullable=True),
        sa.Column('allocated_to_stream_id', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['server_id'], ['shoutcast_servers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_port_pool_id'), 'port_pool', ['id'], unique=False)
    op.create_index(op.f('ix_port_pool_port_number'), 'port_pool', ['port_number'], unique=True)
    op.create_index(op.f('ix_port_pool_allocated_to_stream_id'), 'port_pool', ['allocated_to_stream_id'], unique=False)

    # Create dedicated_streams table
    op.create_table('dedicated_streams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stream_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=True),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('source_password', sa.String(255), nullable=False),
        sa.Column('admin_password', sa.String(255), nullable=False),
        sa.Column('stream_title', sa.String(255), nullable=False),
        sa.Column('stream_description', sa.Text(), nullable=True),
        sa.Column('max_listeners', sa.Integer(), nullable=True, default=100),
        sa.Column('bitrate', sa.Integer(), nullable=True, default=128),
        sa.Column('sample_rate', sa.Integer(), nullable=True, default=44100),
        sa.Column('genre', sa.String(100), nullable=True, default='Electronic'),
        sa.Column('status', sa.Enum('provisioning', 'active', 'suspended', 'terminated', 'maintenance', name='streamstatus'), nullable=True, default='provisioning'),
        sa.Column('is_live', sa.Boolean(), nullable=True, default=False),
        sa.Column('current_listeners', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('last_connection', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['server_id'], ['shoutcast_servers.id'], ),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dedicated_streams_id'), 'dedicated_streams', ['id'], unique=False)
    op.create_index(op.f('ix_dedicated_streams_stream_id'), 'dedicated_streams', ['stream_id'], unique=True)
    op.create_index(op.f('ix_dedicated_streams_user_id'), 'dedicated_streams', ['user_id'], unique=False)

    # Create stream_sessions table
    op.create_table('stream_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stream_id', sa.String(50), nullable=False),
        sa.Column('session_start', sa.DateTime(), nullable=False),
        sa.Column('session_end', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('peak_listeners', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_listeners', sa.Float(), nullable=True),
        sa.Column('total_data_mb', sa.Float(), nullable=True, default=0.0),
        sa.Column('encoder_info', sa.JSON(), nullable=True),
        sa.Column('disconnect_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stream_id'], ['dedicated_streams.stream_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stream_sessions_id'), 'stream_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_stream_sessions_stream_id'), 'stream_sessions', ['stream_id'], unique=False)

    # Create stream_monitoring table  
    op.create_table('stream_monitoring',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stream_id', sa.String(50), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('current_listeners', sa.Integer(), nullable=True, default=0),
        sa.Column('is_live', sa.Boolean(), nullable=True, default=False),
        sa.Column('current_bitrate', sa.Integer(), nullable=True),
        sa.Column('bandwidth_mbps', sa.Float(), nullable=True),
        sa.Column('encoder_connected', sa.Boolean(), nullable=True, default=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stream_id'], ['dedicated_streams.stream_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stream_monitoring_id'), 'stream_monitoring', ['id'], unique=False)
    op.create_index(op.f('ix_stream_monitoring_stream_id'), 'stream_monitoring', ['stream_id'], unique=False)
    op.create_index(op.f('ix_stream_monitoring_recorded_at'), 'stream_monitoring', ['recorded_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_index(op.f('ix_stream_monitoring_recorded_at'), table_name='stream_monitoring')
    op.drop_index(op.f('ix_stream_monitoring_stream_id'), table_name='stream_monitoring')
    op.drop_index(op.f('ix_stream_monitoring_id'), table_name='stream_monitoring')
    op.drop_table('stream_monitoring')
    
    op.drop_index(op.f('ix_stream_sessions_stream_id'), table_name='stream_sessions')
    op.drop_index(op.f('ix_stream_sessions_id'), table_name='stream_sessions')
    op.drop_table('stream_sessions')
    
    op.drop_index(op.f('ix_dedicated_streams_user_id'), table_name='dedicated_streams')
    op.drop_index(op.f('ix_dedicated_streams_stream_id'), table_name='dedicated_streams')
    op.drop_index(op.f('ix_dedicated_streams_id'), table_name='dedicated_streams')
    op.drop_table('dedicated_streams')
    
    op.drop_index(op.f('ix_port_pool_allocated_to_stream_id'), table_name='port_pool')
    op.drop_index(op.f('ix_port_pool_port_number'), table_name='port_pool')
    op.drop_index(op.f('ix_port_pool_id'), table_name='port_pool')
    op.drop_table('port_pool')
    
    op.drop_index(op.f('ix_shoutcast_servers_id'), table_name='shoutcast_servers')
    op.drop_table('shoutcast_servers')
    
    # Drop the enum type
    sa.Enum(name='streamstatus').drop(op.get_bind())