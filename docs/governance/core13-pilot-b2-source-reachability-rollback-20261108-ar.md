# Core13 PILOT-B2 — Source Route Reconciliation, Reachability & Rollback

**8 نوفمبر 2026 | المرحلة B2 فقط | أدلة مصدرية ثابتة، دون تنفيذ Docker أو أكواد مرشّح.**

## 1. مرجعية الصلاحية والحالة

- **Package A**: `CLOSED_PASS_SCOPED_READ_ONLY` وفق [موافقة المالك #6713657840](https://github.com/lijust/EREI-3.2/issues/308#issuecomment-6713657840)، و[Docker GET-only حقيقي #42418179869](https://github.com/lijust/EREI-3.2/actions/runs/42418179869). صلاحيات A2 **لا تنتقل إلى B**.
- **B0**: `GATE_PASS` بعد [موافقة المالك #6713825884](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6713825884).
- **B1**: `GATE_PASS` بعد [موافقة المالك اللاحقة للتشغيل #6717103234](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6717103234)، بناءً على [CI #42421025530](https://github.com/lijust/EREI-3.2/actions/runs/42421025530) الذي نجح فيه **40/40**.
- **التقدم الرسمي عند بدء B2**: **10/16** (G0–G3، A0–A3، B0، B1). لا يُعاد فتح الحزمة A أو تنفيذ Root، ولا تُفتح C قبل B3.

**نطاق B2 المأذون:** توفيق مصادر/مسارات Pilot، فحص نطاق الوصول المحلي، الحفاظ على الاختبارات الموجودة، وتوثيق رجوع واضح، **وليس** إعادة بناء Docker Broker أو ترحيل J4/J4S أو اعتماد تنفيذ AI.

## 2. الملفات والتبعيات المستعملة فعليًا

| المسار في الـPilot | Git blob مثبت | الدور |
|---|---|---|
| `tools/core13_pilot_b1_advisory_only.py` | `8be64b9a1a492e78b97903d95c44fcdea77099ce` | **نقطة الدخول الوحيدة**؛ `guardrails` و`inspect_route`، دون Runtime |
| `contracts/core13-pilot-b0-source-route-inventory-v1.json` | `814e7194dc5ebd95557616a68117138ee880da3e` | قائمة 14 Route مغلقة، مع SHA وموانع 7 مسارات تنفيذ/Root |
| `tools/core13_pilot_b0_route_inventory_gate.py` | `2b858f584188ea881fd51caca2cdd6f6ce9fe286` | تحقق مستقل Offline من القائمة والمصادر؛ **ليس import من B1** |
| `tools/core13_pilot_closure_contract_gate.py` | `b382f283fc32b3bb3b17a9c43ca36473804e3973` | عقد الحوكمة التاريخي؛ **ليس import من B1** |
| `tests/unit/test_core13_pilot_b1_advisory_only.py` | مثبت ببصمة Workflow قبل التنفيذ | اختبارات CLI والمدخلات وAST وآلية Source Hash Drift |
| `.github/workflows/core13-pilot-b0-source-route-inventory-hold.yml` | مثبت بالتغييرات ومراجعة PR | CI **Nonroot** فقط |

لا يوجد استيراد مباشر من B1 إلى `core13_j4*` أو `core13_j5*` أو `core13_pilot_a2*`، ولا إلى `docker`، `socket`، `subprocess`، `os`، أو أدوات شبكة. **هذا حكم على شفرة نقطة الدخول هذه في البيئة المعتمدة، وليس حذفًا لكل مسارات التشغيل المستقلة بالمستودع أو إثباتًا لحماية Python خارج نطاقه.**

## 3. الرسم المحدود لمسار الاستدعاء المحلي (Local Static Reachability)

```text
main
 ├── parse_request
 │    └── _require
 │    └── [callback via json.loads: _unique_pairs]
 └── advise
      ├── _require
      └── load_fixed_manifest
           ├── _require
           └── _verified_source
                ├── _require
                └── _git_blob
```

`argparse` و`json` و`hashlib` و`pathlib` و`stat` فقط ضمن استيرادات الملف. `main` يتلقى طلب JSON محدودًا ويعيد JSON؛ `_verified_source` يقرأ فقط Manifest ثابتًا والـ14 ملفًا ذات البصمات المتطابقة. لا يوجد call edge إلى J4/J4S أو Root/Worker أو تنفيذ Shell/Model؛ وكل Route مجهول يُرفض قبل أي فحص مصدر.

**شاهد سلبي مستقل:** مكون `B1` لا يستدعي بوابات Legacy عند عرض تصنيفها. `inspect_route` يعيد مسارًا وبصمته و`DENY_LEGACY_EXECUTION_ROUTE` حيث يلزم، ولا يمرر الطلب إلى الملف المستعرض.

**اختبار إضافي واحد في B2:** `test_26_b2_entrypoint_local_call_graph_has_no_legacy_targets` يشتق أسماء الدوال المحلية و`ast.Call` الفعلية من مصدر B1 ويطابق شبكة الوصول المسموح بها، ويفحص استدعاء `_unique_pairs` عبر `object_pairs_hook`. يعمل مع الاختبارات القديمة؛ لا يوجد مكوّن تنفيذ أو Runtime جديد.

## 4. مصالحة التاريخ والـPRs بدون كسر الأدلة

| الشاهد التاريخي | المعاملة |
|---|---|
| A0–A3 / App Draft PR #312–#314 | محفوظة ومثبتة؛ الاستدلال من Run وSHA فقط؛ لا ترقية إلى تنفيذ أي كود. |
| A0–A3 / Framework Draft PR #172–#174 | محفوظة، ولا يُنشأ بديل أو تُعاد مراجعة سياسة Root في B2. |
| B0/B1 / App Draft [#315](https://github.com/lijust/EREI-3.2/pull/315) | نفس فرع العمل؛ نقطة الدخول واحدة؛ اختبارات الانحدار في Workflow القائمة. |
| B0/B1 / Framework Draft [#175](https://github.com/lijust/EREI-Engineering-Framework/pull/175) | مرآة عقد/أدلة، دون نسخ Runtime جديد إلى Framework. |
| Legacy J4/J4S/F5B1B/F5B1F | **تبقى الملفات كما هي**؛ ليست مرخصة عبر B1، وحذفها أو ترحيلها خارج نطاق B2. |
| `main...Package A` compare | GitHub أعاد أول 300 ملف فقط؛ النتيجة **غير كافية لإثبات اكتمال repository-wide call graph**. |

**التبسيط المعتمد:** لا حذف ولا تعديل لمكونات الاختبار التاريخية؛ لا إنشاء نقطة دخول Pilot ثانية؛ لا نقل تنفيذ J4 إلى Broker جديد. يتم تحسين نظام الوصول المسموح من خلال **المنع داخل المدخل الجديد نفسه** فقط.

## 5. السيناريوهات السلبية وقيود القبول

- تشغيل `guardrails` أو `inspect_route` بـRoute معتمد يعمل كقراءة فقط.
- كل محاولة `execute` / `docker` / `apply_patch` / `code` / `patch` / `url` / `command` أو Route غير مُدرج ترد بـ**Exit Code 2** دون استدعاءات Docker أو Root أو Network أو Model.
- تغيير Git blob للـManifest أو أي من ملفاتها الـ14 يوقف إنتاج التقرير قبل استخدام المصدر غير المعتمد.
- AST يثبت انحصار **الدوال المحلية** لمصدر B1 الحالي، ولا نستخدمه لإثبات عدم وجود External Launcher أو Entry Point آخر.
- النجاح الرسمي لـB2 يحتاج **Source SHA + Run/Job/decoded logs + نتائج الانحدار + توثيق رجوع وقرار المالك بعد المراجعة** وفق عقد v1.

## 6. Rollback محدود وقابل للتحقق

**الهدف عند مشكلة في B1/B2:** إيقاف استخدام مدخل Pilot الاستشاري دون المساس بدليل A أو تشغيل Docker.

1. **قبل أي دمج:** طلبا السحب [App #315](https://github.com/lijust/EREI-3.2/pull/315) و[Framework #175](https://github.com/lijust/EREI-Engineering-Framework/pull/175) ما زالا Draft؛ لا يُدمجان ولا يُروّجان إلى إعدادات نشر. الإجراء الآمن هو **التوقف عن استدعاء** `tools.core13_pilot_b1_advisory_only` والإبقاء على PR معلّقًا/مغلقًا حسب قرار المالك. **لا توجد خدمة مستمرة أو Kill Switch خارجية في هذا الإصدار**؛ إيقاف الاستدعاء هو Rollback التشغيلي المتاح.
2. **عند Source Drift أو مدخل غير معروف:** وظيفة B1 ترفض الطلب أو المصدر (`exit=2`) دون أعمال جانبية. لا يتم تحرير SHA لتجاوز الرفض، بل تُعاد مراجعة المصدر في PR محدد إن كان ذلك ضروريًا.
3. **إذا دُمجت B1 لاحقًا بمراجعة منفصلة:** Rollback بمراجعة Revert Commits/PR رسميًا على مسار Pilot فقط؛ لا تستخدم `git reset --hard` أو حذف سجلات/أدلة التاريخ، ولا تتطلب إعادة فتح Package A. **لم يُنفذ Revert في B2** لأنه لا يوجد تغيير إنتاجي مثبت يحتاج الرجوع الآن.
4. **اختبار تحقق بعد الرجوع:** تأكيد أن أي Launcher/Workflow لا يستدعي CLI كخدمة منشورة، ثم إعادة تشغيل اختبار مصدر B0 وB1 Nonroot وإثبات `stable_ready=false`، `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`، وصفر Docker/Root/Model calls؛ تسجل الأدلة في Issue #309. وجود Legacy J4 CLI مستقل خارج هذا الباب لم يتغير.

## 7. قرار نهاية B2 وحدود B3

```text
B0=GATE_PASS
B1=GATE_PASS
B2=SOURCE_ROUTE_RECONCILED_AND_ROLLBACK_DOCUMENTED_CI_PENDING
B2_FORMAL_OWNER_SIGNOFF=NOT_RECORDED
PACKAGE_B=CLOSED_PASS=false
PACKAGE_C=NOT_STARTED
REPO_WIDE_RUNTIME_ISOLATION=NOT_ESTABLISHED
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```

عند نجاح CI ومراجعة المالك لـB2 فقط، يُنجز B3 **ملخص إغلاق الحزمة B بدون تجارب تنفيذ جديدة**. لا يُسمح ببدء C قبل إغلاق B رسميًا.
