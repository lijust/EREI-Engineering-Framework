# Core13 PILOT-B3 — حزمة مراجعة وإغلاق B (Sc​​oped Advisory Only)

**التاريخ: 8 نوفمبر 2026 | القرار المقترح: B_PILOT_ROUTE_CONSOLIDATED_SCOPED_PASS | الإغلاق الرسمي: بانتظار توقيع المالك بعد المراجعة.**

## 1. الهدف ومعيار الإغلاق

هذه **حزمة B3 النهائية**، وليست مشروعًا جديدًا. وفق العقد المجمد `contracts/core13-pilot-closure-v1.json`، تتطلب B3 مقارنة واضحة بين المسارات القديمة والجديدة، أدلة الاختبارات المسموحة والرفض، سجل حدود الثقة، وآلية Rollback، ثم اعتماد المالك بنتيجة **`B_PILOT_ROUTE_CONSOLIDATED`** مع قيد نطاق دقيق. **لا تنشئ B3 أي Runtime أو مصدر تنفيذ جديد.**

أجاز المالك العمل في B3 فقط ضمن [موافقة B2 #6719235856](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6719235856). المالك ليس قد اعتمد **B3 بعد**؛ موافقة B2 تصريح بتجهيز حزمة المراجعة، لا شهادة إغلاق الحزمة B.

## 2. تتبع الأدلة والتوقيعات الرسمية

| المعيار | سجل الدليل | الحالة |
|---|---|---|
| Package A | [Owner #6713657840](https://github.com/lijust/EREI-3.2/issues/308#issuecomment-6713657840)، [A2 Root GET #42418179869](https://github.com/lijust/EREI-3.2/actions/runs/42418179869) | `CLOSED_PASS_SCOPED_READ_ONLY` |
| B0 — جرد المصادر | [Owner #6713825884](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6713825884)، [CI #42420217755](https://github.com/lijust/EREI-3.2/actions/runs/42420217755) | GATE_PASS: 14 مصدرًا مثبتًا، 15 اختبارًا |
| B1 — مدخل واحد | [Owner #6717103234](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6717103234)، [CI #42421025530](https://github.com/lijust/EREI-3.2/actions/runs/42421025530) | GATE_PASS: 40/40 إجمالًا |
| B2 — مسار الوصول والرجوع | [Owner #6719235856](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6719235856)، [CI #42462598131](https://github.com/lijust/EREI-3.2/actions/runs/42462598131) | GATE_PASS: 41/41 إجمالًا |
| B3 — مراجعة الحزمة | **هذا المستند** + سجل تقدم متطابق بين المستودعين | PACKET_READY؛ owner signoff PENDING |

**إجمالي البوابات المغلقة رسميًا قبل B3: 11/16.** البوابات: G0–G3 (4)، A0–A3 (4)، B0–B2 (3). لا يُحتسب B3 تلقائيًا نتيجة نجاح GitHub Actions.

## 3. Old → New: مسارات التنفيذ قبل/بعد الحزمة B

| المسار القديم | مخاطر المصدر القديم المثبتة | السلوك المسموح من مدخل B1 الجديد | القرار |
|---|---|---|---|
| J4 المباشر | أوامر host CLI: `docker create`، `start --attach`، `rm --force` | `inspect_route` يصف المسار ويرجع `DENY_LEGACY_EXECUTION_ROUTE`؛ لا يستدعي J4 | **DENY من Pilot** |
| J4S Streaming | يستخدم `subprocess.Popen` لتنفيذ `docker start --attach` ويرتبط بـJ4 | تقرير ثابت المصدر دون Import أو استدعاء J4S | **DENY من Pilot** |
| D3B2A host broker | يمكنه تشغيل subprocess ثابتة على المضيف | B1 لا يستورده ولا يمرر له أوامر | **DENY من Pilot** |
| F5B1B Root Broker | يحتوي على مسار Docker HTTP POST ثابت | خارج الاستيرادات والعمليات المسموحة | **DENY من Pilot** |
| F5B1F Owner CREATE | تجربة مملوكة للمالك لإنشاء حاوية ثابتة | خارج مدخل B1 | **DENY من Pilot** |
| A2 Root Read-only | تجربة Docker ثانوي حقيقي بصلاحيات Root تحت موافقة يدوية | أدلتها محفوظة، لكن **لم تُعد استخدامها** كخدمة B | **DENY من Pilot** |
| A2 workflow | Workflow منفصلة لإجراء Owner-manual | ليست قابلة للاستدعاء من مدخل B1 | **DENY من Pilot** |
| Typed model / IPC fixture / source gates / consolidation CI | أدوات مراجعة أو تجارب تاريخية لا تثبت تنفيذًا مستقلاً آمنًا | `inspect_route` يرجع تقريرًا فقط؛ لا Import إلى الأدوات | **REFERENCE_ONLY** |
| Route غير معروفة | لا توجد هوية مثبتة أو Source SHA | رفض كلي دون تنفيذ أو قراءة مسار يحدده المستخدم | **DENY (default)** |
| **B1 الجديدة** | مصدر جديد واحد فقط مخصص للمراجعة | `guardrails` أو `inspect_route` على **14 معرفًا مثبتًا**، ومدخل JSON محدود | **ALLOW READ-ONLY ADVISORY** |

> **تنبيه دقيق:** هذا الجدول يبين التغيير في **المسار الذي يبدأ من B1 فقط**؛ ملفات J4/J4S/F5 وغيرها ما زالت موجودة وقد تُشغل من أدوات مستقلة خارج B1. لا ندعي حظرًا عامًا على جميع مداخل المستودع.

## 4. دليل التنفيذ السلبي والإيجابي وحدود الاستنتاج

**المصدر المعتمد دون تغيير خلال B2:**
- `tools/core13_pilot_b1_advisory_only.py` Git blob **`8be64b9a1a492e78b97903d95c44fcdea77099ce`**.
- `contracts/core13-pilot-b0-source-route-inventory-v1.json` Git blob **`814e7194dc5ebd95557616a68117138ee880da3e`**.
- `tools/core13_pilot_b0_route_inventory_gate.py` Git blob **`2b858f584188ea881fd51caca2cdd6f6ce9fe286`**.
- `tests/unit/test_core13_pilot_b1_advisory_only.py` Git blob **`a7bdf79de71e3e21feb72bb41c46b685b3f71837`**.
- آخر اختبار CI معتمد: [#42462598131](https://github.com/lijust/EREI-3.2/actions/runs/42462598131)، Job `128674904528`: **B0 15/15 + B1/B2 26/26 = 41/41 PASS**، Nonroot، دون Docker/Root/Network/Model/Patch.

**Positive:** تشغيل CLI الحقيقي بحالتَي `guardrails` و`inspect_route`، وقراءة Manifest والـ14 Blob المتطابقة، وإرجاع Report حتمي لا ينفذ شيئًا.

**Negative:** رفض `execute` و`docker` و`run` و`apply_patch` و`model` وحقول code/patch/command/url، وJSON مكرر/معطوب/متجاوز الحد، ومعرفات Route غير معتمدة أو Source SHA متغيرة. اختبار B2 إضافي يتحقق من حواف الاستدعاء المحلية للدوال باستخدام AST؛ لا يوجد Import لعمليات تنفيذ قديمة من نقطة الدخول. هذه فحوص **Source وCLI**، وليست عزلًا تشغيليًا عالميًا أو أدلة على ذكاء نموذج.

## 5. حل مشكلة التكرار وأثرها الفعلي

لم نُنفذ ترحيل J4 أو J4S إلى Broker جديد، ولم نُضف جهة Root، ولم ننشئ مسار Pilot ثانيًا. **التوحيد الفعلي هنا توحيد واجهة الدخول المسموحة إلى واجهة واحدة غير تنفيذية، مع بقاء الأكواد التاريخية لأغراض الأدلة.**

لا تدّعي B3 إزالة جميع Duplicate modules أو تخفيض عدد الشيفرات في المستودع بالكامل؛ لا يوجد مثل هذا الدليل، وليس مطلوبًا لإغلاق Pilot الاستشاري محدود النطاق.

## 6. خطة Rollback وقيود الإنتاج

الفرعان في [App Draft #315](https://github.com/lijust/EREI-3.2/pull/315) و[Framework Draft #175](https://github.com/lijust/EREI-Engineering-Framework/pull/175) **غير مدمجين عند إعداد الحزمة**؛ لا توجد خدمة B1 إنتاجية مستمرة. الإجراء المتاح عند الخطر هو **التوقف عن استدعاء CLI** مع إبقاء `DENY` هو الافتراضي. إذا دُمجت لاحقًا فيتم Revert معتمد ومسجل للـPR/Commits، لا حذف أدلة أو `git reset --hard`. لم يجر تنفيذ Revert لعدم وجود تغيير إنتاجي يستدعيه.

هذا Rollback **لا يوقف تشغيل CLI القديمة إذا استدعاها شخص خارج B1**؛ لا يوجد حاجز حصرية عامة، ونحافظ على الشفافية بهذا القيد.

## 7. معايير قرار B3 وإغلاق Package B

| شرط الإغلاق | شاهد | قرار المراجعة |
|---|---|---|
| B0/B1/B2 وقّعها المالك | تعليقات #6713825884 / #6717103234 / #6719235856 | **PASS** |
| جدول Old/New يغطي المسارات الـ14 وفق ما نعرفه | Manifest B0 + هذا المستند | **PASS (نطاقي)** |
| مدخل واحد `B1` غير تنفيذي | Source SHA وAST/CLI | **PASS (نطاقي)** |
| CI Positive + Negative + SHA | Run #42462598131، 41/41 | **PASS** |
| Rollback وإثبات أنه غير منشور | تقرير B2 + Draft PRs | **PASS (موثق، غير منفّذ)** |
| بيان مخاطر عدم اكتمال repo-wide isolation | مدون صراحة | **PASS (قيد معترف به)** |
| توقيع المالك النهائي على B3 وحزمة B | **لم يُسجل** | **PENDING** |

**التوصية:** اعتماد `B3=GATE_PASS` و`Package B=CLOSED_PASS_SCOPED_ADVISORY_ONLY` بعد مراجعة المالك لهذا التقرير، **دون** إعلان العزل العام أو فتح صلاحيات Runtime. يمكن بعدها فقط فتح C0 لتسجيل سيناريوهات الاستشارة الثلاثة مسبقًا، وليس تشغيل نموذج أو كود دون عقد C.

```text
B0=GATE_PASS
B1=GATE_PASS
B2=GATE_PASS
B3=PACKET_READY_OWNER_SIGNOFF_PENDING
PACKAGE_B=CLOSED_PASS_NOT_YET
FORMAL_GATES_PASSED=11/16
PACKAGE_C=NOT_STARTED
WHOLE_REPOSITORY_EXECUTION_ISOLATION=NOT_ESTABLISHED
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```
