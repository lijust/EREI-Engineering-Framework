# Core13 PILOT-B2 — Verified nonroot regression and rollback evidence

**التاريخ:** 8 نوفمبر 2026. **نوع الإثبات:** Source-bound، nonroot، دون Docker أو نموذج AI أو Root.

## Authority

- [B1 owner post-run acceptance #6717103234](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6717103234) — راجعت الموافقة المنشورة من حساب `lijust`، وتتضمن إذنًا صريحًا لـB2 Source-route consolidation وRollback documentation فقط.
- [B0 owner signoff #6713825884](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6713825884).
- Package A [owner close #6713657840](https://github.com/lijust/EREI-3.2/issues/308#issuecomment-6713657840).

## Actual verification

**[GitHub Actions run #42462496198](https://github.com/lijust/EREI-3.2/actions/runs/42462496198)**، Job `128674593035` = **SUCCESS**؛ قرأت الـDecoded Logs:

- `Ran 15 tests ... OK` — مصدر وجرد B0.
- `Ran 26 tests ... OK` — مسار الاستشارة B1 بعد إضافة اختبار B2 المحلي.
- **41/41 PASS**، لا إخفاقات.
- اختبار `test_26_b2_entrypoint_local_call_graph_has_no_legacy_targets` يفحص AST للمصدر المحدد، أسماء الدوال المحلية وحواف استدعائها المتوقعة، وتوصيل `_unique_pairs` إلى `json.loads`، وليس فحصًا شاملاً لكل Entry Point في المستودع.
- Workflow يعمل Nonroot، دون `sudo` أو Docker أو تنفيذ Code مرشح أو تعديل مصدر.
- **المصدر النهائي لـB1 لم يتغير**: `tools/core13_pilot_b1_advisory_only.py` Git blob `8be64b9a1a492e78b97903d95c44fcdea77099ce`.
- اختبار B1 المصدر والـAST بعد إضافة B2: `tests/unit/test_core13_pilot_b1_advisory_only.py` Git blob `a7bdf79de71e3e21feb72bb41c46b685b3f71837`.
- Manifest الـ14 Route: `contracts/core13-pilot-b0-source-route-inventory-v1.json` Git blob `814e7194dc5ebd95557616a68117138ee880da3e`.
- توثيق آلية الوصول والرجوع: `docs/governance/core13-pilot-b2-source-reachability-rollback-20261108-ar.md`.

## B2 source reconciliation and rollback

المسار المسموح **واحد فقط** وهو B1 CLI. تمت المحافظة على J4/J4S/F5 وPRs التاريخية دون تغيير السلوك. كما يبقى الرجوع محددًا: **وقف الاستدعاء** إلى نقطة الدخول في حالة الخطأ؛ طلبا السحب ما زالا Draft وليسا خدمة إنتاجية دائمة. في حال الدمج مستقبلاً، يلزم قرار Git revert منفصل موثق؛ **لم يتم تنفيذ rollback تجريبي مدمر في B2**.

**حدود الاستنتاج:** إثبات عدم وجود استدعاء Legacy في AST للمدخل B1 الحالي، وليس إثباتًا لاستحالة الوصول إلى J4/J4S من أي CLI مستقلة، ولا من أي عملية خارج إطار المستودع. جرد B0 محصور في 14 مصدرًا لأن نتيجة compare العامة حدها 300 ملف.

## Formal status

```text
PACKAGE_A=CLOSED_PASS_SCOPED_READ_ONLY
B0=GATE_PASS
B1=GATE_PASS
B2=SOURCE_RECONCILIATION_AND_ROLLBACK_CI_PASS_OWNER_POST_REVIEW_PENDING
FORMAL_GATES_PASSED=10/16
PACKAGE_B=CLOSED_PASS=false
B3=NOT_STARTED
PACKAGE_C=NOT_STARTED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
```

**الخطوة الوحيدة المتبقية لـB2:** اعتماد صاحب المشروع بعد مراجعة Source SHA وCI والـRollback في [Issue #309](https://github.com/lijust/EREI-3.2/issues/309). عندها فقط يمكن تجهيز B3 لإغلاق Package B؛ لا حاجة لتعديل Docker أو إضافة طبقة تنفيذ جديدة.
