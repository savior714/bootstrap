## Hand-off Prompt: 샘플 기능 — MVP 보완

### 배경·사용자 의도
샘플 기능 MVP 후속 hardening.

### 권장 작업 순서

1. **제품 정책 확정** (AskQuestion)
2. **스펙 갱신**
3. **API scope 전용 테스트** (TDD)
4. **run_schema_boot** scope 컬럼
5. **관리 UI polish**
6. **진료 UI** (섹션·mock)
7. **목록 SQL 필터**
8. `just lint-turn-end`

### Bounded scope (편집 허용 경로)

```
docs/specs/business/SPEC_biz_sample.md
tests/api/v1/test_sample_scope.py
src/api/v1/sample_router_helpers.py
src/infrastructure/persistence/migrations/run_schema_boot.py
{{FRONTEND_APP_PATH}}/src/app/dashboard/admin/components/SampleManagement.tsx
{{FRONTEND_APP_PATH}}/src/features/consultation/components/SampleGridWidget.tsx
```

Out of scope: 무관 변경.

### Verify (DoD)

```bash
uv run pytest tests/api/v1/test_sample_scope.py -q
just lint-turn-end
```
