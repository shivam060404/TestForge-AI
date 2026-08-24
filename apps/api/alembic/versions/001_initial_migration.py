"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    run_status_enum = sa.Enum('pending', 'running', 'passed', 'failed', 'cancelled', 'healing', name='runstatus')
    run_status_enum.create(op.get_bind())
    
    step_status_enum = sa.Enum('pending', 'running', 'passed', 'failed', 'skipped', 'healing', 'healed', name='stepstatus')
    step_status_enum.create(op.get_bind())
    
    healing_status_enum = sa.Enum('pending', 'approved', 'rejected', 'auto_approved', name='healingstatus')
    healing_status_enum.create(op.get_bind())
    
    accessibility_impact_enum = sa.Enum('critical', 'serious', 'moderate', 'minor', name='accessibilityimpact')
    accessibility_impact_enum.create(op.get_bind())
    
    locator_strategy_enum = sa.Enum('css', 'xpath', 'text', 'role', 'testId', 'id', 'name', 'placeholder', 'label', name='locatorstrategy')
    locator_strategy_enum.create(op.get_bind())
    
    episode_outcome_enum = sa.Enum('success', 'failure', 'partial', name='episodeoutcome')
    episode_outcome_enum.create(op.get_bind())
    
    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_projects_name', 'projects', ['name'])
    
    # Environments table
    op.create_table(
        'environments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('variables', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('headers', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_environments_project_id', 'environments', ['project_id'])
    
    # Test Cases table
    op.create_table(
        'test_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('environment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('environments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('steps', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_test_cases_project_id', 'test_cases', ['project_id'])
    
    # Test Steps table
    op.create_table(
        'test_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('test_case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order', sa.Integer, nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('target', sa.Text, nullable=True),
        sa.Column('locator', sa.Text, nullable=True),
        sa.Column('locator_strategy', sa.String(50), nullable=True),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('options', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('assertion', postgresql.JSONB, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('continue_on_failure', sa.Boolean, nullable=False, server_default='false'),
    )
    op.create_index('ix_test_steps_test_case_id', 'test_steps', ['test_case_id'])
    op.create_index('ix_test_steps_order', 'test_steps', ['test_case_id', 'order'])
    
    # Test Runs table
    op.create_table(
        'test_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('test_case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('environment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('environments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', run_status_enum, nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('total_steps', sa.Integer, nullable=False, server_default='0'),
        sa.Column('passed_steps', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_steps', sa.Integer, nullable=False, server_default='0'),
        sa.Column('skipped_steps', sa.Integer, nullable=False, server_default='0'),
        sa.Column('triggered_by', sa.String(255), nullable=True),
        sa.Column('commit_sha', sa.String(100), nullable=True),
        sa.Column('branch', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_test_runs_project_id', 'test_runs', ['project_id'])
    op.create_index('ix_test_runs_status', 'test_runs', ['status'])
    op.create_index('ix_test_runs_created_at', 'test_runs', ['created_at'])
    
    # Step Executions table
    op.create_table(
        'step_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_steps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order', sa.Integer, nullable=False),
        sa.Column('status', step_status_enum, nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('screenshot_path', sa.Text, nullable=True),
        sa.Column('dom_snapshot_path', sa.Text, nullable=True),
        sa.Column('console_logs', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('network_logs', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('trace_path', sa.Text, nullable=True),
        sa.Column('healed_locator', sa.Text, nullable=True),
        sa.Column('healing_candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('healing_candidates.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_step_executions_run_id', 'step_executions', ['run_id'])
    op.create_index('ix_step_executions_step_id', 'step_executions', ['step_id'])
    op.create_index('ix_step_executions_order', 'step_executions', ['run_id', 'order'])
    
    # Healing Candidates table
    op.create_table(
        'healing_candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('step_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_locator', sa.Text, nullable=False),
        sa.Column('original_strategy', sa.String(50), nullable=False),
        sa.Column('suggested_locator', sa.Text, nullable=False),
        sa.Column('suggested_strategy', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('reasoning', sa.Text, nullable=False),
        sa.Column('status', healing_status_enum, nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', sa.String(255), nullable=True),
    )
    op.create_index('ix_healing_candidates_run_id', 'healing_candidates', ['run_id'])
    op.create_index('ix_healing_candidates_status', 'healing_candidates', ['status'])
    
    # Visual Baselines table
    op.create_table(
        'visual_baselines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('viewport_width', sa.Integer, nullable=False),
        sa.Column('viewport_height', sa.Integer, nullable=False),
        sa.Column('image_path', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_visual_baselines_project_id', 'visual_baselines', ['project_id'])
    
    # Visual Comparisons table
    op.create_table(
        'visual_comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('baseline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('visual_baselines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('step_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match', sa.Boolean, nullable=False),
        sa.Column('difference_percent', sa.Float, nullable=False),
        sa.Column('diff_image_path', sa.Text, nullable=True),
        sa.Column('threshold', sa.Float, nullable=False, server_default='0.1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_visual_comparisons_baseline_id', 'visual_comparisons', ['baseline_id'])
    op.create_index('ix_visual_comparisons_run_id', 'visual_comparisons', ['run_id'])
    
    # Accessibility Issues table
    op.create_table(
        'accessibility_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('step_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('impact', accessibility_impact_enum, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('help', sa.Text, nullable=True),
        sa.Column('html', sa.Text, nullable=True),
        sa.Column('selector', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_accessibility_issues_run_id', 'accessibility_issues', ['run_id'])
    op.create_index('ix_accessibility_issues_impact', 'accessibility_issues', ['impact'])
    
    # Locator Memory table
    op.create_table(
        'locator_memory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selector', sa.Text, nullable=False),
        sa.Column('strategy', locator_strategy_enum, nullable=False),
        sa.Column('page_url', sa.Text, nullable=False),
        sa.Column('element_role', sa.String(100), nullable=True),
        sa.Column('element_text', sa.Text, nullable=True),
        sa.Column('success_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_locator_memory_project_id', 'locator_memory', ['project_id'])
    op.create_index('ix_locator_memory_selector', 'locator_memory', ['project_id', 'selector'])
    
    # Episode Memory table
    op.create_table(
        'episode_memory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('intent', sa.Text, nullable=False),
        sa.Column('steps', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('outcome', episode_outcome_enum, nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('test_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_episode_memory_project_id', 'episode_memory', ['project_id'])
    
    # Failure Patterns table
    op.create_table(
        'failure_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('error_pattern', sa.Text, nullable=False),
        sa.Column('step_action', sa.String(50), nullable=False),
        sa.Column('frequency', sa.Integer, nullable=False, server_default='1'),
        sa.Column('suggested_fix', sa.Text, nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_failure_patterns_project_id', 'failure_patterns', ['project_id'])


def downgrade() -> None:
    op.drop_table('failure_patterns')
    op.drop_table('episode_memory')
    op.drop_table('locator_memory')
    op.drop_table('accessibility_issues')
    op.drop_table('visual_comparisons')
    op.drop_table('visual_baselines')
    op.drop_table('healing_candidates')
    op.drop_table('step_executions')
    op.drop_table('test_runs')
    op.drop_table('test_steps')
    op.drop_table('test_cases')
    op.drop_table('environments')
    op.drop_table('projects')
    
    # Drop enum types
    sa.Enum(name='failure_pattern_enum').drop(op.get_bind())
    sa.Enum(name='episodeoutcome').drop(op.get_bind())
    sa.Enum(name='locatorstrategy').drop(op.get_bind())
    sa.Enum(name='accessibilityimpact').drop(op.get_bind())
    sa.Enum(name='healingstatus').drop(op.get_bind())
    sa.Enum(name='stepstatus').drop(op.get_bind())
    sa.Enum(name='runstatus').drop(op.get_bind())