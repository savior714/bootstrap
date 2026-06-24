"""Plan archive paths, aliases, and scan patterns."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_SCRIPT = REPO_ROOT / "scripts" / "archive_plans.py"
PLANS = REPO_ROOT / "docs" / "plans"
ARCHIVE = PLANS / "archive"
LEGACY_PLANS = REPO_ROOT / "docs" / "archive" / "plans"

# docs/plans/<old> 참조 → archive/legacy 내 실제 파일명 (리네임·축약 SSOT)
PLAN_BASENAME_ALIASES: dict[str, str] = {
    "PLAN_desktop_grid_migration.md": (
        "PLAN_consultation_grid_free_placement.md"
    ),
    "20260419_ATOMIC_W2_T2.2_SPEC_TECH_lst_mtls_integration.md": (
        "20260419_ATOMIC_W2_T2.2_lst_mtls_integration.md"
    ),
    "PLAN_TEM08_fhir_viewmodel_mapper_blueprint.md": (
        "20260513_PLAN_TEM08_fhir_viewmodel_mapper_blueprint.md"
    ),
    "PLAN_RISK03_fhir_data_consistency_blueprint.md": (
        "20260515_PLAN_RISK03_fhir_data_consistency_blueprint.md"
    ),
    "PLAN_consistency_open_design_ui_polish_blueprint.md": (
        "20260515_PLAN_consistency_open_design_ui_polish_blueprint.md"
    ),
    "PLAN_fhir_phase8_frontend_bridge_blueprint.md": (
        "PLAN_fhir_master_blueprint.md"
    ),
    "PLAN_linear_label_classification_hardening_blueprint.md": (
        "PLAN_TEM39_error_log_automation_loop_blueprint.md"
    ),
    "PLAN_patient_router_test_fix.md": "PLAN_patient_router_test_fix_blueprint.md",
    "PLAN_renderer_biome_warning_cleanup_blueprint.md": (
        "PLAN_fix_precommit_renderer_biome_blueprint.md"
    ),
    "PLAN_ruff_just_lint_server_debt_blueprint.md": (
        "20260515_PLAN_ruff_just_lint_server_debt_blueprint.md"
    ),
    "PLAN_typescript_error_resolution_blueprint.md": (
        "20260516_PLAN_typescript_error_resolution_blueprint.md"
    ),
    "PLAN_widget_padding_consistency_audit_blueprint.md": (
        "PLAN_widget_design_improvement_followup.md"
    ),
    # 2026-05-21 archive prune — git history retains bodies
    "PLAN_TEM60_error_hub_optimization_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_TEM54_error_hub_optimization_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_TEM54_dod_verification_closure_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_verification_error_resolution.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_minor_clean_up_legacy_remnants.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "20260419_EPIC_week2_domain_interop.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260419_EPIC_week4_certification_final.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260420_FRONTEND_react19_tsc_error_cleanup.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260421_REPLAN_SSOT_guideline_consistency_check.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260425_ELECTRON_DISTRIBUTION_STRATEGY_VERIFICATION.md": (
        "20260425_ELECTRON_DISTRIBUTION_STRATEGY.md"
    ),
    "20260427_IMPROVEMENT_PLAN_AND_PRIORITIES.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260427_long_term_improvement_roadmap.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260427_risk_and_followup_actions.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260428_CERTIFICATION_AND_GUARDRAIL_EXECUTION.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260428_billing_payment_completion.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260501_jsx_casing_codemod_execution_plan.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260502_standardize_hostnames.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260506_billing_rearch_phase4_package_bundle_engine.md": (
        "20260506_billing_rearch_phase5_insurance_adapter.md"
    ),
    "PLAN_20260516_vercel_priority_light_refactor_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_RISK07_ai_log_ml_ops_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_TEM11_workspace_three_pane_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_TEM12_session_header_alert_lane_blueprint.md": (
        "PLAN_TEM12_error_boundary_fallback_blueprint.md"
    ),
    "PLAN_TEM13_kcd_icd10_diagnosis_widget_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_TEM24_hira_master_operational_setup_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_add_consultation_progress_note_images.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_add_error_hub_clear_logs_button.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_add_patient_close_button.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_consultation_diagnosis_hybrid_overhaul.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_consultation_patient_present_privacy_screen.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_consultation_recent_exam_results_widget.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_consultation_vitals_extra_row_sheet.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_fix_consultation_maximum_update_depth.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_fix_dashboard_header_context_hooks_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_fix_error_hub_api_failure_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_increase_image_upload_limit_and_album_lightbox.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_minor_qwen36_ai_log_lora_sft_prep_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_server_layout_hydration_improvement_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_sync_consultation_diagnosis_and_prescription.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_terminology_pre_audit_integration.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_typescript_error_resolution_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_unify_consultation_workspace_grid_layout_part2.md": (
        "PLAN_unify_consultation_workspace_grid_layout_part1.md"
    ),
    "PLAN_widget_design_improvement_followup.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "PLAN_widget_padding_consistency_audit_blueprint.md": (
        "PLAN_TEM50_unified_error_observability_hub_blueprint.md"
    ),
    "public-data-integration-strategy.md": ("PLAN_fhir_master_blueprint.md"),
    "20260411_cert_checklist_f_security_market_compare.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_cert_core_e2e_market_compare.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_cert_f012_csap_grading_research.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_cert_f012_market_compare.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_cert_implementation_priority_tiers_compare.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_dependency_verification_tool.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_int_highway_agent_market_compare.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_int_highway_p0_implementation_blueprint.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260411_krcore_v12_dose_calc_blueprint.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260414_cds_rule_engine_implementation_blueprint.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260416_edge_case_DOC_audit_report.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260416_edge_case_audit_blueprint.md": (
        "PLAN_TEM20_emr_cert_unification_blueprint.md"
    ),
    "20260419_ATOMIC_W2_T4.2_celery_transaction.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260422_BLUEPRINT_e2e_session_bootstrap_v2.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "20260422_BLUEPRINT_valkey_cache_invalidation.md": (
        "20260429_lst_knass_sandbox_integration_plan.md"
    ),
    "PLAN_typeerror_e2e_sequential_integrity_probe_dedup_marker.md": (
        "PLAN_typeerror_e2e_sequential_integrity_probe_draft.md"
    ),
    # Discover Loop 통합·리네임 (2026-05-29 archive)
    "PLAN_DISCOVER_INDEX.md": "PLAN_discover_loop.md",
    "PLAN_DISCOVER_OVERNIGHT.md": "PLAN_discover_loop.md",
    "PLAN_DISCOVER_debt_backlog_pilot.md": "PLAN_discover_loop.md",
    "PLAN_discover_loop_infrastructure.md": "PLAN_discover_loop.md",
}

# check/repair 스캔 제외 (생성물·일회성 스크래치·거대 검증 JSON)
CHECK_SKIP_PATH_PARTS = (
    "agents/brain/",
    "artifacts/verify/",
    "verify-korean-text-result.json",
    "docs/reports/biome/auto-fix-",
    "tests/",
    "docs/reports/context-gaps/",
)

# Blueprint/워크플로 템플릿용 플레이스홀더 — 실제 파일이 아님 (plans-index check 제외)
TEMPLATE_PLAN_PLACEHOLDER_BASENAMES = frozenset(
    {
        "PLAN_xxx.md",
        "PLAN_XYZ.md",
        # discover-emit 산출물 (dead-code-pilot Run 완료 전)
        "PLAN_discover_implement_dead_code_queue.md",
    }
)

# tests/fixtures/plans 등은 제외 — SSOT는 docs/plans·상대 ../plans·루트 /plans 만
PLAN_REF_PATTERN = re.compile(
    r"(?:"
    r"docs/plans/(?!archive/)"
    r"|(?<![\w./-])/plans/(?!archive/)"
    r"|(?:\.\./)+plans/(?!archive/)"
    r")([A-Za-z0-9_.-]+\.md)"
)

# 스캔할 확장자
TEXT_SUFFIXES = {".md", ".mdx", ".mjs", ".js", ".ts", ".tsx", ".py", ".html", ".json", ".yml", ".yaml"}
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".turbo",
}
