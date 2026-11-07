# Core13 PILOT-A2 — أول تشغيل Root، فشل محدد ومراجعة الإصلاح الأولى

**التاريخ: 7 نوفمبر 2026. النطاق: الحزمة A فقط، دون تغيير معايير إغلاقها.**

## 1. أدلة Owner الفعلية

صاحب المستودع `lijust` سجل [موافقة G3 الصريحة](https://github.com/lijust/EREI-3.2/issues/307#issuecomment-6708853149) بعد مراجعة عقد Pilot-Close v1 وأدلة A0/A1، مع حظر CREATE وSTART وDELETE وStable/AI Acceptance.

ثم شغّل Owner Manual Workflow [#42385635445](https://github.com/lijust/EREI-3.2/actions/runs/42385635445).

| عنصر التشغيل | Job ID | النتيجة الفعلية |
|---|---|---|
| Nonroot A2+A1+A0+G | `128442304375` | **103/103 PASS** |
| Owner-manual root real dockerd | `128442362660` | **FAIL — exit code 2** |

**لا يوجد إثبات لقراءة Docker حقيقية في ذلك التشغيل.** اكتملت فحوص Hash/Owner/Branch والـCLI في خطوة التهيئة قبل sudo، لكن أمر Python المميز بصلاحيات Root خرج بالرمز 2. تنفيذ A2 السابق كان يعيد `DENIED` في ملف JSON مؤقت عند أي استثناء، دون ظهور سبب الإخفاق في سجل GitHub Actions؛ ولأن أمر Bash كان `set -e`، توقف الـJob قبل قراءة التقرير. **سبب الإخفاق الجذري لم يثبت بعد**؛ لا يجوز نسبه إلى Docker أو مصدر آخر تخمينًا. لم يظهر في التقرير دليل نجاح أو فشل تنظيف الـScratch الخاص؛ أي ادعاء cleanup=PASS في هذا التشغيل غير مثبت.

## 2. الإصلاح الأول (Remediation R1/2 — diagnostic only)

بدل تغيير سياسة الأمان أو إعادة تصميم Root Worker، أُضيفت **مؤشرات مرحلة تشغيل محددة مسبقًا** (OWNER_GATE، ACCOUNTS، HOST_DOCKER_BASELINE، PREPARE_SCOPED_ROOT، START_PRIVATE_DAEMON، VERIFY_PRIVATE_DAEMON، CONTROLLER_WORKER_DENIAL، PROXY_VERIFIER_GET، RECEIPT_VERIFY، HOST_FINAL_BASELINE، SCOPED_CLEANUP)، مع `failure_code` محصور في أكواد مراجَعة، ودون طباعة متغيرات البيئة أو المفتاح أو بيانات Docker أو المسارات السرية أو Stack Trace.

عند خروج Root برمز غير صفري، يفك Workflow التقرير ويرسل إلى Log فقط `A2_OWNER_MANUAL_BLOCKED_STAGE=...` و`A2_OWNER_MANUAL_BLOCKED_CODE=...` ثم يُبقي الـJob **FAIL**. لا يتم تجاهل الخطأ ولا تشغيل Root تلقائيًا. يحافظ `finally` على المرحلة التي وقع فيها الإخفاق الأصلي، بدل استبدالها دومًا بالـCleanup.

المصدر الأخير (Git blob): `f38ea0fb1cddd054c356ea2d3e9dff4b848023e5`.

## 3. التحقق بعد الإصلاح

[GitHub Actions #42386189750](https://github.com/lijust/EREI-3.2/actions/runs/42386189750): **SUCCESS** للـNonroot Job `128443973312`، وOwner Manual Root Job **SKIPPED**.

الاختبارات المؤكدة من السجل: **25 A2 +29 A1 +30 A0 +21 Governance = 105/105 PASS**. الاختبار الجديد يؤكد أن تقرير الإخفاق لا يسرب نص استثناء قد يحتوي على أسرار. هذه الاختبارات لا تثبت نجاح Root الحقيقي.

## 4. حساب بوابات الإغلاق

تم إثبات توقيع G3 عبر الرابط الرسمي، ودليل G0–G2/A0/A1 من تشغيلات سابقة مع مراجعة المالك. ملف `contracts/core13-pilot-closure-progress-v1.json` الجديد هو **سجل تقدم لاحق** منفصل عن `contracts/core13-pilot-closure-v1.json` المحفوظ كـBaseline v1 غير متغير للـSource Pins.

| المقياس | النتيجة |
|---|---|
| إجمالي البوابات | 16 |
| G0–G3 + A0 + A1 | **6 بوابات ذات أدلة وتوقيع مراجعة** |
| A2 | **BLOCKED — Root evidence FAIL** |
| A3 + B0–B3 + C0–C3 | NOT_STARTED |
| جولات إصلاح الحزمة A | **1/2** مستهلكة؛ لا إعادة تصميم مفتوحة |
| حزمة A | NOT_CLOSED |
| قرار Pilot | UNDECIDED |
| `stable_ready` | FALSE |
| `AI_ACCEPTANCE` | BLOCK_AI_ACCEPTANCE |

## 5. الإجراء التالي الوحيد

بعد مراجعة Source Pin الجديد، يستطيع **صاحب الحساب فقط** تشغيل نفس Owner-Manual Workflow لإظهار كود السبب؛ لا تقوم PR/Push بتشغيل Root. إذا ظهر عيب حقيقي، تُخصص **آخر جولة إصلاح R2/2** للسبب المثبت فقط؛ إن لم تنجح A2 ضمن الحد، يُتخذ قرار `CLOSED_NO_GO` أو `CLOSED_BLOCKED` في Issue #308 بدل إضافة مراحل أمنية جديدة.

**لا تُفتح B ولا تُعتمد A2 أو Stable بناء على 105 اختبار Nonroot.**
